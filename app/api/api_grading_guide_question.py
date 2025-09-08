from typing import List, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.sche_api_response import DataResponse
from app.schemas.sche_grading_guide_question import GradingGuideQuestionResponse, GuideQuestionRequestParams, \
    GuideQuestionUpdateRequest, GuideQuestionCreateRequest
from app.services.guide_question_service import GuideQuestionService

router = APIRouter()


# ======================================================================================================================
# Grading Guide Question Management APIs
# ======================================================================================================================
@router.get("/{exam_question_id}", response_model=DataResponse[List[GradingGuideQuestionResponse]])
async def get_guide_question_by_exam_question(
        exam_question_id: int,
        grading_guide_id: int,
        params: GuideQuestionRequestParams = Depends(),
        db: Session = Depends(get_db)
):
    """Retrieve the grading guide question by question ID (authenticated users only)."""
    data = GuideQuestionService.get_grading_guide_question_by_exam_question_id(db, params, exam_question_id,
                                                                               grading_guide_id)
    return DataResponse().custom_response(
        code="0",
        message="Get grading guide questions successfully",
        data=data
    )


@router.get("/grading-guide/{grading_guide_id}", response_model=DataResponse[List[GradingGuideQuestionResponse]])
async def get_guide_question_by_grading_guide(
        grading_guide_id: int,
        params: GuideQuestionRequestParams = Depends(),
        db: Session = Depends(get_db)
):
    """Retrieve the grading guide question by question ID (authenticated users only)."""
    data = GuideQuestionService.get_grading_guide_question_by_grading_guide_id(db, params, grading_guide_id)
    return DataResponse().custom_response(
        code="0",
        message="Get grading guide questions successfully",
        data=data
    )


@router.get("/grading-guide/{grading_guide_id}", response_model=DataResponse[List[GradingGuideQuestionResponse]])
async def get_guide_question_by_grading_guide(
        grading_guide_id: int,
        params: GuideQuestionRequestParams = Depends(),
        db: Session = Depends(get_db)
):
    """Retrieve the grading guide question by question ID (authenticated users only)."""
    data = GuideQuestionService.get_grading_guide_question_by_grading_guide_id(db, params, grading_guide_id)
    return DataResponse().custom_response(
        code="0",
        message="Get grading guide questions successfully",
        data=data
    )


# region POST Methods
@router.post("/", response_model=DataResponse[List[GradingGuideQuestionResponse]])
async def create_guide_question(
        request: GuideQuestionCreateRequest,
        db: Session = Depends(get_db)
) -> Any:
    """Create a new exam question (authenticated leader course only)."""
    data = GuideQuestionService.create_guide_question(request, db)
    return DataResponse().custom_response(
        code='0',
        message='Create grading guide question successfully',
        data=data
    )


# endregion

# region PUT Methods
@router.put("/{guide_question_id}", response_model=DataResponse[GradingGuideQuestionResponse])
async def update_grading_guide_question(
        guide_question_id: int,
        new_guide_question: GuideQuestionUpdateRequest,
        db: Session = Depends(get_db)
) -> Any:
    """Update exam question (authenticated leader course only)."""
    data = GuideQuestionService.update_guide_question(guide_question_id, new_guide_question, db)
    return DataResponse().custom_response(
        code='0',
        message='Update grading guide question successfully',
        data=data
    )


@router.put("/details/hidden", response_model=DataResponse[bool])
def hide_guide_question(
        guide_question_ids: List[int],
        db: Session = Depends(get_db)
) -> Any:
    """Hide grading guide question (authenticated leader course only)."""
    data = GuideQuestionService.hide_guide_question(guide_question_ids, db)
    return DataResponse().custom_response(
        code='0',
        message='Hide grading guide question successfully',
        data=data
    )


@router.put("/details/visible", response_model=DataResponse[bool])
def visible_guide_question(
        guide_question_ids: List[int],
        db: Session = Depends(get_db)
) -> Any:
    """Visible grading guide question (authenticated leader course only)."""
    data = GuideQuestionService.visible_guide_question(guide_question_ids, db)
    return DataResponse().custom_response(
        code='0',
        message='Visible grading guide question successfully',
        data=data
    )


@router.put("/details/delete", response_model=DataResponse[int])
def delete_grading_guide_questions(
        guide_question_ids: List[int],
        db: Session = Depends(get_db)
):
    count = GuideQuestionService.delete_grading_guide_question(db, guide_question_ids)
    return DataResponse().custom_response(
        code="0",
        message="Delete grading guide question successfully",
        data=count
    )
# endregion


# region DELETE Methods
@router.delete("/{guide_id}/{exam_id}", response_model=DataResponse[int])
def delete_history_mapping(
        guide_id: int,
        exam_id: int,
        db: Session = Depends(get_db)
):
    """Delete answer template by session ID (authenticated users only)."""
    count = GuideQuestionService.delete_guide_exam(db, guide_id, exam_id)
    return DataResponse().custom_response(
        code="0",
        message="Delete exam template successfully",
        data=count
    )
# end
