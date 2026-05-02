from sqlalchemy import func, select
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.session import get_session
from dependencies import get_authenticated_user
from models.user import User
from schemas.dashboard import DashboardSummaryResponse
from schemas.resume import FeedbackLearningPreferenceResponse, UserPreferencesModel, UserPreferencesPatch
from schemas.users import (
    EmailIdentityRow,
    MeAiConfigDebugResponse,
    MeDebugResponse,
    MeEmailIdentityDebugResponse,
    MeOauthConfigDebugResponse,
    MeResponse,
    OAuthProviderConfigDebug,
)
from services.dashboard_service import get_dashboard_summary as load_dashboard_summary
from services.resume_service import (
    clear_feedback_learning_for_user,
    get_feedback_learning_debug_for_user,
    update_preferences_for_user,
)
from services.users_service import user_to_me_response

router = APIRouter(prefix="/me", tags=["users"])


@router.get("", response_model=MeResponse)
async def get_me(user: User = Depends(get_authenticated_user)) -> MeResponse:
    return user_to_me_response(user)


@router.get(
    "/dashboard",
    response_model=DashboardSummaryResponse,
    tags=["dashboard"],
    summary="Dashboard aggregates for badges and Discover stats",
)
async def get_dashboard(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> DashboardSummaryResponse:
    return await load_dashboard_summary(session, user.id)


@router.get("/debug", response_model=MeDebugResponse)
async def get_me_debug(user: User = Depends(get_authenticated_user)) -> MeDebugResponse:
    """Same auth + user-store path as other /v1/me/* routes (not JWT-only)."""
    return MeDebugResponse(user_id=user.id, auth_source="clerk_jwt")


@router.get("/debug/email-identities", response_model=MeEmailIdentityDebugResponse)
async def get_me_debug_email_identities(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> MeEmailIdentityDebugResponse:
    """Dev-only diagnostic for identity splits (same email, multiple users.id)."""
    if settings.environment.lower() == "production":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    rows = (
        await session.execute(
            select(User.id, User.created_at, User.email)
            .where(func.lower(User.email) == func.lower(user.email))
            .order_by(User.created_at.asc())
        )
    ).all()
    ids_for_email = [
        EmailIdentityRow(user_id=row[0], created_at=row[1].isoformat() if row[1] is not None else None) for row in rows
    ]
    return MeEmailIdentityDebugResponse(
        email=user.email,
        current_user_id=user.id,
        ids_for_email=ids_for_email,
        multiple_ids_for_same_email=len(ids_for_email) > 1,
    )


@router.get("/debug/ai-config", response_model=MeAiConfigDebugResponse)
async def get_me_debug_ai_config(
    user: User = Depends(get_authenticated_user),
) -> MeAiConfigDebugResponse:
    """Safe AI config diagnostics (never returns API keys)."""
    _ = user  # ensures endpoint is authenticated
    return MeAiConfigDebugResponse(
        openrouter_configured=bool(settings.openrouter_api_key),
        openrouter_api_url=settings.openrouter_api_url,
        openrouter_http_referer=settings.openrouter_http_referer,
        resolved_models={
            "chat": settings.resolve_openrouter_model("chat"),
            "drafts": settings.resolve_openrouter_model("drafts"),
            "prep": settings.resolve_openrouter_model("prep"),
            "resume": settings.resolve_openrouter_model("resume"),
        },
    )


@router.get("/debug/oauth-config", response_model=MeOauthConfigDebugResponse)
async def get_me_debug_oauth_config(
    user: User = Depends(get_authenticated_user),
) -> MeOauthConfigDebugResponse:
    """Safe OAuth config diagnostics (presence-only, no secret values)."""
    _ = user  # ensures endpoint is authenticated

    google_required = {
        "GOOGLE_OAUTH_CLIENT_ID": bool(settings.google_oauth_client_id),
        "GOOGLE_OAUTH_CLIENT_SECRET": bool(settings.google_oauth_client_secret),
        "GOOGLE_OAUTH_REDIRECT_URI": bool(settings.google_oauth_redirect_uri),
        "GOOGLE_OAUTH_STATE_SECRET": bool(settings.google_oauth_state_secret),
        "GOOGLE_OAUTH_TOKEN_FERNET_KEY": bool(settings.google_oauth_token_fernet_key),
    }
    linkedin_required = {
        "LINKEDIN_OAUTH_CLIENT_ID": bool(settings.linkedin_oauth_client_id),
        "LINKEDIN_OAUTH_CLIENT_SECRET": bool(settings.linkedin_oauth_client_secret),
        "LINKEDIN_OAUTH_REDIRECT_URI": bool(settings.linkedin_oauth_redirect_uri),
        "LINKEDIN_OAUTH_STATE_SECRET": bool(settings.linkedin_oauth_state_secret),
        "LINKEDIN_OAUTH_TOKEN_FERNET_KEY_OR_GOOGLE_FALLBACK": bool(
            settings.linkedin_oauth_token_fernet_key or settings.google_oauth_token_fernet_key
        ),
    }

    def summarize(required: dict[str, bool], configured: bool) -> OAuthProviderConfigDebug:
        missing = [k for k, present in required.items() if not present]
        return OAuthProviderConfigDebug(
            configured=configured,
            required_keys_present=required,
            missing_required_keys=missing,
        )

    return MeOauthConfigDebugResponse(
        google=summarize(google_required, settings.google_oauth_is_configured()),
        linkedin=summarize(linkedin_required, settings.linkedin_oauth_is_configured()),
    )


@router.get(
    "/preferences/feedback-learning",
    response_model=FeedbackLearningPreferenceResponse,
    summary="Read stored feedback_learning and resolved matching weights",
)
async def get_feedback_learning_prefs(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> FeedbackLearningPreferenceResponse:
    """Debug/diagnostic: shows persisted outcome snapshot and effective blend weights."""
    if settings.environment.lower() == "production":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    try:
        fl, preview = await get_feedback_learning_debug_for_user(session, user.id)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found — upload a resume first.",
        )
    return FeedbackLearningPreferenceResponse(
        feedback_learning=fl,
        base_matching_weights=preview["base"],
        effective_matching_weights=preview["effective"],
    )


@router.delete("/preferences/feedback-learning", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback_learning_prefs(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> None:
    """Clear feedback_learning so rescoring uses global weights only."""
    if settings.environment.lower() == "production":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    try:
        await clear_feedback_learning_for_user(session, user.id)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found — upload a resume first.",
        )


@router.patch("/preferences", response_model=UserPreferencesModel)
async def patch_preferences(
    patch: UserPreferencesPatch,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> UserPreferencesModel:
    try:
        return await update_preferences_for_user(session, user.id, patch)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found — upload a resume before updating preferences.",
        )
