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


class EmailIdentityRow(BaseModel):
    user_id: str
    created_at: str | None = None


class MeEmailIdentityDebugResponse(BaseModel):
    email: str
    current_user_id: str
    ids_for_email: list[EmailIdentityRow]
    multiple_ids_for_same_email: bool
