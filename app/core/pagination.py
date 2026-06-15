from math import ceil
from typing import Any, Generic, TypeVar
from sqlalchemy import or_


from fastapi import Query
from pydantic import BaseModel, Field
from sqlalchemy.orm.interfaces import LoaderOption
from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm.attributes import QueryableAttribute
from sqlalchemy.sql.elements import ColumnElement

from app.db.session import include_deleted_execution_options

T = TypeVar("T")

DEFAULT_PAGE = 1
DEFAULT_LIMIT = 20
MAX_LIMIT = 100


class PaginationParams:
    """Pagination parameters for list routes."""

    def __init__(
        self,
        page: int = Query(DEFAULT_PAGE, ge=1, description="1-based page number"),
        limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
        search: str | None = Query(
            None,
            min_length=1,
            max_length=100,
            description="Case-insensitive name/code search across the full dataset",
        ),
    ):
        self.page = page
        self.limit = limit
        self.search = search.strip() if search else None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int = Field(description="Total rows matching filters + search (not just this page)")
    page: int
    limit: int
    total_pages: int

    @classmethod
    def build(cls, items: list[T], total: int, page: int, limit: int) -> "PaginatedResponse[T]":
        total_pages = ceil(total / limit) if total else 0
        return cls(
            items=items,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )


def ilike_search(term: str, *columns: QueryableAttribute) -> ColumnElement[bool]:
    """
    Case-insensitive substring match on one or more columns.
    Escapes SQL wildcards so user input '100%' is literal.
    """
    escaped = (
        term.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
    pattern = f"%{escaped}%"
    return or_(*[col.ilike(pattern, escape="\\") for col in columns])


ModelT = TypeVar("ModelT")

def build_list_query(
    model: type[ModelT],
    *,
    load_options: Sequence[LoaderOption] = (),
    statuses: Sequence[Any] | None = None,
    status_column: QueryableAttribute[Any] | None = None,
    search: str | None = None,
    search_columns: Sequence[QueryableAttribute[Any]] = (),
    order_by: Sequence[ColumnElement[Any]] = (),
    extra_where: Sequence[ColumnElement[bool]] = (),
) -> Select[tuple[ModelT]]:
    query = select(model).options(*load_options)

    for clause in extra_where:
        query = query.where(clause)

    if statuses and status_column is not None:
        query = query.where(status_column.in_(statuses))

    if search and search_columns:
        query = query.where(ilike_search(search, *search_columns))

    if order_by:
        query = query.order_by(*order_by)

    return query


async def count_query(
    db: AsyncSession,
    query: Select[Any],
    *,
    include_deleted: bool = False,
) -> int:
    count_q = select(func.count()).select_from(query.subquery())
    result = await db.execute(
        count_q,
        execution_options=include_deleted_execution_options(include_deleted),
    )
    return result.scalar() or 0


async def fetch_paginated(
    db: AsyncSession,
    query: Select[tuple[ModelT]],
    *,
    include_deleted: bool = False,
    pagination: PaginationParams | None = None,
) -> list[ModelT]:
    if pagination:
        query = query.offset(pagination.offset).limit(pagination.limit)

    result = await db.execute(
        query,
        execution_options=include_deleted_execution_options(include_deleted),
    )
    return list(result.scalars().all())

def to_paginated_response(items: list[Any], total: int, pagination: PaginationParams | None = None) -> PaginatedResponse[Any]:
    if pagination:
        return PaginatedResponse.build(items, total, pagination.page, pagination.limit)
    
    return PaginatedResponse.build(items, total, 1, total or 1)