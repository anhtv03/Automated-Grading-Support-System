from typing import Optional, List

from sqlalchemy.orm.session import Session

from app.constants.status import UploadSessionStatus
from app.db.models import Exam, ExamQuestion, UploadSession, Semester, Users, ExamGuideHistory
from app.external.aws_service import S3Uploader
from app.schemas.sche_exam import ExamResponse, ExamRequest


async def db_create_exam(db: Session, data: Exam) -> Optional[Exam]:
    try:
        db.add(data)
        db.commit()
        db.refresh(data)
        return data
    except Exception as e:
        db.rollback()
        raise e


def db_get_query_exams_by_session_id(db: Session, search_id: int):
    try:
        return db.query(Exam).filter(Exam.session_id == search_id)
    except Exception as e:
        db.rollback()
        raise e


def db_get_exams_by_name(db: Session, request: ExamRequest) -> Optional[List[ExamResponse]]:
    try:
        return db.query(Exam).filter(Exam.name == request.name, Exam.session_id == request.session_id).all()
    except Exception as e:
        db.rollback()
        raise e


def get_exam_by_grading_guide_id(db: Session, guide_id: int) -> Optional[Exam]:
    try:
        return (db.query(Exam)
                .join(ExamGuideHistory, ExamGuideHistory.exam_id == Exam.id)
                .filter(ExamGuideHistory.grading_guide_id == guide_id)
                .first())
    except Exception as e:
        db.rollback()
        raise e


def get_exam_by_ids(db: Session, ids: List[int]) -> Optional[List[Exam]]:
    if not ids:
        return []
    return db.query(Exam).filter(Exam.id.in_(ids)).all()

async def db_delete_exams(db: Session, ids: List[int]) -> int:
    try:
        file_keys = [item.file_key for item in db.query(Exam).filter(Exam.id.in_(ids)).all()]

        count = db.query(Exam).filter(Exam.id.in_(ids)).delete(synchronize_session=False)
        db.commit()

        for key in file_keys:
            await S3Uploader.delete_s3_file(key) if key else None

        return count
    except Exception as e:
        db.rollback()
        raise e


def db_get_exam_by_id(db: Session, search_id: int) -> Optional[Exam]:
    return db.query(Exam).filter(Exam.id == search_id).first()


def db_get_questions_existed_by_exam_id(db: Session, exam_id: int, question_name: str) -> Optional[List[ExamQuestion]]:
    return (db.query(ExamQuestion)
            .filter(ExamQuestion.exam_id == exam_id)
            .where(ExamQuestion.question_name.ilike(f'%{question_name}%'),
                   ExamQuestion.status == UploadSessionStatus.VISIBLE)
            .order_by(ExamQuestion.created_at.desc())
            .all())


def db_get_exam_by_user_and_semester_generate(db: Session, user_id: int) -> Optional[List[ExamResponse]]:
    return (db.query(Exam)
            .join(UploadSession, UploadSession.id == Exam.session_id)
            .join(Semester, Semester.id == UploadSession.semester_id)
            .join(Users, Users.id == Semester.user_id)
            .filter(Semester.type == 'ex', Users.id == user_id)
            .order_by(Exam.created_at.desc())
            .all())


def db_update_exam(db: Session, exam: Exam) -> Exam:
    try:
        db.commit()
        db.refresh(exam)
        return exam
    except Exception as e:
        db.rollback()
        raise e


def db_update_exams(db: Session, exams: List[Exam]):
    try:
        db.commit()
        for exam in exams:
            db.refresh(exam)
    except Exception as e:
        db.rollback()
        raise e
