import math
from datetime import datetime, timedelta
from http import HTTPStatus

import pandas as pd
from fastapi import HTTPException
from sqlalchemy import BigInteger
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import aliased
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import cast
from sqlalchemy.sql import func

from app.core.config import TelegramConfig
from app.database.models import PhoneNumber, Provider, BookingHistory
from app.services.v1.telegram import TelegramBot
from app.utils.utils_token import exact_token, is_role_admin


async def get_booking_by_params(request, filter: str, telco: str, limit, offset, db: AsyncSession):
    role = exact_token(request)["role"]

    provider_alias = aliased(Provider)  # Tạo alias tránh xung đột
    # Truy vấn tổng số bản ghi phù hợp
    total_query = select(func.count()).select_from(PhoneNumber).where(
        PhoneNumber.status == "available", PhoneNumber.active == 1
    )

    # Nếu có `telco`, lọc theo nhà mạng
    if telco:
        total_query = total_query.join(provider_alias, PhoneNumber.provider_id == provider_alias.id).where(
            func.upper(provider_alias.name) == func.upper(telco))

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
        .order_by(
            cast(PhoneNumber.phone_number, BigInteger)
        )
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
                "provider_name": pn.provider.name if role == 1 else pn.provider.name.split("_")[0],
                "phone_number": pn.phone_number,
                "booked_until": pn.booked_until,
                "updated_at": pn.updated_at,
                "active": pn.active,
                "maintenance_fee": pn.maintenance_fee,
            }
            for pn in phone_numbers
        ]
    }


async def get_booking_phone_number_for_option(request, quantity, option, db, offset):
    role = exact_token(request)["role"]
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
        .order_by(
            cast(PhoneNumber.phone_number, BigInteger)
        )
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
                "provider_name": pn.provider.name if role == 1 else pn.provider.name.split("_")[0],
                "phone_number": pn.phone_number,
                "booked_until": pn.booked_until,
                "updated_at": pn.updated_at,
                "active": pn.active,
                "maintenance_fee": pn.maintenance_fee,
            }
            for pn in phone_numbers
        ]
    }


async def booking_random(type_number_id, provider_id, quantity_book, request, db: AsyncSession):
    username = exact_token(request)["user_name"]

    query = (
        select(PhoneNumber)
        .where(
            and_(
                PhoneNumber.status == "available",
                PhoneNumber.active == 1,
                PhoneNumber.provider_id == provider_id,
                PhoneNumber.type_id == type_number_id
            )
        )
        .order_by(cast(PhoneNumber.phone_number, BigInteger))
        .limit(quantity_book)
    )
    result = await db.execute(query)
    phone_numbers = result.scalars().all()
    id_phone_numbers = [pn.id for pn in phone_numbers]

    if len(id_phone_numbers) > 0:
        try:
            # Sử dụng nested transaction nếu session đã có transaction đang mở
            trans_context = db.begin_nested() if db.in_transaction() else db.begin()
            async with trans_context:
                booked_phone_numbers = []  # Danh sách số điện thoại đã đặt

                for id_phone_number in id_phone_numbers:
                    query_lock = (
                        select(PhoneNumber)
                        .where(
                            PhoneNumber.id == id_phone_number,
                            PhoneNumber.status == "available"
                        )
                        .with_for_update()  # Khóa số điện thoại để tránh đặt trùng
                    )
                    result_lock = await db.execute(query_lock)
                    phone_number = result_lock.scalar()

                    if not phone_number:
                        raise HTTPException(
                            detail=f"Phone number id {id_phone_number} not found or booked",
                            status_code=HTTPStatus.NOT_FOUND
                        )

                    # Thêm booking history
                    new_booking = BookingHistory(
                        user_name=username,
                        phone_number_id=id_phone_number,
                    )
                    db.add(new_booking)
                    booked_phone_numbers.append(phone_number.phone_number)  # Lưu số điện thoại đã đặt
            # Khi thoát khỏi khối async with, transaction sẽ tự commit (hoặc nested transaction sẽ commit SAVEPOINT)

            # Gửi thông báo Telegram sau khi transaction commit thành công
            bot = TelegramBot(token=TelegramConfig.get("TOKEN_TELEGRAM"))
            message = (
                f"Booking random số thành công:\nHọ tên người book: {username}\n"
                f"Số điện thoại: {', '.join(booked_phone_numbers)}"
            )
            bot.send_message(chat_id=TelegramConfig.get("CHAT_ID"), message=message)

        except SQLAlchemyError as e:
            # Nếu có lỗi, transaction (hoặc nested transaction) sẽ tự rollback
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    await db.commit()

    return [pn.phone_number for pn in phone_numbers]


async def add_booking_in_booking_history(bookingData, request, db: AsyncSession):
    token_data = exact_token(request)
    username = token_data["user_name"]
    chat_id = token_data["chat_id"]


    try:
        async with db.begin():  # Mở transaction toàn bộ danh sách
            booked_phone_numbers = []  # Danh sách số điện thoại đã đặt

            for id_phone_number in bookingData["id_phone_numbers"]:
                # Truy vấn và khóa số điện thoại để tránh đặt trùng
                query = (
                    select(PhoneNumber)
                    .where(PhoneNumber.id == id_phone_number, PhoneNumber.status == "available")
                    .with_for_update()  # khóa tránh tranh chấp
                )
                result = await db.execute(query)
                phone_number = result.scalar()

                if not phone_number:
                    raise HTTPException(
                        detail=f"Phone number id {id_phone_number} not found or booked",
                        status_code=HTTPStatus.NOT_FOUND
                    )

                # Thêm booking history
                new_booking = BookingHistory(
                    user_name=username,
                    phone_number_id=id_phone_number,
                )
                db.add(new_booking)
                booked_phone_numbers.append(phone_number.phone_number)  # Lưu số điện thoại

            # Lưu toàn bộ booking chỉ khi không có lỗi
            await db.commit()

            # Gửi thông báo Telegram với số điện thoại đã đặt
            bot = TelegramBot(token=TelegramConfig.get("TOKEN_TELEGRAM"))
            message = f"Booking thành công:\nHọ tên người book: {username}\nSố điện thoại: {', '.join(booked_phone_numbers)}"
            bot.send_message(chat_id=TelegramConfig.get("CHAT_ID"), message=message)
            bot.send_message(chat_id, message=message)
            return {
                "status": 200,
                "message": "Booking phone_number successfully"
            }

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))


async def release_phone_number(releaseData, request, db: AsyncSession):
    is_role_admin(request)
    username = exact_token(request)["user_name"]

    try:
        async with db.begin():  # Mở transaction toàn bộ danh sách
            issues = []
            successes = []

            for item in releaseData["data_releases"]:
                # Tìm phone number hợp lệ
                query = (
                    select(PhoneNumber)
                    .where(
                        and_(
                            PhoneNumber.phone_number == item["phone_number"],
                            PhoneNumber.active == 1,
                            PhoneNumber.status == "booked",
                            PhoneNumber.booked_until.isnot(None),
                            PhoneNumber.booked_until > datetime.utcnow(),
                        )
                    ).with_for_update()
                )
                result = await db.execute(query)
                phone_number = result.scalar_one_or_none()

                if phone_number:
                    # Cập nhật status trong bảng PhoneNumber
                    phone_number.status = "released"
                    db.add(phone_number)  # Đánh dấu cập nhật vào session

                    # Tìm booking history tương ứng
                    query_booking = (
                        select(BookingHistory)
                        .where(BookingHistory.phone_number_id == phone_number.id)
                        .order_by(BookingHistory.booked_at.desc())  # Lấy bản ghi mới nhất
                        .limit(1)
                    )
                    booking_result = await db.execute(query_booking)
                    booking_history = booking_result.scalar_one_or_none()

                    if booking_history:
                        booking_history.contract_code = item.get("contract_code", "")
                        booking_history.user_name_release = username
                        booking_history.released_at = datetime.utcnow()
                        # Đánh dấu cập nhật
                        db.add(booking_history)
                        successes.append(item)
                    else:
                        issues.append(item)
                else:
                    issues.append(item)

            await db.commit()  # Commit thay đổi vào DB
            if issues:
                df_issues = pd.DataFrame(issues)
                bot = TelegramBot(token=TelegramConfig.get("TOKEN_TELEGRAM"))
                message = f"Những số đã xảy ra vấn đề khi triển khai: \n"
                bot.send_message(chat_id=TelegramConfig.get("CHAT_ID"), message=message)
                bot.send_table(chat_id=TelegramConfig.get("CHAT_ID"), df=df_issues)
            return {"success": successes, "issues": issues}

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))
