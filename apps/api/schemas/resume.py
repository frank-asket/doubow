from pydantic import BaseModel


class ResumeResponse(BaseModel):
    id: str
    storage_path: str
    parsed_profile: dict
    preferences: dict
    version: int
