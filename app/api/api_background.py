from celery.result import AsyncResult
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, Body, Request
from sqlalchemy.orm.session import Session
from app.db.database import get_db
from app.db.models import Users
from app.services.jwt_service import JwtService
from app.services.upload_session_service import UploadSessionService


router = APIRouter()


from app.worker import ai_detector, run_plagiarism_check, run_grading_submission


@router.post("/check-plagiarism", status_code=201)
async def upload_exam_files(
         session_id: int,
         current_user: Users = Depends(JwtService.validate_token),
         db: Session = Depends(get_db)
 ):
    type = "plagiarism_check"
    task = run_plagiarism_check.delay(session_id, current_user.id)
    UploadSessionService.update_session_task_id(db, session_id, current_user.id, type, task.id)
    return JSONResponse({"task_id": task.id})


@router.post("/check-detector", status_code=201)
async def upload_exam_files(
         session_id: int,
         current_user: Users = Depends(JwtService.validate_token),
         db: Session = Depends(get_db)

 ):
    type = "ai_detector"
    task = ai_detector.delay(session_id)
    UploadSessionService.update_session_task_id(db, session_id, current_user.id, type, task.id)
    return JSONResponse({"task_id": task.id})

@router.post("/grading-submission", status_code=201)
async def upload_exam_files(
         session_id: int,
         current_user: Users = Depends(JwtService.validate_token),
         db: Session = Depends(get_db)

 ):
    type = "grading_submission"
    task = run_grading_submission.delay(session_id)
    UploadSessionService.update_session_task_id(db, session_id, current_user.id, type, task.id)
    return JSONResponse({"task_id": task.id})


@router.get("/tasks/{task_id}")
def get_status(task_id):
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result if task_result.successful() else None
    }

    # Nếu có tiến trình đang chạy hoặc đã từng gọi update_state
    if task_result.info and isinstance(task_result.info, dict):
        result.update(task_result.info)

    return JSONResponse(result)


from fastapi import HTTPException
from celery.result import AsyncResult

VALID_TASK_TYPES = {"ai_detector", "plagiarism_check", "grading_submission"}


@router.post("/tasks/cancel")
def cancel_task(
        task_id: str,
        session_id: int,
        type: str,
        current_user: Users = Depends(JwtService.validate_token),
        db: Session = Depends(get_db)):
    if type not in VALID_TASK_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid task type. Must be one of {VALID_TASK_TYPES}")

    upload_session = UploadSessionService.get_upload_session_by_session_id(db, session_id, current_user.id)
    if not upload_session:
        raise HTTPException(status_code=404, detail="Session not found or unauthorized")

    try:
        task = AsyncResult(task_id)
        task.revoke(terminate=True, signal="SIGTERM")

        UploadSessionService.update_session_task(db, session_id, current_user.id, type, status="failure")

        status = task.status
        if status == "REVOKED":
            return JSONResponse({"message": f"Task {task_id} has been cancelled"})
        else:
            return JSONResponse({"message": f"Task {task_id} has been requested to cancel, current status: {status}"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")