from typing import List, Any

from fastapi import APIRouter, Depends, Form, File, UploadFile
from sqlalchemy.orm import Session

from app.constants.status import FileUploadType
from app.db.database import get_db
from app.db.db_grading_guide import create_grading_guide, get_all_grading_guide_by_session_id, db_delete_grading_guides
from app.db.models import GradingGuide
from app.schemas.sche_api_response import DataResponse
from app.schemas.sche_grading_guide import GradingGuideResponse, GradingGuideRequest, GradingGuideUpdateRequest, \
    GradingGuideGenerateRequest, GradingGuideResponsePageResponse, GradingGuideGenerateQuestionRequest, \
    GradingGuideGeneratePromptRequest
from app.schemas.sche_pagination_response import Page, PaginationCustomParams
from app.services.file_service import FileService
from app.services.grading_guide_service import GradingGuideService

router = APIRouter()


# ======================================================================================================================
# Grading Guide Management APIs
# ======================================================================================================================
@router.get("/{session_id}", response_model=DataResponse[List[GradingGuideResponse]])
async def get_grading_guides_by_session_id(
        session_id: int,
        db: Session = Depends(get_db)
):
    """Retrieve grading guide details by ID (authenticated users only)."""
    data = await FileService.get_document_files_by_session_id(
        session_id,
        GradingGuideResponse,
        get_all_grading_guide_by_session_id,
        db
    )
    return DataResponse().custom_response(
        code="0",
        message="Get grading guides successfully",
        data=data
    )


@router.get("/list/{session_id}", response_model=Page[GradingGuideResponsePageResponse])
async def get_grading_guide_page_by_session_id(
        session_id: int,
        params: PaginationCustomParams = Depends(),
        db: Session = Depends(get_db)
):
    """Retrieve grading guide details by ID (authenticated users only)."""
    data = GradingGuideService.get_grading_guide_by_session_id(db, params, session_id)
    return data


@router.post("/", response_model=DataResponse[List[GradingGuideResponse]])
async def create_grading_guides(
        name: str = Form(...),
        type: str = Form(...),
        session_id: int = Form(...),
        files: List[UploadFile] = File(...),
        db: Session = Depends(get_db)
):
    """Create new grading guide (authenticated users only)."""
    grading_guide = GradingGuideRequest(
        name=name,
        type=type,
        session_id=session_id
    )
    data = await FileService.create_document_files(
        request=grading_guide,
        files=files,
        type=FileUploadType.GUIDE_TEMPLATE,
        request_class=GradingGuide,
        response_class=GradingGuideResponse,
        db_create_func=create_grading_guide,
        db=db
    )
    return DataResponse().custom_response_list(
        code='0',
        message='Create grading guide successfully',
        data=data
    )


@router.post("/generate-guide/prompt")
async def generate_grading_guide_prompt(
        request: GradingGuideGenerateRequest,
        db: Session = Depends(get_db)
) -> Any:
    """Generate suggest for grading guide."""
    data = await GradingGuideService.generate_content_question(request, db)
    return DataResponse().custom_response(
        code="0",
        message="Generate grading guide question successfully",
        data=data
    )

@router.post("/generate-guide/suggest-question")
def generate_grading_guide_suggest_question(
        request: GradingGuideGenerateQuestionRequest,
        db: Session = Depends(get_db)
):
    """Generate suggest for grading guide."""
    data = GradingGuideService.generate_suggest_question(request, db)
    return DataResponse().custom_response(
        code="0",
        message="Generate suggest question grading guide successfully",
        data=data
    )


@router.post("/generate-guide/suggest-input")
def generate_grading_guide_suggest_input(
        request: GradingGuideGeneratePromptRequest,
        db: Session = Depends(get_db)
):
    """Generate suggest input for grading guide."""
    data = GradingGuideService.generate_suggest_input(request, db)
    return DataResponse().custom_response(
        code="0",
        message="Generate suggest input grading guide successfully",
        data=data
    )


@router.post("/create-grading-guide", response_model=DataResponse[GradingGuideResponse])
async def create_grading_guide_info(
        guide: GradingGuideRequest,
        db: Session = Depends(get_db)
) -> Any:
    """Create new exam (authenticated users only)."""
    data = await GradingGuideService.create_grading_guide(guide, db)
    return DataResponse().custom_response(
        code='0',
        message='Create grading guide successfully',
        data=data
    )


@router.post("/delete-grading-guides", response_model=DataResponse[int])
async def delete_grading_guides(
        ids: List[int],
        db: Session = Depends(get_db)
):
    """Delete grading guide by ID (authenticated users only)."""
    count = await FileService.delete_document_files_by_id(
        ids,
        db_delete_grading_guides,
        db
    )
    return DataResponse().custom_response(
        code="0",
        message="Delete grading guide successfully",
        data=count
    )


@router.put("/", response_model=DataResponse[GradingGuideResponse])
def update_grading_guide(
        request: GradingGuideUpdateRequest,
        db: Session = Depends(get_db)
) -> Any:
    """Update exam information (course_leader only)."""
    data = GradingGuideService.update_grading_guide(request, db)
    return DataResponse().custom_response(
        code="0",
        message="Successful grading guide update",
        data=data
    )
