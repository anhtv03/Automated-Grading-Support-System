import numpy as np
from fastapi import APIRouter, Depends
from fastapi import HTTPException
from scipy.sparse import csr_matrix
from sqlalchemy.orm.session import Session

from app.constants.status import UploadSessionTaskStatus
from app.db.database import get_db
from app.db.models import Users
from app.schemas.sche_api_response import DataResponse
from app.schemas.sche_upload_session import UploadSessionUpdateTaskStatus
from app.services.answer_template_service import AnswerTemplateService
from app.services.jwt_service import JwtService
from app.services.upload_session_service import UploadSessionService
from app.services.file_service import FileService
from app.services.plagiarism_service import PlagiarismService
from app.services.submission_question_service import QuestionService
from app.services.submission_service import SubmissionService

router = APIRouter()


def group_submission_questions(questions: list):
    grouped = {}

    for q in questions:
        qname = q.question_name.strip().capitalize()  # chuẩn hóa tên câu hỏi

        if qname not in grouped:
            grouped[qname] = {
                "question_name": qname,
                "question_ids": [],
                "question_content": []
            }

        grouped[qname]["question_ids"].append(q.submission_id)
        grouped[qname]["question_content"].append(q.content)

    return list(grouped.values())


@router.get("/result")
async def get_plagiarism_count(
        session_id: int,
        db: Session = Depends(get_db)
):
    result = await PlagiarismService.get_detected_plagiarism_pairs(db, session_id)
    return DataResponse().custom_response(data=result, code="0", message="Get result plagiarism success")


@router.get("/count")
async def get_plagiarized_submission_count(
        session_id: int,
        db: Session = Depends(get_db)
):
    count = await PlagiarismService.get_number_of_plagiarized_submissions(db, session_id)
    number_submission = {"submission_count": count}
    return DataResponse().custom_response(
        data=number_submission,
        code="0",
        message="Get count of plagiarized submissions success"
    )


@router.get("/detail")
async def get_plagiarized_detail(
        submission_id: int,
        db: Session = Depends(get_db)
):
    result = await PlagiarismService.get_plagiarism_detail(db, submission_id)
    return DataResponse().custom_response(
        data=result,
        code="0",
        message="Get detail plagiarism success"
    )
