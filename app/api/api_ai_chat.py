from boto3 import Session
from fastapi import APIRouter
from fastapi.params import Depends
from fastapi_sqlalchemy import db

from app.db.database import get_db
from app.schemas.sche_ai_chat import (
    ChatRequest, ChatResponse, HealthResponse
)
from app.services.ai_chat_service import AIServiceFactory

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    """Generate chat completion using a specified AI provider and log to a database"""
    service = AIServiceFactory.get_service(request.provider)
    response = await service.chat_completion(
        db=db.session,
        messages=request.messages,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        model=request.model,
        grading_guide_question_id=request.grading_guide_question_id  # Pass session_id for logging
    )
    return response


@router.get("/health", response_model=HealthResponse)
async def health_check(
        db: Session = Depends(get_db)
):
    """Check health status of all AI providers"""
    provider_status = await AIServiceFactory.health_check_all(db)
    overall_status = "healthy" if any(provider_status.values()) else "unhealthy"

    return HealthResponse(
        status=overall_status,
        providers=provider_status
    )
