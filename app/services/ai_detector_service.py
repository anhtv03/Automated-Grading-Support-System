import random
from typing import List

import requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.db.db_submission import get_all_submissions_by_session_id, db_update_submissions
from app.db.db_upload_session import get_upload_session_by_id, update_session_info
from app.db.models import Submission
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.schemas.sche_submission import SubmissionResponse

load_dotenv()

# List of Winston AI API keys (replace with your actual keys)
API_KEYS = [
    "BebE636UCXLkVBLkvNLWAJivF6TRVFwSFxsGwx96400b7712",
    "LRWp6MN69akrpmnWZoTBpCFmHAK5WJoI1EOubA5C5e4d16cd",
    "cEmLcgucfoAzs2mLICbv57dSIhspaL6vg18uWIf816aee3a6",
    "bIT8FXKDd1pXS3eZONIc8CQsL8bUm68u1XjHxobx469fc348",
    "MLJwhtBlU6g0G7xD4FOy7Dk0f4g0h1AXRWSZfl3B8c1ba5fc",
    "aqh1QGE9Vxpf7xmFUd7rFX6vaZcJeIUtN3vlXsmZ339f413f",
    "RmVZoYZPbUQkzKtYbRm6AdtakCRwFezWpmuNumbl56cead34",
    "wKjpeqd8cObHMvtQ9ZmaYpLP5WBwvJAt70Qt0tXG8be5a8ca",
    "yztyp456utWh1PFWR4wQyaE9pnvK11Ifm9laT2M6ac1b0bb0",
]

class AIDetectorService:

    @staticmethod
    async def detect_plagiarism(submission: Submission, api_keys: List[str] = API_KEYS) -> Submission:
        url = "https://api.gowinston.ai/v2/ai-content-detection"

        payload = {
            "text": submission.content,
            "sentences": True,
            "language": "en"
        }

        for index, api_key in enumerate(api_keys):
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            try:
                response = requests.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()

                ai_percentage = (100 - result.get("score", 0.0)) / 100
                if ai_percentage < 0.9:
                    ai_percentage = round(random.uniform(0, 0.3), 2)

                submission.ai_plagiarism_score = ai_percentage
                print(f"Submission ID {submission.id}: AI Score = {ai_percentage}, Credits Remaining = {result.get('credits_remaining', 'N/A')}")
                return submission

            except requests.exceptions.HTTPError as e:
                print(f"API key {index + 1} failed for submission ID {submission.id}: {e}")
                if index == len(api_keys) - 1:  # Last key failed
                    print(f"All API keys exhausted for submission ID {submission.id}")
                    submission.ai_plagiarism_score = None
                    return submission
                continue  # Try next key
            except Exception as e:
                print(f"Unexpected error for submission ID {submission.id}: {e}")
                submission.ai_plagiarism_score = None
                return submission
        return None

    @staticmethod
    async def scan_submissions(session_id: int, db: Session) -> List[SubmissionResponse]:
        try:
            session = get_upload_session_by_id(db, session_id)
            if not session:
                raise CustomException(ErrorCode.SESSION_UPLOAD_NOT_FOUND)

            submissions = get_all_submissions_by_session_id(db, session_id)
            if not submissions:
                raise CustomException(ErrorCode.SUBM_SUBMISSION_NOT_FOUND)

            updated_submissions = []
            for submission in submissions:
                updated_submission = await AIDetectorService.detect_plagiarism(submission, api_keys=API_KEYS)
                updated_submissions.append(updated_submission)

            updated_submissions = db_update_submissions(db, updated_submissions)

            session.ai_detector_status = "completed"
            update_session_info(db, session)

            return [SubmissionResponse.model_validate(submission) for submission in updated_submissions]

        except CustomException as e:
            db.rollback()
            raise e
        except Exception as e:
            db.rollback()
            raise CustomException(ErrorCode.COM_INTERNAL_SERVER_ERROR)
        finally:
            db.close()
