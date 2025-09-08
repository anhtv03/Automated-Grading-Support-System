from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm.session import Session

from app.db.database import get_db
from app.schemas.sche_api_response import DataResponse
from app.schemas.sche_submission import SubmissionResponse
from app.services.ai_detector_service import AIDetectorService

router = APIRouter()


@router.patch("/check-ai-detector", response_model=DataResponse[List[SubmissionResponse]])
async def check_plagiarism_endpoint(
        session_id: int,
        db: Session = Depends(get_db)
):
    submissions_updated = await AIDetectorService.scan_submissions(session_id, db)
    return DataResponse().custom_response(
            code="0",
            message="Scan AI plagiarism success",
            data=submissions_updated
        )
