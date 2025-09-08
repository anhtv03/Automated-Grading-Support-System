from typing import List, Dict, Any

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.data import Test
from app.db.database import get_db
from app.db.db_submission import create_submission, get_all_submissions_by_session_id, db_delete_submissions
from app.db.models import Submission, Users
from app.external.aws_service import S3Uploader
from app.schemas.sche_api_response import DataResponse
from app.schemas.sche_score_history import ScoreHistoryCreateResponse
from app.schemas.sche_statistic import SubmissionStatistic
from app.schemas.sche_submission import (
    SubmissionCreateRequest,
    SubmissionAIDetector,
    SubmissionResponse,
    SubmissionItemDetailResponse
)
from app.services.file_service import FileService
from app.services.jwt_service import JwtService
from app.services.score_history_service import ScoreHistoryService
from app.services.submission_service import SubmissionService

router = APIRouter()


# region GET Methods
@router.get("/{session_id}", response_model=DataResponse[List[SubmissionResponse]])
async def get_submissions_by_session_id(
        session_id: int,
        db: Session = Depends(get_db)
):
    """Retrieve grading guide details by ID (authenticated users only)."""
    data = await FileService.get_document_files_by_session_id(
        session_id=session_id,
        response_class=SubmissionResponse,
        db_get_func=get_all_submissions_by_session_id,
        db=db
    )
    return DataResponse().custom_response(
        code="0",
        message="Get submissions successfully",
        data=data
    )


@router.get("/{session_id}/test", response_model=DataResponse[List[SubmissionResponse]])
def get_submissions_by_session_id(
        session_id: int,
        db: Session = Depends(get_db)
):
    """Retrieve grading guide details by ID (authenticated users only)."""
    data = Test.generate_final_results(
        session_id=session_id,
        db=db
    )
    return DataResponse().custom_response(
        code="0",
        message="Get submissions successfully",
        data=data
    )


@router.get("/get-file/{file_key}", response_model=DataResponse)
async def get_file_url(
        file_key: str
) -> Any:
    """Get presigned URL for file."""
    url = await S3Uploader.get_presigned_url(file_key)
    return DataResponse().custom_response(
        code="0",
        message="Get file successfully",
        data={"presigned_url": url}
    )


@router.get("/statistic/{session_id}", response_model=DataResponse[Dict[str, int]])
async def get_data_statistic(
        session_id: int,
        db: Session = Depends(get_db)
) -> Any:
    """Retrieve submission statistics by session ID."""
    data_statistic = SubmissionService.get_data_statistic(session_id, db)
    return DataResponse().custom_response(
        code="0",
        message="Statistic successfully",
        data=data_statistic
    )


@router.get("/ai-statistic/{session_id}", response_model=DataResponse[Dict[str, int]])
async def get_data_statistic(
        session_id: int,
        db: Session = Depends(get_db)
) -> Any:
    """Retrieve submission statistics by session ID."""
    data_statistic = SubmissionService.get_data_statistic_by_ai(session_id, db)
    return DataResponse().custom_response(
        code="0",
        message="Statistic successfully",
        data=data_statistic
    )


@router.get("/ai-detector/{session_id}", response_model=DataResponse[SubmissionAIDetector])
async def count_ai_detected(
        session_id: int,
        db: Session = Depends(get_db)
) -> Any:
    """Count AI-detected submissions by session ID."""
    data_statistic = SubmissionService.count_ai_detected(session_id, db)
    return DataResponse().custom_response(
        code="0",
        message="Statistic successfully",
        data=data_statistic
    )


@router.get("/details/{submission_id}", response_model=DataResponse[SubmissionItemDetailResponse])
async def get_submission_by_id(
        submission_id: int,
        current_user: Users = Depends(JwtService.validate_token),
        db: Session = Depends(get_db)
) -> Any:
    """Retrieve submissions (lecturer/course_leader only)."""
    result = SubmissionService.get_submission_by_session_id(current_user.id, submission_id, db)
    return DataResponse().custom_response(
        code="0",
        message="Get submission successfully",
        data=result
    )


# endregion


# region POST Methods
@router.post("/", response_model=DataResponse[List[SubmissionResponse]])
async def create_submissions(
        name: str = Form(...),
        session_id: int = Form(...),
        files: List[UploadFile] = File(...),
        db: Session = Depends(get_db)
) -> Any:
    """Create new submissions (lecturer/course_leader only)."""
    submission = SubmissionCreateRequest(name=name, session_id=session_id)
    data = await FileService.create_document_files(
        request=submission,
        files=files,
        type="SUBMISSION",
        request_class=Submission,
        response_class=SubmissionResponse,
        db_create_func=create_submission,
        db=db
    )
    return DataResponse().custom_response_list(
        code="0",
        message="Submissions created successfully",
        data=data
    )


@router.post("/upload", response_model=DataResponse[dict])
async def upload_file(
        file: UploadFile = File(...)
) -> Any:
    """Upload file to S3."""
    data = await S3Uploader.upload_file_to_s3(file)
    return DataResponse().custom_response(
        code='0',
        message='Upload file successfully',
        data=data
    )


@router.post("/delete-submissions", response_model=DataResponse[int])
async def delete_submissions(
        ids: List[int],
        db: Session = Depends(get_db)
) -> Any:
    """Delete exam template by session ID (authenticated users only)."""
    count = await FileService.delete_document_files_by_id(
        ids=ids,
        db_delete_func=db_delete_submissions,
        db=db
    )
    return DataResponse().custom_response(
        code="0",
        message="Delete submissions successfully",
        data=count
    )


@router.post("/create/score-history")
def create_score_history(
        request: ScoreHistoryCreateResponse,
        db: Session = Depends(get_db)
):
    result = ScoreHistoryService.create_score_history(request, db)
    return DataResponse().custom_response(
        code="0",
        message="Create score history successfully",
        data=result
    )


@router.post("/statistic-grading", response_model=DataResponse[List[SubmissionStatistic]])
async def get_data_statistic(
        session_id: int,
        criteria_ids: List[int],
        db: Session = Depends(get_db)
) -> Any:
    """Retrieve submission statistics by session ID."""
    data_statistic = SubmissionService.get_data_statistic_grading(session_id, criteria_ids, db)
    return DataResponse().custom_response(
        code="0",
        message="Statistic successfully",
        data=data_statistic
    )

# endregion

# region PUT Methods
@router.put("/update-score", response_model=DataResponse[bool])
async def update_score_submission(
        session_id: int,
        db: Session = Depends(get_db)
):
    data = SubmissionService.update_submission_score(session_id, db)
    return DataResponse().custom_response(
        code="0",
        message="Update successfully",
        data=data
    )

# endregion
