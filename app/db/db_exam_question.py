from typing import Optional, List

from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.session import Session

from app.constants.status import UploadSessionStatus
from app.db.db_material import db_delete_material_by_id
from app.db.models import ExamQuestion
from app.services.document_service import MaterialService


def db_get_exam_question_by_id(db: Session, search_id: int) -> Optional[ExamQuestion]:
    return db.query(ExamQuestion).filter(ExamQuestion.id == search_id).first()


def db_get_exam_question_by_ids(db: Session, ids: List[int]) -> Optional[List[ExamQuestion]]:
    if not ids:
        return []
    return db.query(ExamQuestion).filter(ExamQuestion.id.in_(ids)).all()


def db_get_exam_questions_by_exam_id(db: Session, exam_id: int) -> Optional[List[ExamQuestion]]:
    return (db.query(ExamQuestion)
            .filter(ExamQuestion.exam_id == exam_id)
            .order_by(ExamQuestion.question_name.asc())
            .all())


def db_get_exam_questions_by_exam_id_and_question_name(db: Session, exam_id: int, question_name: str) -> Optional[
    List[ExamQuestion]]:
    return (db.query(ExamQuestion)
            .filter(ExamQuestion.exam_id == exam_id, ExamQuestion.question_name.ilike(f'%{question_name}%'))
            .order_by(ExamQuestion.created_at.desc())
            .all()
            )


def db_get_exam_questions_visible(
        db: Session,
        exam_id: int,
        question_name: str
) -> Optional[ExamQuestion]:
    return (db.query(ExamQuestion)
            .filter(ExamQuestion.exam_id == exam_id, ExamQuestion.question_name.ilike(f'%{question_name}%'),
                    ExamQuestion.status == UploadSessionStatus.VISIBLE)
            .order_by(ExamQuestion.created_at.desc())
            .first())


def db_query_exam_questions_by_exam_id(db: Session, exam_id: int):
    return db.query(ExamQuestion).filter(ExamQuestion.exam_id == exam_id)


def db_create_exam_question(db: Session, exam_question: ExamQuestion) -> Optional[ExamQuestion]:
    try:
        db.add(exam_question)
        db.commit()
        db.refresh(exam_question)
        return exam_question
    except Exception as e:
        db.rollback()
        raise e


def db_update_exam_question_content(db: Session, exam_question: ExamQuestion) -> ExamQuestion:
    try:
        flag_modified(exam_question, "criteria")
        db.commit()
        db.refresh(exam_question)
        return exam_question
    except Exception as e:
        db.rollback()
        raise e


def db_update_questions(db: Session, questions: List[ExamQuestion]):
    try:
        db.commit()
        for question in questions:
            db.refresh(question)
    except Exception as e:
        db.rollback()
        raise e


async def db_delete_exam_questions(db: Session, exam_question_id: int) -> int:
    try:
        MaterialService.delete_material(exam_question_id, db_delete_material_by_id, db)

        exam_question = db_get_exam_question_by_id(db, exam_question_id)
        exam_id = exam_question.exam_id
        count = db.query(ExamQuestion).filter(ExamQuestion.id == exam_question_id).delete(synchronize_session=False)

        if count:
            deleted_name = exam_question.question_name
            cursor = db.connection().connection.cursor()
            cursor.execute(
                "CALL update_exam_question_titles(%s, %s)",
                (exam_id, deleted_name)
            )
            cursor.close()

        db.commit()
        return count
    except Exception as e:
        db.rollback()
        raise e


async def db_delete_exam_questions_by_exam_id(db: Session, exam_question_id: int) -> int:
    try:
        MaterialService.delete_material(exam_question_id, db_delete_material_by_id, db)
        count = db.query(ExamQuestion).filter(ExamQuestion.id == exam_question_id).delete(synchronize_session=False)

        db.commit()
        return count
    except Exception as e:
        db.rollback()
        raise e
