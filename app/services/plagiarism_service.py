import re
from typing import List, Tuple, Dict, Any

import nltk
import numpy as np
from fastapi import HTTPException
from nltk.corpus import stopwords
from scipy.sparse import csr_matrix
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.db.db_plagiarism import get_plagiarism_details_by_submission, get_plagiarized_submission_pairs, \
    count_plagiarized_submissions
from app.db.db_plagiarism_result import save_plagiarism_result, get_plagiarism_results_by_session
from app.db.db_upload_session import get_upload_session_by_id
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.schemas.sche_plagiarism import PlagiarismResultItem, PlagiarismDetailResponse
from app.schemas.sche_plagiarism_result import PlagiarismCreateRequest
from app.schemas.sche_submission import SubmissionResponse, SubmissionPlagiarismResponse
from app.schemas.sche_submisson_question import SubmissionQuestionUpdateRequest, SubmissionQuestionData
from app.services.submission_question_service import QuestionService
from app.services.submission_service import SubmissionService
from app.services.upload_session_service import UploadSessionService
from app.constants.status import UploadSessionTaskStatus
from app.services.file_service import FileService
from app.services.answer_template_service import AnswerTemplateService
from app.schemas.sche_upload_session import UploadSessionUpdateTaskStatus
from app.schemas.sche_api_response import DataResponse
import logging
# sample stop word
MINIMAL_STOP_WORDS = {'a', 'an', 'the'}

logger = logging.getLogger(__name__)
class PlagiarismService:

    @staticmethod
    def preprocess_text(text: str) -> str:
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        words = [w for w in text.split() if w not in MINIMAL_STOP_WORDS]
        text = " ".join(words)
        logger.debug(f"Văn bản sau tiền xử lý: {text}")
        return text

    def compute_tfidf(texts: List[str]) -> Tuple[np.ndarray, TfidfVectorizer]:
        # try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts)
        return tfidf_matrix, vectorizer

    # except CustomException as e:
        #     raise
        # except Exception as e:
        #     raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)


    @staticmethod
    async def assign_to_cluster_zero(
            db: Session,
            nonzero_ids: np.ndarray,
            skipped_ids: List[int],
            nonzero_vectors: np.ndarray,
            cluster_labels: List[int],
            used_ids: List[int]
    ):
        """Gán tất cả bài nộp vào cụm 0 và trả về kết quả."""
        logger.info("Gán tất cả bài nộp vào cụm 0")
        for sub_ques_id in nonzero_ids:
            await QuestionService.update_cluster_id(
                db,
                SubmissionQuestionUpdateRequest(id=int(sub_ques_id), cluster_id=0)
            )
            cluster_labels.append(0)
            used_ids.append(int(sub_ques_id))
        return {
            "used_ids": used_ids,
            "cluster_labels": cluster_labels,
            "skipped_ids": skipped_ids,
            "mapped_ids": nonzero_ids.tolist(),
            "vectors_dense": nonzero_vectors
        }

    @staticmethod
    async def cluster_and_update_documents(
            db: Session,
            question_name: str,
            tfidf_matrix,  # CSR matrix
            sub_ques_ids: List[int],
            k_max: int = 10
    ):
        vectors_dense = tfidf_matrix.toarray()
        row_sums = np.sum(vectors_dense, axis=1)

        # 1. Lọc vector hợp lệ (≠ 0)
        nonzero_mask = row_sums > 0
        nonzero_vectors = vectors_dense[nonzero_mask]
        nonzero_ids = np.array(sub_ques_ids)[nonzero_mask]

        # 2. Bỏ qua vector 0
        zero_ids = np.array(sub_ques_ids)[~nonzero_mask]
        skipped_ids = zero_ids.tolist()

        cluster_labels = []
        used_ids = []

        n = len(nonzero_vectors)
        logger.info(f"Số lượng vector hợp lệ: {n}")

        # 3. Nếu có 0 hoặc 1 bài hợp lệ → không clustering
        if n <= 1:
            logger.info("Không đủ vector hợp lệ để phân cụm")
            return {
                "used_ids": used_ids,
                "cluster_labels": cluster_labels,
                "skipped_ids": skipped_ids,
                "mapped_ids": nonzero_ids.tolist(),
                "vectors_dense": nonzero_vectors
            }

        # 4. Nếu có 15 bài hoặc ít hơn → gán tất cả vào cụm 0
        elif n <= 15:
            logger.info("Số lượng bài nộp <= 15, gán tất cả vào cụm 0")
            return await PlagiarismService.assign_to_cluster_zero(
                db, nonzero_ids, skipped_ids, nonzero_vectors, cluster_labels, used_ids
            )

        # 5. Nếu > 15 bài → clustering linh hoạt
        else:
            unique_vectors = np.unique(nonzero_vectors, axis=0)
            max_clusters = len(unique_vectors)
            logger.debug(f"Số lượng vector độc nhất: {max_clusters}")
            if max_clusters < 2:
                logger.info("Không đủ vector độc nhất, gán tất cả vào cụm 0")
                return await PlagiarismService.assign_to_cluster_zero(
                    db, nonzero_ids, skipped_ids, nonzero_vectors, cluster_labels, used_ids
                )

            k_range = range(2, min(k_max + 1, n // 2, max_clusters + 1))
            if not k_range:
                logger.warning("k_range rỗng, gán tất cả vào cụm 0")
                return await PlagiarismService.assign_to_cluster_zero(
                    db, nonzero_ids, skipped_ids, nonzero_vectors, cluster_labels, used_ids
                )

            silhouette_scores = []
            for k in k_range:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
                labels = kmeans.fit_predict(nonzero_vectors)
                if len(set(labels)) > 1:  # Chỉ tính silhouette score nếu có nhiều hơn một cụm
                    score = silhouette_score(nonzero_vectors, labels)
                    silhouette_scores.append(score)
                    logger.debug(f"Điểm silhouette cho k={k}: {score}")
                else:
                    logger.warning(f"Chỉ tạo được một cụm cho k={k}, bỏ qua")

            if not silhouette_scores:
                logger.warning("Không có điểm silhouette hợp lệ, gán tất cả vào cụm 0")
                return await PlagiarismService.assign_to_cluster_zero(
                    db, nonzero_ids, skipped_ids, nonzero_vectors, cluster_labels, used_ids
                )

            optimal_k = k_range[np.argmax(silhouette_scores)]
            kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init="auto")
            labels = kmeans.fit_predict(nonzero_vectors)

            for i, cluster_id in enumerate(labels):
                sub_ques_id = int(nonzero_ids[i])
                logger.info(f"sub_id: {sub_ques_id} and question_name: {question_name} have cluster_id: {cluster_id}")
                await QuestionService.update_cluster_id(
                    db,
                    SubmissionQuestionUpdateRequest(id=sub_ques_id, cluster_id=int(cluster_id))
                )
                cluster_labels.append(int(cluster_id))
                used_ids.append(sub_ques_id)

        return {
            "used_ids": used_ids,
            "cluster_labels": cluster_labels,
            "skipped_ids": skipped_ids,
            "mapped_ids": nonzero_ids.tolist(),
            "vectors_dense": nonzero_vectors
        }

    @staticmethod
    async def check_plagiarism_in_clusters(
            db: Session,
            tfidf_matrix: np.ndarray | csr_matrix,
            question_name: str,
            sub_ques_ids: List[int],
            cluster_labels: np.ndarray,
            threshold: float = 0.9
    ) -> List[Dict[str, Any]]:
        # try:
            vectors_dense = tfidf_matrix if isinstance(tfidf_matrix, np.ndarray) else tfidf_matrix.toarray()
            results = []

            unique_clusters = np.unique(cluster_labels)
            for cluster_id in unique_clusters:
                cluster_indices = np.where(cluster_labels == cluster_id)[0]
                if len(cluster_indices) < 2:
                    continue

                cluster_vectors = vectors_dense[cluster_indices]
                similarities = cosine_similarity(cluster_vectors)

                for i in range(len(cluster_indices)):
                    for j in range(i + 1, len(cluster_indices)):
                        if similarities[i][j] > threshold:
                            sub_ques_1 = await QuestionService.get_submission_question_by_question_name(
                                db, sub_ques_ids[cluster_indices[i]], question_name
                            )
                            sub_ques_2 = await QuestionService.get_submission_question_by_question_name(
                                db, sub_ques_ids[cluster_indices[j]], question_name
                            )

                            if not sub_ques_1 or not sub_ques_2:
                                raise HTTPException(
                                    status_code=404,
                                    detail=f"Submission not found for sub {sub_ques_ids[cluster_indices[i]]} in {question_name} or {sub_ques_ids[cluster_indices[j]]}"
                                )

                            # Lưu vào DB
                            plagiarism_result = PlagiarismCreateRequest(
                                source_id=sub_ques_1.id,
                                plagiarism_id=sub_ques_2.id,
                                similarity_score=round(float(similarities[i][j]), 2)
                            )

                            save_plagiarism_result(db, plagiarism_result)

                            results.append({
                                "document_source": sub_ques_1.id,
                                "document_plagiarism": sub_ques_2.id,
                                "similarity_score": float(similarities[i][j])
                            })
            return results
        # except CustomException as e:
        #     raise
        # except Exception as e:
        #     raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
    async def get_results_by_session(db: Session, session_id: int):
        # try:
            return get_plagiarism_results_by_session(db, session_id)
        # except CustomException as e:
        #     raise
        # except Exception as e:
        #     raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    async def get_detected_plagiarism_pairs(db: Session, session_id: int) -> List[PlagiarismResultItem]:
        upload_session = get_upload_session_by_id(db, session_id)
        number_question = 4
        threshold = 0.5
        if upload_session is None:
            raise CustomException(ErrorCode.SESSION_UPLOAD_NOT_FOUND)
        rows = get_plagiarized_submission_pairs(db, session_id, number_question, threshold)
        result = []

        for row in rows:
            result.append(PlagiarismResultItem(
                similarity_score=row.similarity_score,
                source=SubmissionResponse(
                    id=row.source_id,
                    name=row.source_name,
                    file_key=row.source_path
                ),
                plagiarism=SubmissionResponse(
                    id=row.plagiarism_id,
                    name=row.plagiarism_name,
                    file_key=row.plagiarism_path
                )
            ))

        return result

    async def get_number_of_plagiarized_submissions(db: Session, session_id: int) -> int:
        upload_session = get_upload_session_by_id(db, session_id)
        number_question = 4
        threshold = 0.5
        if upload_session is None:
            raise CustomException(ErrorCode.SESSION_UPLOAD_NOT_FOUND)
        return count_plagiarized_submissions(db, session_id, number_question, threshold)

    async def get_plagiarism_detail(db: Session, submission_id: int) -> PlagiarismDetailResponse:
        submission = SubmissionService.get_by_id(db, submission_id)
        rows = get_plagiarism_details_by_submission(db, submission_id)
        if not rows:
            # Trả về object hợp lệ, nhưng không có thông tin đạo văn
            return PlagiarismDetailResponse(
                source=SubmissionResponse(
                    id=submission.id,
                    name=submission.name,
                    file_key=submission.file_key
                ),
                plagiarism=[]
            )
        source_submission = None
        plagiarism_map = {}
        for row in rows:
            # Xác định đâu là nguồn (submission đang được xem)
            if row.source_id == submission_id:
                source_id = row.source_id
                target_id = row.target_id
                target_name = row.target_name
                target_path = row.target_path
                question_id = row.question_id_a
                question_name = row.question_name_a
            else:
                source_id = row.target_id
                target_id = row.source_id
                target_name = row.source_name
                target_path = row.source_path
                question_id = row.question_id_b
                question_name = row.question_name_b

            # Gán submission nguồn duy nhất
            if not source_submission:
                source_submission = SubmissionResponse(
                    id=submission_id,
                    name=row.source_name if row.source_id == submission_id else row.target_name,
                    file_key=row.source_path if row.source_id == submission_id else row.target_path
                )

            # Gom nhóm theo bài đạo văn
            if target_id not in plagiarism_map:
                plagiarism_map[target_id] = SubmissionPlagiarismResponse(
                    id=target_id,
                    name=target_name,
                    file_key=target_path,
                    questions=[]
                )

            plagiarism_map[target_id].questions.append(
                SubmissionQuestionData(
                    id=question_id,
                    question_name=question_name,
                    score=float(row.similarity_score)
                )
            )

        return PlagiarismDetailResponse(
            source=source_submission,
            plagiarism=list(plagiarism_map.values())
        )

    async def check_plagiarism(
            session_id: int,
            user_id: int,
            db: Session
    ):
        session = UploadSessionService.get_upload_session_by_session_id(db, session_id, user_id)
        if session.plagiarism_status == UploadSessionTaskStatus.COMPLETED:
            return DataResponse().custom_response_list(
                code="0",
                message="Have check plagiarism before",
                data=None
            )
        # if not grading or plagiarism before will insert submission question
        # if (session.plagiarism_status == UploadSessionTaskStatus.NOT_START) and (session.grading_status == UploadSessionTaskStatus.NOT_START):
        #     FileService.create_submission_questions(db, session_id)
        # get all submission by session_id
        submissions = SubmissionService.get_all_submissions_by_session_id(db, session_id)
        grouped = {}
        # loop submission to extract content to question {questionName: "content"}
        for submission in submissions:
            blocks = submission.content.split("\n")
            questions = FileService.group_blocks_by_question(blocks)
            question_content_map = {
                q["questionName"].strip().capitalize(): q["content"]
                for q in questions
            }

            submission_questions = await QuestionService.get_submission_question_by_submission_id(db, submission.id)
            # add content into question
            for sq in submission_questions:
                qname = sq.question_name.strip().capitalize()
                content = question_content_map.get(qname, "").strip()
                if not content:
                    continue
                if qname not in grouped:
                    grouped[qname] = {
                        "question_name": qname,
                        "question_ids": [],
                        "question_content": []
                    }

                grouped[qname]["question_ids"].append(sq.id)
                grouped[qname]["question_content"].append(content)
        template = AnswerTemplateService.get_exam_template_by_session_id(session_id, db)
        template_question_map = {}
        if template:
            blocks_temp = template.content.split("\n")
            template_questions = FileService.group_blocks_by_question(blocks_temp)
            template_question_map = {
                q["questionName"]: PlagiarismService.preprocess_text(q["content"])
                for q in template_questions
            }

        for group in grouped.values():
            question_name = group["question_name"]
            texts = group["question_content"][:]

            if question_name in template_question_map:
                texts.append(template_question_map[question_name])
                has_template = True
            else:
                has_template = False

            cleaned_texts = [PlagiarismService.preprocess_text(t) for t in texts]
            tfidf_matrix, tfidf_model = PlagiarismService.compute_tfidf(cleaned_texts)
            if has_template:
                tfidf_matrix = PlagiarismService.subtract_template(tfidf_matrix)

            result = await PlagiarismService.cluster_and_update_documents(
                db=db,
                question_name=question_name,
                tfidf_matrix=tfidf_matrix,
                sub_ques_ids=group["question_ids"],
                k_max=10
            )
            vectors_dense = result["vectors_dense"]
            mapped_ids = result["mapped_ids"]
            used_ids = result["used_ids"]

            id_to_index = {qid: idx for idx, qid in enumerate(mapped_ids)}

            used_vectors = [vectors_dense[id_to_index[qid]] for qid in used_ids]

            filtered_matrix = np.array(used_vectors)

            plagiarism_results = await PlagiarismService.check_plagiarism_in_clusters(
                db=db,
                tfidf_matrix=filtered_matrix,
                question_name=question_name,
                sub_ques_ids=used_ids,
                cluster_labels=result["cluster_labels"],
                threshold=0.9
            )

        results = await PlagiarismService.get_results_by_session(db, session_id)

        # update status upload session
        session_status = UploadSessionUpdateTaskStatus(
            id=session_id,
            status=UploadSessionTaskStatus.COMPLETED
        )
        UploadSessionService.update_session_task_status(db, session_status, user_id)

        # return json_data
        return DataResponse().custom_response_list(
            code="0",
            message="Check plagiarism success",
            data=None
        )

    def subtract_template(tfidf_matrix):
        if tfidf_matrix.shape[0] <= 1:
            raise HTTPException(status_code=400, detail="Insufficient documentation after removing template")

        template_vector = tfidf_matrix[-1]
        matrix_wo_template = tfidf_matrix[:-1]

        if template_vector.shape[1] != matrix_wo_template.shape[1]:
            raise HTTPException(status_code=500, detail="Shape mismatch.")

        A = matrix_wo_template.toarray()
        T = template_vector.toarray().reshape(1, -1)

        result = np.maximum(A - T, 0)
        return csr_matrix(result)
