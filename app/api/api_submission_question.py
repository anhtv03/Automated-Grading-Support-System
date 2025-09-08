from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm.session import Session

from app.db.database import get_db
from app.schemas.sche_api_response import DataResponse
from app.schemas.sche_criteria import CriteriaResponse
from app.schemas.sche_submisson_question import SubmissionQuestionResponse, \
    CriteriaHistoryResponse, CriteriaHistoryUpdateRequest
from app.services.submission_question_service import QuestionService

router = APIRouter()


@router.post("/", response_model=DataResponse[List[SubmissionQuestionResponse]])
async def create_submission_questions(
        session_id: int,
        db: Session = Depends(get_db)
):
    data = QuestionService.create_questions(session_id, db)
    return DataResponse().custom_response_list(
        code="0",
        message="Create submission question successfully",
        data=data
    )


@router.get("/criteria-history/{submission_id}", response_model=DataResponse[List[CriteriaHistoryResponse]])
async def get_criteria_history(
        submission_id: int,
        db: Session = Depends(get_db)
):
    data = QuestionService.get_criteria_history_by_submission_id(submission_id, db)
    return DataResponse().custom_response_list(
        code="0",
        message="Get criteria history successfully",
        data=data
    )


@router.get("/criteria/{grading_guide_id}", response_model=DataResponse[List[CriteriaResponse]])
async def get_criteria_history(
        grading_guide_id: int,
        db: Session = Depends(get_db)
):
    data = QuestionService.get_criteria_by_grading_guide_id(grading_guide_id, db)
    return DataResponse().custom_response_list(
        code="0",
        message="Get criteria history successfully",
        data=data
    )


@router.put("/update-score", response_model=DataResponse[bool])
async def update_score(
        request: List[CriteriaHistoryUpdateRequest],
        db: Session = Depends(get_db)
):
    data = QuestionService.update_submission_question_score(request, db)
    return DataResponse().custom_response(
        code="0",
        message="Update successfully",
        data=data
    )


@router.put("/update-final-score", response_model=DataResponse[bool])
def update_final_score(
        submission_ids: List[int],
        db: Session = Depends(get_db)
):
    data = QuestionService.update_submission_score(submission_ids, db)
    return (DataResponse().custom_response(
        code="0",
        message="Update successfully",
        data=data
    ))


@router.put("/update-final-score/{session_id}", response_model=DataResponse[bool])
def update_final_score_by_session_id(
        session_id: int,
        db: Session = Depends(get_db)
):
    data = QuestionService.update_submission_score_by_session_id(session_id, db)
    return DataResponse().custom_response(
        code="0",
        message="Update successfully",
        data=data
    )
