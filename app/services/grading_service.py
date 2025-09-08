import json
from typing import Dict, List, Any

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.db_criteria import find_criteria
from app.db.db_grading_guide import db_get_grading_guide_by_session_id
from app.db.db_guide_question import get_guide_questions
from app.db.db_score_history import get_score_history
from app.db.db_submission import get_submissions_by_session_id
from app.db.db_submission_question import get_submission_question_by_sub_id
from app.db.db_upload_session import get_upload_session_by_id, update_session_info
from app.db.models import GradingGuide, Criteria
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode


class GradingService:
    @staticmethod
    def grade_submissions(db: Session, session_id: int) -> Any:
        try:
            # Fetch grading guide and questions
            grading_guide = db_get_grading_guide_by_session_id(db, session_id).first()
            if not grading_guide:
                raise CustomException(ErrorCode.GUIDE_GRADING_GUIDE_NOT_FOUND)

            guide_questions = get_guide_questions(db, grading_guide.id)
            guide_content_map: Dict[str, str] = {gq.question_name: gq.content for gq in guide_questions}

            criteria_map = GradingService.get_criteria_map(db, grading_guide)
            if len(guide_content_map) != len(criteria_map):
                raise CustomException(ErrorCode.COM_GUIDE_CONTENT_MISMATCH)

            # Fetch all submissions and their questions in one go
            submissions = get_submissions_by_session_id(db, session_id)
            sub_questions_map = {sub.id: get_submission_question_by_sub_id(db, sub.id) for sub in submissions}

            # output_dir = "extracted_json_content"
            # os.makedirs(output_dir, exist_ok=True)

            # Process submissions
            for submission in submissions:
                sub_id = submission.id
                sub_questions = sub_questions_map.get(sub_id, [])

                # Create a JSON structure for this submission
                # submission_data = {
                #     "submission_id": sub_id,
                #     "submission_name": getattr(submission, 'name', f"submission_{sub_id}"),
                #     "prompts": []
                # }

                for sq in sub_questions:
                    q_name = sq.question_name
                    if q_name not in criteria_map or q_name not in guide_content_map:
                        continue

                    criteria_list = criteria_map[q_name]
                    guide_content = guide_content_map[q_name]

                    try:
                        # Stringify criteria names
                        criteria_str = "\n".join(c.name for c in criteria_list if hasattr(c, 'name'))

                        # Define instruction and constraints
                        instruction = (
                            "As an expert in Software Testing, grade the submission based on the provided Grading Guide. "
                            "Strictly follow the Marking Criteria to assign points. Extract the main criteria from the "
                            "Detailed Answer and assign scores without per-criterion explanations. Base your evaluation "
                            "on trained Software Testing knowledge and the project context provided in the Question. "
                            "Your response must be EXCLUSIVELY a valid JSON object starting with '{' and ending with '}', "
                            "with no introductory text, explanations, or any other content before or after the JSON. "
                            "The \"max_score\" values in the \"criteria\" array are fixed and must not be altered under any circumstances."
                            "\"general_comment\": A concise comment (20-50 words) evaluating the submission's alignment "
                            "with the Marking Criteria and project context."
                        )

                        constraints = (
                            "Constraints:\n"
                            "- If the submission contains no data, set all criterion scores to 0 and "
                            "\"general_comment\": \"No content provided, evaluation not possible.\"\n"
                            "- For each criterion, the score MUST be <= max_score, and max_score must remain UNCHANGED from the Sample.\n"
                            "- Only modify \"score\" within \"criteria\" and \"general_comment\"; all other fields and the structure must remain identical to the Sample.\n"
                            "- Return ONLY the JSON object as shown in the Sample, with no additional text or content.\n"
                            "- The output must be pure JSON without any wrapping text, prefixes like 'Here is the JSON:', or additional lines.\n"
                            "- Strictly preserve the \"max_score\" values as provided in the Sample; any modification to \"max_score\" will invalidate the response."
                        )

                        # Generate sample JSON as string with \n, including max_score
                        sample_criteria = ",\n".join(
                            f'    {{\n'
                            f'        "criterion": "{c.name}",\n'
                            f'        "score": 0,\n'
                            f'        "max_score": {c.max_point or 0}\n'
                            f'    }}'
                            for c in criteria_list
                        )

                        sample = (
                            "Sample:\n"
                            '{\n'
                            f'  "criteria": [\n{sample_criteria}\n  ],\n'
                            '  "general_comment": ""\n'
                            '}'
                        )

                        # Create system and user content
                        # system_content = f"{instruction}\n\n{constraints}\n\n{sample}\n\n"
                        # user_content = f"Grading guide: \n{guide_content}\n\nSubmission: {sq.content if sq.content else ''}"
                        # submission_data["prompts"].append([
                        #     {"role": "system", "content": system_content},
                        #     {"role": "user", "content": user_content}
                        # ])

                        # Build prompt
                        prompt1 = f"{instruction}\n\n{constraints}\n\n{sample}"
                        prompt2 = f"Grade the following student submission based on the provided grading guide\nGrading guide: \n{guide_content}\n\nSubmission: {sq.content if sq.content else ''}"

                        # Call AI service with retry logic
                        # max_retries = 3
                        # for attempt in range(max_retries):
                        #     result = GradingService.get_score(prompt1, prompt2)
                        #
                        #     # Parse JSON content from result
                        #     result_data = json.loads(result)
                        #
                        #     # Check if max_score is unchanged and score <= max_score
                        #     is_valid = True
                        #     for crit in criteria_list:
                        #         for criterion in result_data.get("criteria", []):
                        #             if criterion["criterion"] == crit.name:
                        #                 original_max_score = crit.max_point or 0
                        #                 if (criterion.get("score", 0) > criterion.get("max_score", 0) or
                        #                         criterion.get("max_score", 0) != original_max_score):
                        #                     is_valid = False
                        #                     break
                        #         if not is_valid:
                        #             break
                        #
                        #     if is_valid:
                        #         break
                        #     else:
                        #         print(f"Attempt {attempt + 1}/{max_retries} failed: Invalid score or max_score for question {sq.id}. Retrying...")
                        #         if attempt == max_retries - 1:
                        #             print.error(f"Max retries reached for question {sq.id}. Using default scores.")
                        #             result_data = {
                        #                 "criteria": [{"criterion": c.name, "score": 0, "max_score": c.max_point or 0}
                        #                              for c in criteria_list],
                        #                 "general_comment": "Evaluation failed after multiple retries due to invalid scoring."
                        #             }

                        # Update submission question

                        result = GradingService.get_score(prompt1, prompt2)
                        result_data = json.loads(result)


                        sq.ai_comment = result_data.get("general_comment", "")

                        # Create lookup dict for criteria scores
                        criteria_scores = {crit["criterion"]: crit.get("score", 0) for crit in
                                           result_data.get("criteria", [])}

                        # Update score history
                        for crit in criteria_list:
                            score_hist = get_score_history(db, sq.id, crit.id)
                            if score_hist and crit.name in criteria_scores:
                                score_hist.ai_score = criteria_scores[crit.name]

                    except Exception as e:
                        continue
                # if submission_data["prompts"]:
                #     output_json_path = os.path.join(output_dir, f"submission_{sub_id}_prompts.json")
                #     with open(output_json_path, "w", encoding="utf-8") as f:
                #         json.dump(submission_data, f, ensure_ascii=False, indent=4)
                #     print(f"Submission prompts saved to: {output_json_path}")

            session = get_upload_session_by_id(db, session_id)
            session.grading_status = "completed"
            update_session_info(db, session)

            db.commit()  # Single commit at the end
        except CustomException as e:
            raise e
        except Exception as e:
            db.rollback()  # Rollback on global error
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_criteria_map(db: Session, guide: GradingGuide) -> Dict[str, List[Criteria]]:
        if not guide:
            raise CustomException(ErrorCode.GUIDE_GRADING_GUIDE_NOT_FOUND)

        criteria_map: Dict[str, List[Criteria]] = {}
        for q_num in range(1, guide.question_number + 1):
            criteria = find_criteria(db, guide.id, q_num)
            if not criteria:
                raise CustomException(ErrorCode.GUIDE_GRADING_GUIDE_NOT_FOUND)
            criteria_map[f"Question {q_num}"] = criteria

        return criteria_map

    @staticmethod
    def get_score(prompt1: str, prompt2: str) -> str:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        try:
            response = client.chat.completions.create(
                model="ft:gpt-4o-mini-2024-07-18:personal:apegss-swt301:C57C6t8n",
                messages=[
                    {"role": "system",
                     "content": prompt1},
                    {"role": "user",
                     "content": prompt2}
                ],
                max_completion_tokens=250
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"An error occurred: {e}")

        # client = OpenAI(
        #     base_url="https://router.huggingface.co/v1",
        #     api_key=os.getenv("HF_TOKEN"),
        # )
        #
        # completion = client.chat.completions.create(
        #     model="meta-llama/Llama-3.1-405B-Instruct:fireworks-ai",
        #     messages=[
        #         {
        #             "role": "user",
        #             "content": prompt
        #         }
        #     ],
        # )
        # return completion.choices[0].message
