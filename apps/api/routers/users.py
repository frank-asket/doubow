from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/me", tags=["users"])


class MeResponse(BaseModel):
    id: str
    email: str
    name: str
    plan: Literal["free", "pro"]


@router.get("", response_model=MeResponse)
async def get_me() -> MeResponse:
    return MeResponse(id="dev-user", email="demo@doubow.ai", name="Franck L.", plan="pro")
