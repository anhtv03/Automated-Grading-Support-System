import uuid
from datetime import datetime

import boto3
from fastapi import UploadFile, File

from app.core.config import Settings
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode


class S3Uploader:
    @staticmethod
    async def upload_file_to_s3(file: UploadFile = File(...)) -> dict:
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=Settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Settings.AWS_SECRET_ACCESS_KEY,
                region_name=Settings.AWS_REGION
            )

            key_file = f"{uuid.uuid4()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            await file.seek(0)
            s3_client.upload_fileobj(
                file.file,
                Settings.AWS_BUCKET_NAME,
                key_file,
                ExtraArgs={'ContentType': file.content_type}
            )

            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': Settings.AWS_BUCKET_NAME, 'Key': key_file},
                ExpiresIn=300,
            )

            return {
                "file_key": key_file,
                "presigned_url": url
            }
        except CustomException as e:
            raise
        except Exception as e:
            print(f"Error during S3 upload: {e}")
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)


    async def get_presigned_url(file_key: str) -> str:
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=Settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Settings.AWS_SECRET_ACCESS_KEY,
                region_name=Settings.AWS_REGION
            )

            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': Settings.AWS_BUCKET_NAME, 'Key': file_key},
                ExpiresIn=300,
            )
            return url
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    async def delete_s3_file(file_key: str) -> None:
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=Settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Settings.AWS_SECRET_ACCESS_KEY,
                region_name=Settings.AWS_REGION
            )
            s3_client.delete_object(Bucket=Settings.AWS_BUCKET_NAME, Key=file_key)
            return None
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
