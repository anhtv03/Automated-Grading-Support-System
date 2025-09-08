from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.constants.status import FileUploadType
from app.db.database import get_db
from app.db.db_answer_template import create_answer_template, get_all_answer_templates_by_session_id, \
    db_delete_exam_templates
from app.db.models import AnswerTemplate
from app.schemas.sche_api_response import DataResponse
from app.schemas.sche_exam_template import AnswerTemplateRequest, AnswerTemplateResponse
from app.services.file_service import FileService

router = APIRouter()


# ======================================================================================================================
# Exam Template Management APIs
# ======================================================================================================================
@router.get("/{session_id}", response_model=DataResponse[List[AnswerTemplateResponse]])
async def get_exam_templates_by_session_id(
        session_id: int,
        db: Session = Depends(get_db)
):
    """Retrieve exam template details by session ID (authenticated users only)."""
    data = await FileService.get_document_files_by_session_id(
        session_id,
        AnswerTemplateResponse,
        get_all_answer_templates_by_session_id,
        db
    )
    return DataResponse().custom_response(
        code="0",
        message="Get exam template successfully",
        data=data
    )


@router.post("/", response_model=DataResponse[List[AnswerTemplateResponse]])
async def create_exam_templates(
    name: str = Form(...),
    session_id: int = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Create new exam templates for authenticated users."""
    exam_template = AnswerTemplateRequest(
        name=name,
        session_id=session_id
    )
    data = await FileService.create_document_files(
        request=exam_template,
        files=files,
        type=FileUploadType.ANSWER_TEMPLATE,
        request_class=AnswerTemplate,
        response_class=AnswerTemplateResponse,
        db_create_func=create_answer_template,
        db=db
    )
    return DataResponse().custom_response_list(
        code="0",
        message="Exam templates created successfully",
        data=data
    )


@router.post("/delete", response_model=DataResponse[int])
async def delete_exam_templates(
        ids: List[int],
        db: Session = Depends(get_db)
):
    """Delete answer template by session ID (authenticated users only)."""
    count = await FileService.delete_document_files_by_id(
        ids,
        db_delete_exam_templates,
        db
    )
    return DataResponse().custom_response(
        code="0",
        message="Delete exam template successfully",
        data=count
    )
