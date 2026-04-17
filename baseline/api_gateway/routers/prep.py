from fastapi import APIRouter, Query
from schemas.prep import PrepSessionResponse
from services.prep_service import get_prep_session

router = APIRouter(prefix="/me/prep", tags=["prep"])


@router.get("", response_model=PrepSessionResponse)
async def list_prep(application_id: str = Query(...)) -> PrepSessionResponse:
    return await get_prep_session(application_id)
