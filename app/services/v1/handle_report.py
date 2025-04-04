import math

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import PhoneNumber, Provider, BookingHistory, TypeNumber
from app.utils.utils_token import exact_token, is_role_admin
from sqlalchemy import select, func, extract, and_

async def get_dashboard(year, month, day, db: AsyncSession):
    # Điều kiện cho khoảng thời gian (cho booked_at)
    conditions_booked = [
        extract('year', BookingHistory.booked_at) == year,
        extract('month', BookingHistory.booked_at) == month,
    ]
    if day is not None:
        conditions_booked.append(extract('day', BookingHistory.booked_at) == day)

    # 1. Thống kê số đã được book (dựa vào booked_at)
    query_booked = (
        select(func.count(func.distinct(BookingHistory.phone_number_id)))
        .select_from(BookingHistory)
        .where(and_(*conditions_booked))
    )
    booked_result = await db.execute(query_booked)
    booked_count = booked_result.scalar() or 0

    # # 2. Thống kê số chưa được book trong khoảng thời gian truyền vào:
    # subquery = (
    #     select(BookingHistory.phone_number_id)
    #     .where(and_(*conditions_booked))
    #     .distinct()
    # )
    # query_not_booked = (
    #     select(func.count(PhoneNumber.id))
    #     .where(PhoneNumber.active == 1, PhoneNumber.status == "available")
    #     .where(~PhoneNumber.id.in_(subquery))
    # )
    # not_booked_result = await db.execute(query_not_booked)
    # not_booked_count = not_booked_result.scalar() or 0

    # 3. Thống kê số đã được triển khai trong khoảng thời gian (dựa vào released_at)
    conditions_deployed = [
        extract('year', BookingHistory.released_at) == year,
        extract('month', BookingHistory.released_at) == month,
    ]
    if day is not None:
        conditions_deployed.append(extract('day', BookingHistory.released_at) == day)

    query_deployed = (
        select(func.count(func.distinct(BookingHistory.phone_number_id)))
        .select_from(BookingHistory)
        .where(and_(*conditions_deployed))
    )
    deployed_result = await db.execute(query_deployed)
    deployed_count = deployed_result.scalar() or 0

    return {
        "booked": booked_count,
        # "not_booked": not_booked_count,
        "deployed": deployed_count,
    }


# get book theo người dùng
async def get_booking_report_by_user(
    request, option, year=None, month=None, day=None, limit=20, offset=0, db=None
):
    user_name = exact_token(request)["user_name"]

    # Chọn cột ngày dựa vào option
    date_column = None
    if option == "booked":
        date_column = BookingHistory.booked_at
    elif option == "released":
        date_column = BookingHistory.released_at

    date_filters = []
    if date_column:
        if year:
            date_filters.append(extract("year", date_column) == year)
        if month:
            date_filters.append(extract("month", date_column) == month)
        if day:
            date_filters.append(extract("day", date_column) == day)

    # Truy vấn đếm tổng số bản ghi
    count_query = select(func.count()).select_from(
        select(PhoneNumber)
        .join(Provider, PhoneNumber.provider_id == Provider.id)
        .join(TypeNumber, PhoneNumber.type_id == TypeNumber.id)
        .join(BookingHistory, and_(
            BookingHistory.user_name == user_name,
            BookingHistory.phone_number_id == PhoneNumber.id,
        ))
        .where(and_(
            PhoneNumber.active == 1,
            PhoneNumber.status == option,
            *date_filters
        ))
    )

    total_count = await db.scalar(count_query)
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 1

    # Truy vấn dữ liệu có phân trang
    query = (
        select(
            PhoneNumber.id,
            BookingHistory.user_name,
            PhoneNumber.status,
            PhoneNumber.created_at,
            PhoneNumber.installation_fee,
            PhoneNumber.vanity_number_fee,
            PhoneNumber.phone_number,
            PhoneNumber.booked_until,
            PhoneNumber.updated_at,
            PhoneNumber.active,
            PhoneNumber.maintenance_fee,
            Provider.name.label("provider_name"),
            TypeNumber.name.label("type_name")
        )
        .join(Provider, PhoneNumber.provider_id == Provider.id)
        .join(TypeNumber, PhoneNumber.type_id == TypeNumber.id)
        .join(BookingHistory, and_(
            BookingHistory.user_name == user_name,
            BookingHistory.phone_number_id == PhoneNumber.id,
        ))
        .where(and_(
            PhoneNumber.active == 1,
            PhoneNumber.status == option,
            *date_filters
        ))
        .distinct()
        .limit(limit)
        .offset(offset * limit)
    )

    result_frame = await db.execute(query)
    result = result_frame.mappings().all()

    return {
        "data": result,
        "total_pages": total_pages,
    }




async def get_booking_report_by_option (
    request, option, year=None, month=None, day=None, limit=20, offset=0, db=None
):
    is_role_admin(request)

    # Xác định cột ngày dựa trên option
    date_column = BookingHistory.booked_at if option == "booked" else BookingHistory.released_at

    # Áp dụng bộ lọc thời gian nếu có
    date_filters = []
    if date_column:
        if year:
            date_filters.append(extract("year", date_column) == year)
        if month:
            date_filters.append(extract("month", date_column) == month)
        if day:
            date_filters.append(extract("day", date_column) == day)

    # Subquery để lấy latest_booked_at cho từng số điện thoại
    latest_booking_subquery = (
        select(
            BookingHistory.phone_number_id,
            func.max(BookingHistory.booked_at).label("latest_booked_at")
        )
        .group_by(BookingHistory.phone_number_id)
        .subquery()
    )

    # Truy vấn đếm tổng số bản ghi
    count_query = select(func.count()).select_from(
        select(PhoneNumber)
        .join(Provider, PhoneNumber.provider_id == Provider.id)
        .join(TypeNumber, PhoneNumber.type_id == TypeNumber.id)
        .join(BookingHistory, PhoneNumber.id == BookingHistory.phone_number_id)
        .join(latest_booking_subquery, BookingHistory.phone_number_id == latest_booking_subquery.c.phone_number_id)
        .where(and_(
            PhoneNumber.active == 1,
            PhoneNumber.status == option,
            BookingHistory.booked_at == latest_booking_subquery.c.latest_booked_at,  # Áp dụng latest_booked_at
            *date_filters
        ))
    )

    total_count = await db.scalar(count_query)
    total_pages = max(1, math.ceil(total_count / limit))

    # Truy vấn dữ liệu có phân trang
    query = (
        select(
            BookingHistory.user_name,
            PhoneNumber.id,
            PhoneNumber.status,
            PhoneNumber.created_at,
            PhoneNumber.installation_fee,
            PhoneNumber.vanity_number_fee,
            PhoneNumber.phone_number,
            PhoneNumber.booked_until,
            PhoneNumber.updated_at,
            PhoneNumber.active,
            PhoneNumber.maintenance_fee,
            Provider.name.label("provider_name"),
            TypeNumber.name.label("type_name"),
            BookingHistory.contract_code,
            BookingHistory.user_name_release,
            BookingHistory.booked_at,
            BookingHistory.released_at
        )
        .join(Provider, PhoneNumber.provider_id == Provider.id)
        .join(TypeNumber, PhoneNumber.type_id == TypeNumber.id)
        .join(BookingHistory, PhoneNumber.id == BookingHistory.phone_number_id)
        .join(latest_booking_subquery, BookingHistory.phone_number_id == latest_booking_subquery.c.phone_number_id)
        .where(and_(
            PhoneNumber.active == 1,
            PhoneNumber.status == option,
            BookingHistory.booked_at == latest_booking_subquery.c.latest_booked_at,  # Áp dụng latest_booked_at
            *date_filters
        ))
        .distinct()
        .limit(limit)
        .offset(offset * limit)
    )

    result_frame = await db.execute(query)
    result = result_frame.mappings().all()

    return {
        "data": result,
        "total_pages": total_pages,
    }
