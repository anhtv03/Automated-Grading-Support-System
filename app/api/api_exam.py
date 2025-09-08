from typing import Any, List

from fastapi import APIRouter, Depends, Form, File, UploadFile
from sqlalchemy.orm import Session

from app.constants.status import FileUploadType
from app.db.database import get_db
from app.db.db_exam import db_create_exam, db_delete_exams
from app.db.models import Exam, Users
from app.schemas.sche_api_response import DataResponse
from app.schemas.sche_exam import ExamUpdatedRequest, ExamResponse, ExamRequest, ExamGuideRequest
from app.schemas.sche_exam_question import ExamQuestionGenerateRequest, ExamQuestionGeneratePromptRequest
from app.schemas.sche_pagination_response import PaginationCustomParams, Page
from app.services.exam_question_service import ExamQuestionService
from app.services.exam_service import ExamService
from app.services.file_service import FileService
from app.services.jwt_service import JwtService

router = APIRouter()


# region GET Methods
@router.get("/{session_id}", response_model=Page[ExamResponse])
def get_exams_by_session_id(
        session_id: int,
        params: PaginationCustomParams = Depends(),
        db: Session = Depends(get_db)
) -> Any:
    """Retrieve exam details by ID (authenticated users only)."""
    data = ExamService.get_exam_by_session_id(db, params, session_id)
    return data


@router.get("/list/exam-generated", response_model=DataResponse[List[ExamResponse]])
async def get_exams_by_user(
        current_user: Users = Depends(JwtService.validate_token),
        db: Session = Depends(get_db)
) -> Any:
    """Retrieve exams (authenticated users only)."""
    data = ExamService.get_exams_by_user_id(current_user.id, db)
    return DataResponse().custom_response(
        code="0",
        message="Get exams successfully",
        data=data
    )


@router.get("/{guide_id}/grading-guide", response_model=DataResponse[ExamResponse])
def get_exams_by_guide_id(
        guide_id: int,
        db: Session = Depends(get_db)
) -> Any:
    """Retrieve exam details by ID (authenticated users only)."""
    data = ExamService.get_exams_by_grading_guide_id(guide_id, db)
    return DataResponse().custom_response(
        code="0",
        message="Get exam successfully",
        data=data
    )

# endregion


# region POST Methods
@router.post("/generate-exam/prompt")
async def generate_exam_prompt(
        request: ExamQuestionGenerateRequest,
        db: Session = Depends(get_db)
) -> Any:
    """Generate exam questions from prompt."""
    data = await ExamQuestionService.generate_content_question(request, db)
    return DataResponse().custom_response(
        code="0",
        message="Generate answer question successfully",
        data=data
    )


@router.post("/generate-exam/suggest-question")
async def generate_exam_suggest(
        request: ExamQuestionGenerateRequest,
        db: Session = Depends(get_db)
) -> Any:
    """Generate suggest for exam questions prompt."""
    data = ExamQuestionService.generate_suggest_prompt(request, db)
    return DataResponse().custom_response(
        code="0",
        message="Generate suggest question successfully",
        data=data
    )


@router.post("/generate-exam/suggest-input")
async def generate_exam_suggest(
        request: ExamQuestionGeneratePromptRequest,
        db: Session = Depends(get_db)
) -> Any:
    """Generate suggest for input prompt."""
    data = ExamQuestionService.generate_suggest_input(request, db)
    return DataResponse().custom_response(
        code="0",
        message="Generate suggest input prompt successfully",
        data=data
    )


@router.post("/create-exam", response_model=DataResponse[ExamResponse])
async def create_exam(
        exam: ExamRequest,
        db: Session = Depends(get_db)
) -> Any:
    """Create new exam (authenticated users only)."""
    data = await ExamService.create_exam(exam, db)
    return DataResponse().custom_response(
        code='0',
        message='Create exam successfully',
        data=data
    )


@router.post("/", response_model=DataResponse[List[ExamResponse]])
async def create_exams(
        name: str = Form(...),
        session_id: int = Form(...),
        files: List[UploadFile] = File(...),
        db: Session = Depends(get_db)
) -> Any:
    """Create new exam (authenticated users only)."""
    exam = ExamRequest(name=name, session_id=session_id)
    data = await FileService.create_document_files(
        request=exam,
        files=files,
        type=FileUploadType.EXAM,
        request_class=Exam,
        response_class=ExamResponse,
        db_create_func=db_create_exam,
        db=db
    )
    return DataResponse().custom_response_list(
        code='0',
        message='Create exam successfully',
        data=data
    )


@router.post("/import-exam", response_model=DataResponse[bool])
async def import_exam(
        exam_guide: ExamGuideRequest,
        db: Session = Depends(get_db)
) -> Any:
    """Create new exam (authenticated users only)."""
    data = ExamService.import_exam(exam_guide, db)
    return DataResponse().custom_response(
        code='0',
        message='Import exam successfully',
        data=data
    )

@router.post("/delete-exams", response_model=DataResponse[int])
async def delete_exams(
        ids: List[int],
        db: Session = Depends(get_db)
) -> Any:
    """Delete exam by ID (authenticated users only)."""
    count = await FileService.delete_document_files_by_id(ids, db_delete_exams, db)
    return DataResponse().custom_response(
        code="0",
        message="Delete exams successfully",
        data=count
    )


# endregion


# region PUT Methods
@router.put("/", response_model=DataResponse[ExamResponse])
def update_exam(
        request: ExamUpdatedRequest,
        db: Session = Depends(get_db)
) -> Any:
    """Update exam information (course_leader only)."""
    data = ExamService.update_exam(request, db)
    return DataResponse().custom_response(
        code="0",
        message="Successful exam update",
        data=data
    )


@router.put("/details/hidden", response_model=DataResponse[bool])
def hide_exams(
        exam_ids: List[int],
        db: Session = Depends(get_db)
) -> Any:
    """Hide exam (authenticated leader course only)."""
    data = ExamService.hide_exams(exam_ids, db)
    return DataResponse().custom_response(
        code='0',
        message='Hide exam successfully',
        data=data
    )


@router.put("/details/visible", response_model=DataResponse[bool])
def visible_exams(
        exam_ids: List[int],
        db: Session = Depends(get_db)
) -> Any:
    """Visible exam (authenticated leader course only)."""
    data = ExamService.visible_exams(exam_ids, db)
    return DataResponse().custom_response(
        code='0',
        message='Visible exam successfully',
        data=data
    )
# endregion
