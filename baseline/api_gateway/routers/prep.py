from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user
from models.user import User
from schemas.prep import PrepSessionResponse
from services.prep_service import get_prep_for_user

router = APIRouter(prefix="/me/prep", tags=["prep"])


@router.get("", response_model=PrepSessionResponse)
async def list_prep(
    application_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> PrepSessionResponse:
    res = await get_prep_for_user(session, user.id, application_id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prep session not found")
    return res
