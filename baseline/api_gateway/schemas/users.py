from typing import Literal

from pydantic import BaseModel


class MeResponse(BaseModel):
    id: str
    email: str
    name: str
    plan: Literal["free", "pro"]


class MeDebugResponse(BaseModel):
    user_id: str
    auth_source: Literal["clerk_jwt"]
