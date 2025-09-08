from typing import List, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.sche_api_response import DataResponse
from app.schemas.sche_exam_question import ExamQuestionGenerateResponse, ExamQuestionRequest, ExamQuestionUpdateRequest, \
    ExamQuestionGetRequest, ExamRequestParams
from app.services.exam_question_service import ExamQuestionService

router = APIRouter()


# region GET Methods
@router.get("/{exam_id}", response_model=DataResponse[List[ExamQuestionGenerateResponse]])
async def get_exam_questions(
        exam_id: int,
        params: ExamRequestParams = Depends(),
        db: Session = Depends(get_db)
) -> Any:
    """Retrieve exam questions by exam ID (authenticated Leader Course only)."""
    data = ExamQuestionService.get_exam_questions(exam_id, params, db)
    return DataResponse().custom_response(
        code="0",
        message="Get exam question successfully",
        data=data
    )


@router.get("/{exam_id}/list-question", response_model=DataResponse[List[ExamQuestionGenerateResponse]])
async def get_exam_question_by_name(
        exam_id: int,
        question_name: str,
        db: Session = Depends(get_db)
) -> Any:
    """Retrieve exam question by name (authenticated Leader Course only)."""
    exam_question = ExamQuestionGetRequest(
        exam_id=exam_id,
        question_name=question_name
    )
    data = ExamQuestionService.get_exam_question_by_name(exam_question, db)
    return DataResponse().custom_response(
        code="0",
        message="Get exam question successfully",
        data=data
    )


@router.get("/details/{exam_question_id}", response_model=DataResponse[ExamQuestionGenerateResponse])
async def get_exam_question_by_id(
        exam_question_id: int,
        db: Session = Depends(get_db)
) -> Any:
    """Retrieve exam question by ID (authenticated Leader Course only)."""
    data = ExamQuestionService.get_exam_question_by_id(exam_question_id, db)
    return DataResponse().custom_response(
        code="0",
        message="Get exam question successfully",
        data=data
    )


# endregion


# region POST Methods
@router.post("/", response_model=DataResponse[ExamQuestionGenerateResponse])
async def create_exam_question(
        exam_question: ExamQuestionRequest,
        db: Session = Depends(get_db)
) -> Any:
    """Create a new exam question (authenticated leader course only)."""
    data = ExamQuestionService.create_exam_question(exam_question, db)
    return DataResponse().custom_response(
        code='0',
        message='Create exam question successfully',
        data=data
    )


# endregion


# region PUT Methods
@router.put("/{exam_question_id}", response_model=DataResponse[ExamQuestionGenerateResponse])
async def update_exam_question(
        exam_question_id: int,
        new_exam_question: ExamQuestionUpdateRequest,
        db: Session = Depends(get_db)
) -> Any:
    """Update exam question (authenticated leader course only)."""
    data = ExamQuestionService.update_exam_question(exam_question_id, new_exam_question, db)
    return DataResponse().custom_response(
        code='0',
        message='Update exam question successfully',
        data=data
    )


@router.put("/details/hidden", response_model=DataResponse[bool])
def hide_exam_question(
        exam_question_ids: List[int],
        db: Session = Depends(get_db)
) -> Any:
    """Hide exam question (authenticated leader course only)."""
    data = ExamQuestionService.hide_exam_question(exam_question_ids, db)
    return DataResponse().custom_response(
        code='0',
        message='Hide exam question successfully',
        data=data
    )


@router.put("/details/visible", response_model=DataResponse[bool])
def visible_exam_question(
        exam_question_ids: List[int],
        db: Session = Depends(get_db)
) -> Any:
    """Visible exam question (authenticated leader course only)."""
    data = ExamQuestionService.visible_exam_question(exam_question_ids, db)
    return DataResponse().custom_response(
        code='0',
        message='Visible exam question successfully',
        data=data
    )


# endregion


# region DELETE Methods
@router.delete("/delete/{question_id}", response_model=DataResponse[int])
async def delete_exam_questions(
        question_id: int,
        db: Session = Depends(get_db)
) -> Any:
    """Delete exam question by ID (authenticated leader course only)."""
    count = await ExamQuestionService.delete_exam_question_by_ids(question_id, db)
    return DataResponse().custom_response(
        code="0",
        message="Delete exam questions successfully",
        data=count
    )
# endregion
