from typing import Optional, List

from sqlalchemy import exc, text
from sqlalchemy.future import select
from sqlalchemy.orm.session import Session

from app.db.models import Material
from app.external.aws_service import S3Uploader
from app.schemas.sche_material import DuplicateMaterialsRequest


def db_get_material_by_id(db: Session, material_id: int) -> Optional[Material]:
    return db.query(Material).filter(Material.id == material_id).first()


def get_material_by_question_id(db: Session, question_id: int) -> Optional[Material]:
    return db.query(Material).filter(Material.exam_question_id == question_id).first()


async def db_create_material(db: Session, new_material: Material) -> Optional[Material]:
    try:
        db.add(new_material)
        db.commit()
        db.refresh(new_material)
        return new_material
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise e


async def db_duplicate_material(db: Session, request: DuplicateMaterialsRequest):
    try:
        cursor = db.connection().connection.cursor()
        cursor.execute(
            "CALL duplicate_materials_and_embeddings(%s, %s, %s)",
            (request.material_ids,
             request.old_exam_question_id,
             request.new_exam_question_id)
        )
        db.commit()
        cursor.close()
        return True
    except Exception as e:
        db.rollback()
        raise e


async def db_delete_material_by_id(db: Session, material_id: int) -> int:
    try:
        material = db_get_material_by_id(db, material_id)
        file_key = material.file_key

        collection_name = f"materials_collection_question_{material.exam_question_id}"
        try:
            raw_sql = text(
                f"DELETE FROM public.langchain_pg_embedding "
                f"WHERE collection_id = (SELECT uuid FROM public.langchain_pg_collection WHERE name = :collection_name) "
                f"AND cmetadata->>'entity_id' = :entity_id;"
            )
            db.execute(raw_sql, {"collection_name": collection_name, "entity_id": str(material_id)})
            db.commit()
        except Exception as e:
            print(f"Error deleting PGVector chunks for Material {material_id}: {e}")
            raise

        count = db.query(Material).filter(Material.id == material_id).delete(synchronize_session=False)
        db.commit()

        if file_key:
            await S3Uploader.delete_s3_file(file_key)
        return count
    except Exception as e:
        db.rollback()
        raise e


def db_get_material_by_question_id(db: Session, question_id: int) -> Optional[List[Material]]:
    return db.query(Material).filter(Material.exam_question_id == question_id).all()


def db_get_material_ids_by_question_id(db: Session, question_id: int) -> List[int]:
    result = db.execute(
        select(Material.id).filter(Material.exam_question_id == question_id)
    )
    material_ids = result.scalars().all()
    return material_ids if material_ids else []
