from typing import List, Optional, Dict

from sqlalchemy import exc, and_, null, func
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.orm import subqueryload
from sqlalchemy.orm.session import Session

from app.db.models import Submission, UploadSession, Semester, SubmissionQuestion, ScoreHistory
from app.external.aws_service import S3Uploader
from app.schemas.sche_statistic import SubmissionQuestionResponse, \
    CriteriaResponse, SubmissionStatistic


async def create_submission(db: Session, new_submission: Submission) -> Optional[Submission]:
    try:
        db.add(new_submission)
        db.commit()
        db.refresh(new_submission)
        return new_submission
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise e


def db_get_submission_by_id(db: Session, id: int) -> Optional[Submission]:
    return db.query(Submission).filter(Submission.id == id).first()


def get_all_submissions_by_session_id(db: Session, session_id: int):
    return db.query(Submission).filter(Submission.session_id == session_id).all()


def get_submissions_by_submission_ids(db: Session, submission_ids: List[int]) -> Optional[List[Submission]]:
    if not submission_ids:
        return []
    return db.query(Submission).filter(Submission.id.in_(submission_ids)).all()


def is_user_owner_of_upload_session(db: Session, session_id: int, user_id: int) -> bool:
    stmt = (
        select(UploadSession)
        .join(Semester)
        .where(
            UploadSession.id == session_id,
            Semester.user_id == user_id
        )
    )

    result = db.execute(stmt).scalar_one_or_none()

    return result is not None


def get_submissions_by_session_id(db: Session, session_id: int):
    return (
        db.query(Submission)
        .filter(Submission.session_id == session_id)
        .all()
    )


def get_query_submissions_by_session_id(db: Session, session_id: int):
    return (
        db.query(Submission)
        .filter(Submission.session_id == session_id)
        .options(
            subqueryload(Submission.submission_question)
        )
    )


def create_submissions(db: Session, submissions: List[Submission]) -> List[Submission]:
    try:
        db.add_all(submissions)
        db.commit()
        for submission in submissions:
            db.refresh(submission)
        return submissions
    except Exception as e:
        db.rollback()
        raise e


async def db_delete_submissions(db: Session, ids: List[int]) -> int:
    try:
        file_keys = [item.file_key for item in db.query(Submission).filter(Submission.id.in_(ids)).all()]

        count = db.query(Submission).filter(Submission.id.in_(ids)).delete(synchronize_session=False)
        db.commit()

        for key in file_keys:
            await S3Uploader.delete_s3_file(key) if key else None

        return count
    except Exception as e:
        db.rollback()
        raise e


def get_submission_score_counts(db: Session, session_id: int) -> Dict[str, int]:
    try:
        ranges = [
            ("Not Scored", Submission.final_score.is_(null())),
            ("Poor", and_(Submission.final_score >= 0, Submission.final_score <= 3.94)),
            ("Average", and_(Submission.final_score >= 3.95, Submission.final_score <= 5.94)),
            ("Fair", and_(Submission.final_score >= 5.95, Submission.final_score <= 6.94)),
            ("Good", and_(Submission.final_score >= 6.95, Submission.final_score <= 7.94)),
            ("Very Good", and_(Submission.final_score >= 7.95, Submission.final_score <= 8.94)),
            ("Excellent", and_(Submission.final_score >= 8.95, Submission.final_score <= 10)),
        ]

        counts = (
            db.query(*[func.count().filter(cond).label(name) for name, cond in ranges])
            .filter(Submission.session_id == session_id)
            .first()
        )

        return {name: counts[i] or 0 for i, (name, _) in enumerate(ranges)}
    except Exception as e:
        db.rollback()
        raise e


def get_submission_score_by_ai_counts(db: Session, session_id: int) -> Dict[str, int]:
    try:
        query = (
            db.query(
                Submission.id.label("submission_id"),
                func.coalesce(func.sum(ScoreHistory.ai_score), 0).label("total_score")
            )
            .join(SubmissionQuestion, SubmissionQuestion.submission_id == Submission.id)
            .join(ScoreHistory, ScoreHistory.question_id == SubmissionQuestion.id)
            .filter(Submission.session_id == session_id)
            .group_by(Submission.id)
            .subquery()
        )

        ranges = [
            ("Not Scored", query.c.total_score.is_(None)),
            ("Poor", and_(query.c.total_score >= 0, query.c.total_score <= 3.94)),
            ("Average", and_(query.c.total_score >= 3.95, query.c.total_score <= 5.94)),
            ("Fair", and_(query.c.total_score >= 5.95, query.c.total_score <= 6.94)),
            ("Good", and_(query.c.total_score >= 6.95, query.c.total_score <= 7.94)),
            ("Very Good", and_(query.c.total_score >= 7.95, query.c.total_score <= 8.94)),
            ("Excellent", and_(query.c.total_score >= 8.95, query.c.total_score <= 10)),
        ]

        counts = (
            db.query(*[func.count().filter(cond).label(name) for name, cond in ranges])
            .select_from(query)
            .first()
        )

        return {name: counts[i] or 0 for i, (name, _) in enumerate(ranges)}
    except Exception as e:
        db.rollback()
        raise e


def get_ai_plagiarism_submissions_by_session_id(db: Session, session_id: int):
    return (
        db.query(Submission)
        .filter(Submission.session_id == session_id, Submission.ai_plagiarism_score >= 0.9)
        .all()
    )


def db_update_submissions(db: Session, submissions: List[Submission]) -> List[Submission]:
    try:
        for submission in submissions:
            db.merge(submission)
        db.commit()
        for submission in submissions:
            db.refresh(submission)
        return submissions
    except Exception as e:
        db.rollback()
        raise e


def get_statistics_grading_submision(db: Session, session_id: int, criteria_ids: List[int]) -> List[SubmissionStatistic]:
    sql = """
          SELECT 
                 sub.id,
                 sub.name,
                 sq."id",
                 sq.question_name,
                 sq.expert_comment,
                 sh.criteria_id,
                 sh.expert_score
          FROM submission sub
                   INNER JOIN submission_question sq ON sub.id = sq.submission_id
                   INNER JOIN score_history sh ON sh.question_id = sq.id
          WHERE sub.session_id = :session_id
            AND sh.criteria_id IN :criteria_ids
          ORDER BY sub.id ASC, sq.id ASC, sh.criteria_id; \
          """
    result = db.execute(text(sql), {"session_id": session_id, "criteria_ids": tuple(criteria_ids)}).fetchall()

    submission_map = {}
    for sub_id, sub_name, sq_id, sq_name, sq_comment, crit_id, expert_score in result:
        if sub_id not in submission_map:
            submission_map[sub_id] = SubmissionStatistic(id=sub_id, name=sub_name, questions=[])  # Pydantic tự khởi tạo questions=[]

        submission = submission_map[sub_id]
        question = next((q for q in submission.questions if q.id == sq_id), None) if submission.questions is not None else None
        if not question:
            question = SubmissionQuestionResponse(id=sq_id, question_name=sq_name, expert_comment=sq_comment)
            submission.questions.append(question)

        question.criteria.append(CriteriaResponse(criteria_id=crit_id, expert_score=expert_score))

    return list(submission_map.values())

