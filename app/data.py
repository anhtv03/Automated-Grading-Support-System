import os
import re

from sqlalchemy.orm import Session

from app.db.db_submission import get_all_submissions_by_session_id
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode


class Test:
    @staticmethod
    def getdata(session_id: int, db: Session):
        try:
            data = get_all_submissions_by_session_id(db, session_id)
            base_dir = 'd-original-submission'
            os.makedirs(base_dir, exist_ok=True)

            for submission in data:
                name = submission.name.strip() if submission.name else f"unnamed_{submission.id}"

                extension = '.docx'
                if name.endswith('.doc'):
                    extension = '.doc'

                name = name.replace(extension, '')  # Clean up the name for directory use
                content = submission.content or ""

                submission_dir = os.path.join(base_dir, name)
                os.makedirs(submission_dir, exist_ok=True)

                # Extract questions using regex
                # pattern = r'(Question \d+ \(\d+ points\):)(.*?)(?=Question \d+ \(\d+ points\):|$)'
                # pattern = r'(Question \d+:)(.*?)(?=Question \d+:|$)'
                pattern = r'(Question \d+(?: \(\d+ points\))?:)(.*?)(?=Question \d+(?: \(\d+ points\))?:|$)'
                matches = re.findall(pattern, content, re.DOTALL)

                if matches:
                    for title, question_content in matches:
                        # Clean filename: Question1(5points).txt -> Question15.txt
                        filename = title[:10].replace(' ', '') + '.txt'
                        file_path = os.path.join(submission_dir, filename)

                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(f"{title.strip()}\n{question_content.strip()}")
                else:
                    print(f"Error: No questions found in submission '{name}' (session_id: {session_id})")


        except CustomException:
            raise
        except Exception:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def generate_results(db: Session, session_id: int):
        try:
            # Lấy tất cả submissions từ session_id
            submissions = get_all_submissions_by_session_id(db, session_id)

            # Đọc prefix và post từ c-format-prompt
            cdata_dir = 'c-format-prompt'
            with open(os.path.join(cdata_dir, 'prefix_q4.txt'), 'r', encoding='utf-8') as f:
                prefix = f.read().strip()
            with open(os.path.join(cdata_dir, 'post.txt'), 'r', encoding='utf-8') as f:
                post = f.read().strip()

            base_dir = 'd-original-submission'
            output_base_dir = 'Eata'
            os.makedirs(output_base_dir, exist_ok=True)

            for submission in submissions:
                name = submission.name.strip() if submission.name else f"unnamed_{submission.id}"
                name = name.replace('.docx', '').replace('.doc', '')  # Clean name

                submission_dir = os.path.join(base_dir, name)
                if not os.path.exists(submission_dir):
                    continue  # Bỏ qua nếu folder không tồn tại

                output_submission_dir = os.path.join(output_base_dir, name)
                os.makedirs(output_submission_dir, exist_ok=True)

                # Duyệt các file QuestionX.txt trong folder
                for filename in os.listdir(submission_dir):
                    if filename.endswith('.txt') and filename.startswith('Question4'):
                        file_path = os.path.join(submission_dir, filename)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            question_content = f.read().strip()

                        # Ghép chuỗi
                        question_content_tabbed = '\n'.join('\t' + line for line in question_content.splitlines())
                        result_content = prefix + '\n' + question_content_tabbed + '\n\t' + post

                        # Lưu output, ví dụ: question1_result.txt
                        output_filename = 'result_' + filename.lower().replace('.txt', '')
                        output_path = os.path.join(output_submission_dir, output_filename)
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(result_content)

        except CustomException:
            raise
        except Exception:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def generate_final_results(db: Session, session_id: int):
        try:
            submissions = get_all_submissions_by_session_id(db, session_id)

            cdata_dir = 'c-format-prompt'
            with open(os.path.join(cdata_dir, 'final.txt'), 'r', encoding='utf-8') as f:
                final_prefix = f.read().strip()

            output_base_dir = 'Eata'

            for submission in submissions:
                name = submission.name.strip() if submission.name else f"unnamed_{submission.id}"
                name = name.replace('.docx', '').replace('.doc', '')

                output_submission_dir = os.path.join(output_base_dir, name)
                if not os.path.exists(output_submission_dir):
                    continue

                for filename in os.listdir(output_submission_dir):
                    if filename.startswith('result_question'):
                        file_path = os.path.join(output_submission_dir, filename)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            result_content = f.read().strip()

                        final_content = result_content + '\n<|im_start|>assistant' + '\n' + "+=====" + '\n<|im_end|>'

                        output_path = os.path.join(output_submission_dir, 'final_' + filename)
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(final_content)

        except CustomException:
            raise
        except Exception:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)