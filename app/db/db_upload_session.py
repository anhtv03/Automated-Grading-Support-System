from typing import List

from sqlalchemy import select
from sqlalchemy.orm import subqueryload
from sqlalchemy.orm.session import Session

from app.db.models import UploadSession, Submission, SubmissionQuestion, Semester


def save_upload_session(db: Session, upload_session: UploadSession):
    try:
        db.add(upload_session)
        db.commit()
        db.refresh(upload_session)
        return upload_session
    except Exception as e:
        db.rollback()
        raise e


def query_session_by_name_semester(db: Session, name: str, semester_id: int) -> UploadSession:
    return db.query(UploadSession).filter(UploadSession.name == name, UploadSession.semester_id == semester_id).first()


def query_session_by_name_parent(db: Session, name: str, parent_session_id: int) -> UploadSession:
    return db.query(UploadSession).filter(UploadSession.name == name,
                                          UploadSession.parent_session_id == parent_session_id).first()


def get_upload_session_by_id(db: Session, id: int) -> UploadSession:
    return db.query(UploadSession).filter(UploadSession.id == id).first()


def get_upload_session_by_owner(db: Session, session_id: int, user_id: int):
    stmt = (
        select(UploadSession)
        .join(Semester)
        .where(
            UploadSession.id == session_id,
            Semester.user_id == user_id
        )
    )

    result = db.execute(stmt).scalar_one_or_none()

    return result


def query_sessions_by_semester_id(db: Session, semester_id: int):
    return db.query(UploadSession).filter(UploadSession.semester_id == semester_id,
                                          UploadSession.parent_session_id == None)


def query_child_sessions_by_parent_id(db: Session, parent_session_id: int):
    return db.query(UploadSession).filter(UploadSession.parent_session_id == parent_session_id)


def get_upload_sessions_by_session_ids(db: Session, session_ids: List[int]) -> List[UploadSession]:
    if not session_ids:
        return []
    return db.query(UploadSession).filter(UploadSession.id.in_(session_ids)).all()


def get_upload_sessions_dashboard(db: Session, semester_id: int):
    return (
        db.query(UploadSession)
        .filter(UploadSession.semester_id == semester_id)
        .options(
            subqueryload(UploadSession.submission)
            .subqueryload(Submission.question)
            .subqueryload(SubmissionQuestion.ai_grading),
            subqueryload(UploadSession.submission)
            .subqueryload(Submission.question)
            .subqueryload(SubmissionQuestion.expert_grading)
        )
    )


def update_session_info(db: Session, session_upload: UploadSession) -> UploadSession:
    try:
        db.commit()
        db.refresh(session_upload)
        return session_upload
    except Exception as e:
        db.rollback()
        raise e


def update_session_status(db: Session, session_upload: UploadSession, status: str) -> UploadSession:
    try:
        session_upload.status = status
        db.commit()
        db.refresh(session_upload)
        return session_upload
    except Exception as e:
        db.rollback()
        raise e


def delete_sessions(db: Session, sessions: List[UploadSession]):
    try:
        for session in sessions:
            db.delete(session)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e


def save_upload_sessions(db: Session, sessions: List[UploadSession]):
    try:
        db.commit()
        for session in sessions:
            db.refresh(session)
    except Exception as e:
        db.rollback()
        raise e
