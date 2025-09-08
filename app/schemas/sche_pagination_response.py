import logging
from abc import ABC, abstractmethod
from contextvars import ContextVar
from typing import Optional, Generic, Sequence, Type, TypeVar, Callable, Any, List

from boto3 import Session
from fastapi import HTTPException
from pydantic import BaseModel, conint
from sqlalchemy import asc, desc
from sqlalchemy.orm import Query
from sqlalchemy.sql import operators
from sqlalchemy.sql.elements import BinaryExpression

from app.schemas.sche_api_response import ResponseSchemaBase, MetadataSchema
from app.schemas.sche_user import UserClassification

T = TypeVar("T")
C = TypeVar("C")

logger = logging.getLogger()


class PaginationParams(BaseModel):
    page_size: Optional[conint(gt=0, lt=1001)] = 10
    page_no: Optional[conint(gt=0)] = 1
    sort_by: Optional[str] = 'id'
    order: Optional[str] = 'asc'
    keyword: Optional[str] = None


class PaginationCustomParams(BaseModel):
    page_size: Optional[conint(gt=0, lt=1001)] = 10
    page_no: Optional[conint(gt=0)] = 1
    sort_by: Optional[str] = 'id'
    order: Optional[str] = 'asc'
    keyword: Optional[str] = None
    options: Optional[str] = None  # "status:active&age=18&valid=true&name=abc"


class BasePage(ResponseSchemaBase, Generic[T], ABC):
    data: Sequence[T]

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    @abstractmethod
    def create(cls: Type[C], code: str, message: str, data: Sequence[T], metadata: MetadataSchema) -> C:
        pass  # pragma: no cover


class Page(BasePage[T], Generic[T]):
    metadata: MetadataSchema

    @classmethod
    def create(cls, code: str, message: str, data: Sequence[T], metadata: MetadataSchema) -> "Page[T]":
        return cls(
            code=code,
            message=message,
            data=data,
            metadata=metadata
        )


PageType: ContextVar[Type[BasePage]] = ContextVar("PageType", default=Page)


def paginate(model, query: Query, params: Optional[PaginationParams]) -> BasePage:
    code = '0'
    message = 'Success'

    try:
        total = query.count()

        if params.order:
            direction = desc if params.order == 'desc' else asc
            query = query.order_by(direction(getattr(model, params.sort_by)))

        data = query.limit(params.page_size).offset(params.page_size * (params.page_no - 1)).all()

        metadata = MetadataSchema(
            current_page=params.page_no,
            page_size=params.page_size,
            total_items=total
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return PageType.get().create(code, message, data, metadata)


def paginate_mapper(db, model, query: Query, params: Optional[PaginationParams],
                    mapper: Optional[Callable[[Session, Any], Any]] = None) -> BasePage:
    code = '0'
    message = 'Success'

    try:
        total = query.count()

        if params.order:
            direction = desc if params.order == 'desc' else asc
            query = query.order_by(direction(getattr(model, params.sort_by)))

        items = query.limit(params.page_size).offset(params.page_size * (params.page_no - 1)).all()

        # Ánh xạ sang schema nếu mapper được cung cấp
        data = [mapper(db, item) for item in items] if mapper else items

        metadata = MetadataSchema(
            current_page=params.page_no,
            page_size=params.page_size,
            total_items=total
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return PageType.get().create(code, message, data, metadata)


def parse_key_to_filters(model, options: str):
    filters = []
    if not options:
        return filters

    conditions = options.replace('&', '|').split('|')

    for condition in conditions:
        if ':' in condition:
            field, value = condition.split(':', 1)
        elif '=' in condition:
            field, value = condition.split('=', 1)
        else:
            continue

        if hasattr(model, field):
            column = getattr(model, field)
            # Nếu là boolean
            if value.lower() in ['true', 'false']:
                filters.append(column == (value.lower() == 'true'))
            else:
                filters.append(column.like(f"%{value}%"))
        elif hasattr(model, 'name'):
            # fallback nếu không có field đó
            filters.append(getattr(model, 'name').like(f"%{value}%"))

    return filters


def paginate_advanced(model, query: Query, params: PaginationCustomParams) -> BasePage:
    code = '0'
    message = 'Success'

    try:
        if params.options:
            filters = parse_key_to_filters(model, params.options)
            for f in filters:
                query = query.filter(f)

        total = query.count()

        if hasattr(model, params.sort_by):
            direction = desc if params.order == 'desc' else asc
            query = query.order_by(direction(getattr(model, params.sort_by)))

        data = query.limit(params.page_size).offset(params.page_size * (params.page_no - 1)).all()

        metadata = MetadataSchema(
            current_page=params.page_no,
            page_size=params.page_size,
            total_items=total
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return PageType.get().create(code, message, data, metadata)


def parse_key_to_filters_classify_email(model, options: str):
    filters = []
    if not options:
        return filters

    conditions = options.replace('&', '|').split('|')

    for condition in conditions:
        if ':' in condition:
            field, value = condition.split(':', 1)
        elif '=' in condition:
            field, value = condition.split('=', 1)
        else:
            continue

        if hasattr(model, field):
            column = getattr(model, field)
            if value.lower() in ['true', 'false']:
                filters.append(column == (value.lower() == 'true'))
            elif field == 'status':
                filters.append(column == value)
            else:
                filters.append(column.like(f"%{value}%"))
        elif hasattr(model, 'name'):
            filters.append(getattr(model, 'name').like(f"%{value}%"))

    return filters


def apply_in_memory_filters(data: List[UserClassification], filters: List[BinaryExpression]) -> List[
    UserClassification]:
    filtered_data = data
    for f in filters:
        field = f.left.key
        operator = f.operator
        value = f.right.value

        filtered_data = [
            item for item in filtered_data
            if apply_single_filter(item, field, operator, value)
        ]
    return filtered_data


def apply_single_filter(item: UserClassification, field: str, operator: Any, value: Any) -> bool:
    item_value = getattr(item, field, None)
    if item_value is None:
        return False

    if operator == operators.eq:
        return item_value == value
    elif operator == operators.like_op:
        return str(value).strip('%').lower() in str(item_value).lower()
    elif operator == operators.gt_op:
        return item_value > value
    elif operator == operators.lt_op:
        return item_value < value
    elif operator == operators.ge_op:
        return item_value >= value
    elif operator == operators.le_op:
        return item_value <= value
    return True
