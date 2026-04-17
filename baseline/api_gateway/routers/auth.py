from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthHealthResponse(BaseModel):
    ok: bool
    providers: list[str]


@router.get("/health", response_model=AuthHealthResponse)
async def auth_health() -> AuthHealthResponse:
    return AuthHealthResponse(ok=True, providers=["google", "linkedin"])
