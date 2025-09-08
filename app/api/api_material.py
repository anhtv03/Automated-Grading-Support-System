from typing import Any, List

from fastapi import APIRouter, UploadFile, File, Depends, Form
from sqlalchemy.orm.session import Session

from app.db.database import get_db
from app.db.db_material import db_create_material, db_delete_material_by_id
from app.db.models import Material
from app.schemas.sche_api_response import DataResponse
from app.schemas.sche_material import MaterialContentResponse
from app.services.document_service import MaterialService

router = APIRouter()


@router.get("/{question_id}", response_model=DataResponse[List[MaterialContentResponse]])
async def get_material_by_question_id(
        question_id: int,
        db: Session = Depends(get_db)
):
    """Retrieve material details by ID (authenticated leader course only)."""
    data = MaterialService.get_material_by_question_id(question_id, db)
    return DataResponse().custom_response(
        code="0",
        message="Get materials successfully",
        data=data
    )


@router.post("/", response_model=DataResponse[List[MaterialContentResponse]])
async def create_material(
        exam_question_id: int = Form(...),
        files: List[UploadFile] = File(...),
        db: Session = Depends(get_db)
) -> Any:
    data = await MaterialService.create_document_files(
        base_id=exam_question_id,
        files=files,
        request_class=Material,
        response_class=MaterialContentResponse,
        db_create_func=db_create_material,
        db=db
    )
    return DataResponse().custom_response(
        code="0",
        message="Add materials successfully",
        data=data
    )


@router.delete("/delete-material", response_model=DataResponse[int])
async def delete_material(
        document_id: int,
        db: Session = Depends(get_db)
) -> Any:
    count = await MaterialService.delete_material(
        document_id,
        db_delete_material_by_id,
        db
    )
    return DataResponse().custom_response(
        code="0",
        message="Delete material successfully",
        data=count
    )

