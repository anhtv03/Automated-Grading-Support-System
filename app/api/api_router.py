from fastapi import APIRouter, Depends

from app.api import (api_auth, api_answer_template, api_grading, api_grading_guide, api_plagiarism, api_submission,
                     api_upload_session, api_exam_question, api_ai_chat, api_data, api_similarity, api_semester,
                     api_user, api_submission_question, api_exam, api_background,
                     api_material, api_grading_guide_question)
from app.helpers.login_manager import PermissionRequired

router = APIRouter()

router.include_router(api_data.router, tags=["data"], prefix="/api/data")

router.include_router(api_user.router, tags=["user"], prefix="/api/user")

router.include_router(api_auth.router, tags=["authentication"], prefix="/api/auth")

router.include_router(api_semester.router, tags=["semester"], prefix="/api/semesters",
                      dependencies=[Depends(PermissionRequired('lecturer', 'course_leader'))])

router.include_router(api_upload_session.router, tags=["upload-session"], prefix="/api/upload-session",
                      dependencies=[Depends(PermissionRequired('lecturer', 'course_leader'))])

router.include_router(api_answer_template.router, tags=["answer-template"], prefix="/api/answer-template",
                      dependencies=[Depends(PermissionRequired('lecturer', 'course_leader'))])

router.include_router(api_grading_guide.router, tags=["grading-guide"], prefix="/api/grading-guide",
                      dependencies=[Depends(PermissionRequired('lecturer', 'course_leader'))])

router.include_router(api_grading_guide_question.router, tags=["guide-question"], prefix="/api/guide-question")

router.include_router(api_submission.router, tags=["submission"], prefix="/api/submission",
                      dependencies=[Depends(PermissionRequired('lecturer', 'course_leader'))])

router.include_router(api_submission_question.router, tags=["submission-question"], prefix="/api/submission-question")

router.include_router(api_grading.router, tags=["grading"], prefix="/api/grading",
                      dependencies=[Depends(PermissionRequired('lecturer', 'course_leader'))])

router.include_router(api_plagiarism.router, tags=["plagiarism"], prefix="/api/plagiarism")

router.include_router(api_similarity.router, tags=["similarity"], prefix="/api/similarity",
                      dependencies=[Depends(PermissionRequired('lecturer', 'course_leader'))])

router.include_router(api_exam.router, tags=["exam"], prefix="/api/exam")

router.include_router(api_exam_question.router, tags=["exam-question"], prefix="/api/exam-question")
router.include_router(api_material.router, tags=["material"], prefix="/api/material")
router.include_router(api_ai_chat.router, tags=["ai-chat"], prefix="/api/ai-chat")

router.include_router(api_background.router, tags=["background"], prefix="/api/background-task")
