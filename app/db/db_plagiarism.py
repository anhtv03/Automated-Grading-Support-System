from sqlalchemy.orm.session import Session


def get_plagiarized_submission_pairs(db: Session, session_id: int, number_question: int, threshold: float):
    sql = """
    WITH all_matches AS (
    SELECT
        sq1.submission_id AS sub_a,
        sq2.submission_id AS sub_b,
        sq1.question_name,
        pr.similarity_score AS score
    FROM plagiarism_result pr
    JOIN submission_question sq1 ON pr.source_id = sq1.id
    JOIN submission_question sq2 ON pr.plagiarism_id = sq2.id
    JOIN submission s1 ON sq1.submission_id = s1.id
    JOIN submission s2 ON sq2.submission_id = s2.id
    WHERE sq1.submission_id != sq2.submission_id
      AND s1.session_id = :session_id
      AND s2.session_id = :session_id
),
grouped_similarity AS (
    SELECT
        LEAST(am.sub_a, am.sub_b) AS sub1,
        GREATEST(am.sub_a, am.sub_b) AS sub2,
        COUNT(*) FILTER (WHERE am.score >= 0.9) AS matched_questions
    FROM all_matches am
    GROUP BY LEAST(am.sub_a, am.sub_b), GREATEST(am.sub_a, am.sub_b)
),
plagiarism_check AS (
    SELECT 
        gs.sub1,
        gs.sub2,
        gs.matched_questions,
        ROUND((gs.matched_questions::float / :number_question)::numeric, 2) AS similarity_score
    FROM grouped_similarity gs
)
SELECT pc.sub1 AS source_id,
       pc.sub2 AS plagiarism_id, 
       pc.similarity_score,
       s1.name     AS source_name,
       s1.file_key AS source_path,
       s2.name     AS plagiarism_name,
       s2.file_key AS plagiarism_path
FROM plagiarism_check pc
JOIN submission s1 ON pc.sub1 = s1.id
JOIN submission s2 ON pc.sub2 = s2.id
WHERE pc.similarity_score >= :threshold;
    """
    result = db.execute(text(sql), {
        "session_id": session_id,
        "number_question": number_question,
        "threshold": threshold
    }).fetchall()
    return result

def count_plagiarized_submissions(db: Session,session_id: int,num_questions: int,threshold: float) -> int:
    sql = """
        WITH valid_questions AS (
            SELECT sq.id, sq.submission_id
            FROM submission_question sq
            JOIN submission s ON s.id = sq.submission_id
            WHERE s.session_id = :session_id
        ),
        paired_plagiarism AS (
            SELECT 
                LEAST(sq1.submission_id, sq2.submission_id) AS sub1,
                GREATEST(sq1.submission_id, sq2.submission_id) AS sub2,
                COUNT(*) AS matched_count
            FROM plagiarism_result pr
            JOIN valid_questions sq1 ON pr.source_id = sq1.id
            JOIN valid_questions sq2 ON pr.plagiarism_id = sq2.id
            WHERE pr.similarity_score >= 0.9
              AND sq1.submission_id != sq2.submission_id
            GROUP BY LEAST(sq1.submission_id, sq2.submission_id), GREATEST(sq1.submission_id, sq2.submission_id)
        ),
        plagiarism_ratio AS (
            SELECT sub1,
                sub2,
                matched_count,
                ROUND(matched_count::numeric / :num_questions, 2) AS ratio
            FROM paired_plagiarism
        ),
        plagiarized_submissions AS (
            SELECT sub1 AS sub_id FROM plagiarism_ratio WHERE ratio >= :threshold
            UNION
            SELECT sub2 AS sub_id FROM plagiarism_ratio WHERE ratio >= :threshold
        )
        SELECT COUNT(DISTINCT sub_id) FROM plagiarized_submissions;
    """
    result = db.execute(
        text(sql),
        {
            "session_id": session_id,
            "num_questions": num_questions,
            "threshold": threshold
        }
    ).scalar()

    return result or 0

from sqlalchemy.orm import Session
from sqlalchemy.sql import text
def get_plagiarism_details_by_submission(db: Session, submission_id: int):
    sql = """
    SELECT 
        s1.id AS source_id,
        s1.name AS source_name,
        s1.file_key AS source_path,

        s2.id AS target_id,
        s2.name AS target_name,
        s2.file_key AS target_path,

        sq1.id AS question_id_a,
        sq1.question_name AS question_name_a,

        sq2.id AS question_id_b,
        sq2.question_name AS question_name_b,

        ROUND(pr.similarity_score::numeric, 2) AS similarity_score

    FROM plagiarism_result pr
    JOIN submission_question sq1 ON pr.source_id = sq1.id
    JOIN submission_question sq2 ON pr.plagiarism_id = sq2.id
    JOIN submission s1 ON sq1.submission_id = s1.id
    JOIN submission s2 ON sq2.submission_id = s2.id
    WHERE (s1.id = :submission_id OR s2.id = :submission_id)
    ORDER BY sq1.question_name;
    """

    result = db.execute(
        text(sql),
        {"submission_id": submission_id}
    ).fetchall()

    return result
