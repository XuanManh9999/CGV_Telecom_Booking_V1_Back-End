import math
from fastapi import  HTTPException
from http import HTTPStatus
from sqlalchemy.orm import joinedload
from sqlalchemy.future import select
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import PhoneNumber, Provider, BookingHistory
from sqlalchemy.sql import func
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
async def get_booking_by_params(filter: str, telco: str, limit, offset, db: AsyncSession):
    provider_alias = aliased(Provider)  # Tạo alias tránh xung đột

    # Truy vấn tổng số bản ghi phù hợp
    total_query = select(func.count()).select_from(PhoneNumber).where(
        PhoneNumber.status == "available", PhoneNumber.active == 1
    )

    # Nếu có `telco`, lọc theo nhà mạng
    if telco:
        total_query = total_query.join(provider_alias, PhoneNumber.provider_id == provider_alias.id).where( func.upper(provider_alias.name)  == func.upper(telco) )

    # Nếu có `filter`, xử lý pattern LIKE
    if filter:
        pattern = filter.replace("*", "%") if "*" in filter else f"%{filter}%"
        total_query = total_query.where(PhoneNumber.phone_number.like(pattern))

    total_result = await db.execute(total_query)
    total_count = total_result.scalar()  # Lấy tổng số lượng

    # Tính tổng số trang
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 1

    # Truy vấn lấy danh sách phone number
    query = (
        select(PhoneNumber)
        .join(provider_alias, PhoneNumber.provider_id == provider_alias.id)  # JOIN bảng Provider
        .options(joinedload(PhoneNumber.provider), joinedload(PhoneNumber.type_number))  # Load quan hệ
        .where(PhoneNumber.status == "available", PhoneNumber.active == 1)
    )

    if telco:
        query = query.where(func.upper(provider_alias.name) == func.upper(telco))

    if filter:
        query = query.where(PhoneNumber.phone_number.like(pattern))

    query = query.limit(limit).offset(offset * limit)

    result = await db.execute(query)
    phone_numbers = result.scalars().all()

    return {
        "total_pages": total_pages,
        "phone_numbers": [
            {
                "id": pn.id,
                "status": pn.status,
                "created_at": pn.created_at,
                "type_name": pn.type_number.name if pn.type_number else None,
                "installation_fee": pn.installation_fee,
                "vanity_number_fee": pn.vanity_number_fee,
                "provider_name": pn.provider.name if pn.provider else None,
                "phone_number": pn.phone_number,
                "booked_until": pn.booked_until,
                "updated_at": pn.updated_at,
                "active": pn.active,
                "maintenance_fee": pn.maintenance_fee,
            }
            for pn in phone_numbers
        ]
    }

async def get_booking_phone_number_for_option(quantity, option, db, offset):
    provider_alias = aliased(Provider)  # Tạo alias để tránh xung đột

    # Truy vấn tổng số lượng bản ghi phù hợp
    total_query = select(func.count()).select_from(PhoneNumber).where(
        PhoneNumber.status == option, PhoneNumber.active == 1
    )
    total_result = await db.execute(total_query)
    total_count = total_result.scalar()  # Lấy tổng số lượng

    # Tính tổng số trang
    total_pages = math.ceil(total_count / quantity) if total_count > 0 else 1

    # Truy vấn lấy danh sách phone number
    query = (
        select(PhoneNumber)
        .join(provider_alias, PhoneNumber.provider_id == provider_alias.id)  # JOIN bảng Provider
        .options(joinedload(PhoneNumber.provider), joinedload(PhoneNumber.type_number))  # Load quan hệ
        .where(PhoneNumber.status == option, PhoneNumber.active == 1)  # Lọc số chưa được book
        .limit(quantity)
        .offset(offset * quantity)
    )

    result = await db.execute(query)
    phone_numbers = result.scalars().all()

    return {
        "total_pages": total_pages,
        "phone_numbers": [
            {
                "id": pn.id,
                "status": pn.status,
                "created_at": pn.created_at,
                "type_name": pn.type_number.name if pn.type_number else None,
                "installation_fee": pn.installation_fee,
                "vanity_number_fee": pn.vanity_number_fee,
                "provider_name": pn.provider.name if pn.provider else None,
                "phone_number": pn.phone_number,
                "booked_until": pn.booked_until,
                "updated_at": pn.updated_at,
                "active": pn.active,
                "maintenance_fee": pn.maintenance_fee,
            }
            for pn in phone_numbers
        ]
    }


async def add_booking_in_booking_history(bookingData, db: AsyncSession):
    try:
        async with db.begin():  # Mở transaction toàn bộ danh sách
            new_booking_histories = []

            for id_phone_number in bookingData["id_phone_numbers"]:
                #  Truy vấn và khóa số điện thoại để tránh đặt trùng
                query = (
                    select(PhoneNumber)
                    .where(PhoneNumber.id == id_phone_number, PhoneNumber.status == "available")
                    .with_for_update()  # khóa tránh tranh chấp
                )
                result = await db.execute(query)
                phone_number = result.scalar()

                if not phone_number:
                    raise HTTPException(
                        status_code=HTTPStatus.NOT_FOUND,
                        detail=f"Phone number id {id_phone_number} not found or booked"
                    )

                # Thêm booking history
                new_booking = BookingHistory(
                    user_name=bookingData["user_name"],
                    phone_number_id=id_phone_number,
                )
                db.add(new_booking)
                new_booking_histories.append(new_booking)

            # Lưu toàn bộ booking chỉ khi không có lỗi
            await db.commit()
            return {
                "status": 200,
                "message": "Booking phone_number successfully",
                "booking_histories": new_booking_histories,
            }

    except SQLAlchemyError as e:
        await db.rollback()  # Nếu có lỗi, rollback để không lưu bất kỳ số nào
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))
