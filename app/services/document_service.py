# import json
import os
from typing import List, Callable, Type

from fastapi import UploadFile, File, Depends
from langchain_community.vectorstores import PGVector, DistanceStrategy
from langchain_core.documents import Document as LangchainDocument
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import db_material
from app.db.database import get_db
from app.db.db_material import db_get_material_by_question_id, db_get_material_by_id
from app.db.models import Material
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.external.aws_service import S3Uploader
from app.schemas.sche_base import RequestT, ResponseT
from app.schemas.sche_material import MaterialContentResponse
from app.utils.file_util import read_document_pdf, read_document_docx

GOOGLE_API_KEYS = os.getenv("GOOGLE_API_KEYS", "").split(",")

class MaterialService:
    _embeddings_model = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

    @staticmethod
    def process_document_for_chunks(file_path: str) -> List[LangchainDocument]:
        """Processes a PDF document, reads content, splits into chunks, and prepares for storage."""
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == '.pdf':
            documents = read_document_pdf(file_path)
        elif file_extension in ['.docx', '.doc', '.rtf', '.odt']:
            documents = read_document_docx(file_path)
        else:
            raise CustomException(ErrorCode.EXAM_INVALID_FILE_FORMAT)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            length_function=len,
            add_start_index=True,
        )
        splits = text_splitter.split_documents(documents)
        return splits

    @staticmethod
    async def create_document_files(
            base_id: int,
            files: List[UploadFile] = File(...),
            request_class: Type[RequestT] = Material,
            response_class: Type[ResponseT] = MaterialContentResponse,
            db_create_func: Callable[[Session, RequestT], ResponseT] = db_material.db_create_material,
            db: Session = Depends(get_db),
            api_keys: List[str] = GOOGLE_API_KEYS
    ) -> List[ResponseT]:
        if not api_keys:
            raise CustomException(ErrorCode.COM_AI_GENERATE_FAILED)

        try:
            result = []
            original_api_key = os.getenv("GOOGLE_API_KEY")

            for file in files:
                temp_path = None
                try:
                    temp_prefix = "temp"
                    temp_filename = f"{file.filename}"

                    # 1. xu ly document
                    os.makedirs(temp_prefix, exist_ok=True)
                    temp_path = os.path.join(temp_prefix, temp_filename)
                    with open(temp_path, "wb") as f:
                        f.write(await file.read())

                    # 2. xu ly document content (tao chunks)
                    langchain_splits = MaterialService.process_document_for_chunks(temp_path)
                    file_key = await S3Uploader.upload_file_to_s3(file)

                    # 3. Luu thong tin document và contents vao DB
                    new_material = request_class(
                        title=file.filename,
                        file_key=file_key['file_key'],
                        exam_question_id=base_id
                    )
                    result_material = await db_create_func(db, new_material)
                    result.append(response_class.model_validate(result_material))

                    collection_name = f"materials_collection_question_{base_id}"
                    for split in langchain_splits:
                        split.metadata['entity_id'] = result_material.id

                    # 4. Chen chunks vao PGVector
                    for index, api_key in enumerate(api_keys):
                        try:
                            os.environ["GOOGLE_API_KEY"] = api_key

                            PGVector.from_documents(
                                documents=langchain_splits,
                                embedding=MaterialService._embeddings_model,
                                connection_string=settings.DATABASE_URL,
                                collection_name=collection_name,
                                distance_strategy=DistanceStrategy.COSINE,
                                pre_delete_collection=False
                            )
                            print(
                                f"Successfully ingested {len(langchain_splits)} chunks into PGVector collection '{collection_name}'.")
                            break

                        except Exception as e:
                            print(f"Error with API key {index + 1} for file {file.filename}: {e}")
                            if index == len(api_keys) - 1:
                                print(f"All API keys exhausted for file {file.filename}")

                                await db_material.db_delete_material_by_id(db, result_material.id)
                                if file_key:
                                    await S3Uploader.delete_s3_file(file_key["file_key"])

                                if original_api_key:
                                    os.environ["GOOGLE_API_KEY"] = original_api_key
                                else:
                                    os.environ.pop("GOOGLE_API_KEY", None)
                                raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
                            continue

                except CustomException as e:
                    raise
                except Exception as e:
                    print(f"Error processing file {file.filename}: {e}")
                    continue
                finally:
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)

            if original_api_key:
                os.environ["GOOGLE_API_KEY"] = original_api_key
            else:
                os.environ.pop("GOOGLE_API_KEY", None)

            return result

        except CustomException as e:
            if original_api_key:
                os.environ["GOOGLE_API_KEY"] = original_api_key
            else:
                os.environ.pop("GOOGLE_API_KEY", None)
            raise
        except Exception as e:
            if original_api_key:
                os.environ["GOOGLE_API_KEY"] = original_api_key
            else:
                os.environ.pop("GOOGLE_API_KEY", None)
            print(f"Error during document file creation: {e}")
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    async def delete_material(
            material_id: int,
            db_delete_func: Callable[[Session, int], int] = db_material.db_delete_material_by_id,
            db: Session = Depends(get_db),
    ) -> int:
        try:
            material_record = db_get_material_by_id(db, material_id)
            if not material_record:
                raise CustomException(ErrorCode.EXAM_DOCUMENT_NOT_EXISTED)

            count = await db_delete_func(db, material_id)
            return count
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_material_by_question_id(
            question_id: int,
            db: Session = Depends(get_db)
    ) -> List[MaterialContentResponse]:
        try:
            result = []
            materials = db_get_material_by_question_id(db, question_id)

            for item in materials:
                result.append(MaterialContentResponse.model_validate(item))

            return result
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
