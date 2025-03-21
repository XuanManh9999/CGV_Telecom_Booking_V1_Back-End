from http import HTTPStatus
from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_
from sqlalchemy.sql import func, extract

from app.database.models import PhoneNumber, Provider, BookingHistory, TypeNumber
from app.utils.utils_token import exact_token


async def get_dartboard(year, month, day, db: AsyncSession):
    conditions = [
        PhoneNumber.active == 1,
        extract('year', PhoneNumber.created_at) == year,
        extract('month', PhoneNumber.created_at) == month,
    ]

    # Nếu day không phải None, thêm điều kiện lọc theo ngày
    if day is not None:
        conditions.append(extract('day', PhoneNumber.created_at) == day)

    query = (
        select(PhoneNumber.status, func.count(PhoneNumber.id))
        .where(and_(*conditions))
        .group_by(PhoneNumber.status)
    )

    result = await db.execute(query)
    status_counts = result.all()  # Lấy tất cả kết quả

    return {status: count for status, count in status_counts} # Trả về dạng dict

async def get_booking_by_user(report_request, request, db : AsyncSession):
    extact = exact_token(request)
    return {
        "year": report_request.year,
        "month": report_request.month,
        "day": report_request.day,
        "user": extact
    }

async def get_booking_report_by_role(report_request, request, db : AsyncSession):
    return None