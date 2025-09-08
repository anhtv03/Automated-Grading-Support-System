# app/api/__init__.py
from fastapi import APIRouter

from app.api import api_auth, api_answer_template, api_grading, api_grading_guide, api_plagiarism, api_submission, \
    api_upload_session
from app.api import api_semester
from app.api import api_similarity
from app.api import api_user

api_router = APIRouter()
api_router.include_router(api_auth.router)
api_router.include_router(api_answer_template.router)
api_router.include_router(api_grading.router)
api_router.include_router(api_grading_guide.router)
api_router.include_router(api_plagiarism.router)
api_router.include_router(api_semester.router)
api_router.include_router(api_similarity.router)
api_router.include_router(api_submission.router)
api_router.include_router(api_upload_session.router)
api_router.include_router(api_user.router)
