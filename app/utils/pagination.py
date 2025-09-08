from typing import Type, Any, List
from sqlalchemy.orm import Query
from fastapi import HTTPException
from sqlalchemy import asc, desc
import json

from app.schemas.sche_pagination import PaginatedResponse
from app.schemas.sche_role import RoleResponse
from app.schemas.sche_user import UserResponse


def parse_key_to_filters(model: Type[Any], options: str) -> List[Any]:
    if not options:
        return []
    try:
        conditions = json.loads(options)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid options format")

    filters = []
    for field, value in conditions.items():
        if hasattr(model, field):
            column = getattr(model, field)
            if isinstance(value, dict) and "value" in value and "operator" in value:
                if value["operator"] == "=":
                    filters.append(column == value["value"])
                elif value["operator"] == "like":
                    filters.append(column.like(f"%{value['value']}%"))
            else:
                filters.append(column == value)  # Mặc định dùng = cho exact match
        else:
            filters.append(getattr(model, 'name').like(f"%{value}%"))
    return filters


def apply_filters(query: Query, model: Type[Any], options: str) -> Query:
    for f in parse_key_to_filters(model, options):
        query = query.filter(f)
    return query


def apply_sorting(query: Query, model: Type[Any], sort_by: str, order: str) -> Query:
    if sort_by and not hasattr(model, sort_by):
        raise HTTPException(status_code=400, detail=f"Invalid sort_by: {sort_by}")
    if hasattr(model, sort_by):
        direction = desc if order == 'desc' else asc
        query = query.order_by(direction(getattr(model, sort_by)))
    return query


def apply_pagination(query: Query, page_no: int, page_size: int) -> List[Any]:
    return query.limit(page_size).offset(page_size * (page_no - 1)).all()


def paginate(model: Type[Any], query: Query, params: Any) -> PaginatedResponse:
    query = apply_filters(query, model, params.options)
    total = query.count()
    query = apply_sorting(query, model, params.sort_by, params.order)
    data = apply_pagination(query, params.page_no, params.page_size)

    result = [UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        status=user.status,
        roles=RoleResponse(id=user.role.id, name=user.role.name) if user.role else None
    ) for user in data]

    return PaginatedResponse(
        data=result,
        total=total,
        page_no=params.page_no,
        page_size=params.page_size
    )