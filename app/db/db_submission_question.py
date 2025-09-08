from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm.session import Session

from app.db.models import SubmissionQuestion, Submission
from app.schemas.sche_submisson_question import SubmissionQuestionCreateRequest, SubmissionQuestionUpdateRequest, \
    CriteriaHistoryResponse


def get_submission_questions_id(db: Session, id: int) -> SubmissionQuestion:
    return db.query(SubmissionQuestion).filter(SubmissionQuestion.id == id).first()


def save_submission_question(db: Session, request: SubmissionQuestionCreateRequest):
    try:
        new_submission = SubmissionQuestion(
            submission_id=request.submission_id,
            question_name=request.question_name
        )
        db.add(new_submission)
        db.flush()
        db.refresh(new_submission)
        return new_submission
    except Exception as e:
        db.rollback()
        raise e


def create_submission_questions(db: Session, submission_questions: List[SubmissionQuestion]) -> Optional[
    List[SubmissionQuestion]]:
    try:
        db.add_all(submission_questions)
        db.commit()
        for new_submission in submission_questions:
            # Refresh each submission to get the updated state
            db.refresh(new_submission)
        return submission_questions
    except Exception as e:
        db.rollback()
        raise e


def update_submission_question_cluster_id(db: Session, request: SubmissionQuestionUpdateRequest):
    try:
        submission_question = db.query(SubmissionQuestion).filter(SubmissionQuestion.id == request.id).first()
        if submission_question:
            submission_question.cluster_id = request.cluster_id
            db.commit()
            db.refresh(submission_question)
        return submission_question
    except Exception as e:
        db.rollback()
        raise e


def get_submission_questions_by_exam_id(db: Session, session_id: int):
    return (
        db.query(SubmissionQuestion)
        .join(Submission, SubmissionQuestion.submission_id == Submission.id)
        .filter(Submission.session_id == session_id)
        .all()
    )


def get_submission_question_by_submission_and_question_name(
        db: Session, sub_id: int, question_name: str
):
    return (
        db.query(SubmissionQuestion)
        .filter(
            SubmissionQuestion.id == sub_id,
            SubmissionQuestion.question_name == question_name
        )
        .first()
    )


def get_submission_question_by_sub_id(db: Session, sub_id: int) -> Optional[List[SubmissionQuestion]]:
    return db.query(SubmissionQuestion).filter(SubmissionQuestion.submission_id == sub_id).all()


def get_sub_question_by_sub_id(db: Session, sub_id: int) -> Optional[List[SubmissionQuestion]]:
    return db.query(SubmissionQuestion).filter(SubmissionQuestion.submission_id == sub_id).all()


def db_get_score_history_by_submission_id(db: Session, submission_id: int) -> List[CriteriaHistoryResponse]:
    try:
        query = """
                SELECT sq.submission_id, \
                       sq.id  AS "question_id", \
                       sq.question_name, \
                       c.id   AS "criteria_id", \
                       c.name AS "criteria_title", \
                       c.max_point, \
                       sh.ai_score, \
                       sh.expert_score
                FROM public.submission_question sq
                         JOIN public.score_history sh ON sh.question_id = sq.id
                         JOIN public.criteria c ON c.id = sh.criteria_id
                WHERE sq.submission_id = :submission_id
                ORDER BY sq.id ASC, c.id ASC \
                """
        result = db.execute(text(query), {"submission_id": submission_id}).fetchall()

        response = [
            CriteriaHistoryResponse(
                submission_id=row.submission_id,
                question_id=row.question_id,
                question_name=row.question_name,
                criteria_id=row.criteria_id,
                criteria_title=row.criteria_title,
                max_point=row.max_point,
                ai_score=row.ai_score,
                expert_score=row.expert_score
            )
            for row in result
        ]
        return response
    except Exception as e:
        db.rollback()
        raise e


def db_update_submission_question_comments(db: Session, questions: List[SubmissionQuestion]):
    try:
        db.commit()
        for question in questions:
            db.refresh(question)
    except Exception as e:
        db.rollback()
        raise e
