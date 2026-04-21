from pydantic import BaseModel


class PrepSessionResponse(BaseModel):
    id: str
    questions: list[str]
    star_stories: list[dict]
    company_brief: str
