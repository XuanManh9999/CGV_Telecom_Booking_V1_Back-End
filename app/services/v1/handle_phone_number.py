from datetime import datetime
from http import HTTPStatus
from io import BytesIO

import pandas as pd
from fastapi import UploadFile, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import and_, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func, extract

from app.database.models import Provider, TypeNumber, PhoneNumber, BookingHistory, BackupData
from app.services.v1.handle_provider import get_provider_by_id
from app.services.v1.handle_type_number import get_type_number_by_id
from app.utils import utils_regex
from app.utils.utils_token import is_role_admin
import calendar

async def get_phone_number_available_quantity(db):
    result = await db.execute(
        select(func.count(PhoneNumber.id)).where(
            PhoneNumber.status == "available",
            PhoneNumber.active == 1
        )
    )
    return {
        "quantity_available": result.scalar()
    }


async def get_report_phone_number_by_time(year, month, day,  db: AsyncSession):
    conditions = [extract('year', PhoneNumber.created_at) == year]

    if month is not None:
        conditions.append(extract('month', PhoneNumber.created_at) == month)

    if day is not None:
        conditions.append(extract('day', PhoneNumber.created_at) == day)


    # Xác định nhóm theo tháng hoặc ngày
    group_by_column = extract('month', PhoneNumber.created_at) if month is None else extract('day', PhoneNumber.created_at)

    query = select(
        group_by_column,
        func.count(PhoneNumber.id)
    ).where(*conditions).group_by(group_by_column)

    result = await db.execute(query)
    data = dict(result.all())

    if month is None:
        return {m: data.get(m, 0) for m in range(1, 13)}
    else:
        max_day = calendar.monthrange(year, month)[1]
        return {d: data.get(d, 0) for d in range(1, max_day + 1)}


async def process_excel_file(request, file: UploadFile, db: AsyncSession):
    is_role_admin(request)
    if not utils_regex.is_excel_file(file.filename):
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="File must be an Excel (.xlsx) file.")

    try:
        contents = await file.read()
        file.file.close()  # Đóng file sau khi đọc
        df = pd.read_excel(BytesIO(contents), engine="openpyxl")

        required_columns = ["Số điện thoại", "Nhà cung cấp", "Loại số", "Phí khởi tạo", "Phí duy trì", "Phí số đẹp"]
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Thiếu một số cột trong file Excel.")

        column_mapping = {
            "Số điện thoại": "phone",
            "Nhà cung cấp": "provider",
            "Loại số": "type_number",
            "Phí khởi tạo": "installation_fee",
            "Phí duy trì": "maintenance_fee",
            "Phí số đẹp": "vanity_number_fee"
        }

        df = df.rename(columns=column_mapping).dropna(subset=["phone"])

        valid_records = []
        invalid_rows = []
        for index, row in df.iterrows():
            error_messages = []
            phone = utils_regex.normalize_phone_number(str(row["phone"]).strip())
            if not utils_regex.is_valid_phone(phone):
                error_messages.append("Số điện thoại không hợp lệ.")

            for col in ["provider", "type_number", "installation_fee", "maintenance_fee", "vanity_number_fee"]:
                if pd.isna(row[col]) or str(row[col]).strip() == "":
                    error_messages.append(f"Cột {col} không được để trống.")

            try:
                row["installation_fee"] = float(row["installation_fee"])
                row["maintenance_fee"] = float(row["maintenance_fee"])
                row["vanity_number_fee"] = float(row["vanity_number_fee"])
                if row["installation_fee"] < 0 or row["maintenance_fee"] < 0 or row["vanity_number_fee"] < 0:
                    error_messages.append("Các loại phí phải là số dương.")
            except ValueError:
                error_messages.append("Các loại phí phải là số hợp lệ.")

            if error_messages:
                invalid_rows.append({"row": index + 2, "errors": error_messages})
            else:
                row["phone"] = phone
                valid_records.append(row.to_dict())

        if invalid_rows:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail={"message": "Invalid data", "errors": invalid_rows})

        update_config = await handle_add_phone_number(valid_records, db)

        return JSONResponse(content={
            "status": HTTPStatus.OK,
            "message": "Upload phone number done!",
            "update_error": update_config
        }, status_code=HTTPStatus.OK)

    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))

# hàm phụ của process_excel_file
async def handle_add_phone_number(data, db: AsyncSession):
    update_config = []

    async with db.begin():  # Bắt đầu transaction
        try:
            for phone_number in data:
                provider_query = await db.execute(
                    select(Provider).where(
                        func.upper(Provider.name) == func.upper(phone_number["provider"])
                    )
                )

                type_number_query = await db.execute(
                    select(TypeNumber).where(
                        func.upper(TypeNumber.name) == func.upper(phone_number["type_number"])
                    )
                )

                provider = provider_query.scalars().first()
                type_number = type_number_query.scalars().first()

                # Xử lý Provider
                if not provider:
                    new_provider = Provider(name=phone_number["provider"])
                    db.add(new_provider)
                    await db.flush()
                    await db.refresh(new_provider)
                    provider_id = new_provider.id
                else:
                    provider_id = provider.id

                # Xử lý TypeNumber
                if not type_number:
                    new_type_number = TypeNumber(name=phone_number["type_number"])
                    db.add(new_type_number)
                    await db.flush()
                    await db.refresh(new_type_number)
                    type_number_id = new_type_number.id
                else:
                    type_number_id = type_number.id

                # Kiểm tra số điện thoại đã tồn tại chưa
                result = await db.execute(
                    select(PhoneNumber).where(PhoneNumber.phone_number == phone_number["phone"], Provider.active == 1)
                )
                existing_phone = result.scalars().first()

                now = datetime.utcnow()
                if existing_phone:
                    last_updated = existing_phone.updated_at
                    if last_updated and (now.year == last_updated.year and now.month == last_updated.month):
                        update_config.append(existing_phone.phone_number)
                    else:
                        # Cập nhật nếu đã hơn 1 tháng
                        existing_phone.type_id = type_number_id
                        existing_phone.provider_id = provider_id
                        existing_phone.installation_fee = phone_number["installation_fee"]
                        existing_phone.maintenance_fee = phone_number["maintenance_fee"]
                        existing_phone.vanity_number_fee = phone_number["vanity_number_fee"]
                        existing_phone.updated_at = now
                else:
                    # Tạo mới nếu chưa có
                    new_phone_number = PhoneNumber(
                        phone_number=phone_number["phone"],
                        type_id=type_number_id,
                        provider_id=provider_id,
                        installation_fee=phone_number["installation_fee"],
                        maintenance_fee=phone_number["maintenance_fee"],
                        vanity_number_fee=phone_number["vanity_number_fee"],
                        updated_at=now
                    )
                    db.add(new_phone_number)

            await db.commit()  # Chỉ commit nếu không có lỗi

        except Exception as e:
            await db.rollback()  # Rollback nếu có lỗi
            raise HTTPException(status_code=500, detail=f"Error inserting phone numbers: {str(e)}")

    return update_config


async def get_phone_number_by_id (phone_number_id, db: AsyncSession):
    result = await db.execute(
        select(PhoneNumber, TypeNumber, Provider)
        .join(TypeNumber, PhoneNumber.type_id == TypeNumber.id)
        .join(Provider, PhoneNumber.provider_id == Provider.id)
        .filter( PhoneNumber.id == phone_number_id, PhoneNumber.active == 1)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Phone number not found or inactive")

    phone_number, type_number, provider = row
    return {
        "phone_number_id": phone_number.id,
        "provider_id": provider.id,
        "type_number_id": type_number.id,
        "status": phone_number.status,
        "phone_number": phone_number.phone_number,
        "installation_fee": phone_number.installation_fee,
        "maintenance_fee": phone_number.maintenance_fee,
        "vanity_number_fee": phone_number.vanity_number_fee,
        "booked_until": phone_number.booked_until
    }

async def create_phone_number(request, phone_number_client, db: AsyncSession):
    try:
        is_role_admin(request)
        await get_type_number_by_id(phone_number_client.type_id, db)
        await get_provider_by_id(phone_number_client.provider_id, db)

        # Chuẩn hóa số điện thoại
        phone_number_client.phone_number = utils_regex.normalize_phone_number(phone_number_client.phone_number)

        # Kiểm tra số điện thoại hợp lệ
        if not utils_regex.is_valid_phone(phone_number_client.phone_number):
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Phone Number is Invalid")

        # Kiểm tra số điện thoại đã tồn tại chưa
        result = await db.execute(select(PhoneNumber).where(PhoneNumber.phone_number == phone_number_client.phone_number))
        existing_phone = result.scalars().first()

        if existing_phone:
            # Lấy thời gian hiện tại và thời gian cập nhật cuối cùng
            now = datetime.utcnow()
            last_updated = existing_phone.updated_at

            if last_updated and (now.year == last_updated.year and now.month == last_updated.month):
                raise HTTPException(status_code=HTTPStatus.CONFLICT,
                                    detail="Số điện thoại không được cập nhật trong cùng một tháng")

            # Nếu hơn 1 tháng, cập nhật lại số điện thoại
            existing_phone.type_id = phone_number_client.type_id
            existing_phone.provider_id = phone_number_client.provider_id
            existing_phone.installation_fee = phone_number_client.installation_fee
            existing_phone.maintenance_fee = phone_number_client.maintenance_fee
            existing_phone.vanity_number_fee = phone_number_client.vanity_number_fee
            existing_phone.updated_at = now

            await db.commit()
            await db.refresh(existing_phone)
            return existing_phone

        # Nếu số điện thoại chưa tồn tại, tạo mới
        new_phone_number = PhoneNumber(
            phone_number=phone_number_client.phone_number,
            type_id=phone_number_client.type_id,
            provider_id=phone_number_client.provider_id,
            installation_fee=phone_number_client.installation_fee,
            maintenance_fee=phone_number_client.maintenance_fee,
            vanity_number_fee=phone_number_client.vanity_number_fee,
            updated_at=datetime.utcnow()
        )

        db.add(new_phone_number)
        await db.commit()
        await db.refresh(new_phone_number)
        return new_phone_number

    except HTTPException as http_exc:
        await db.rollback()
        raise http_exc  # Giữ nguyên lỗi HTTP để trả về đúng mã lỗi

    except SQLAlchemyError as db_exc:
        await db.rollback()
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Database error occurred")

    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(exc))


async def update_phone_number(request, phone_number_client, phone_id : int, db : AsyncSession):
    is_role_admin(request)
    await get_provider_by_id(phone_number_client.provider_id, db)
    await get_type_number_by_id(phone_number_client.type_id, db)


    result_frame = await db.execute(
        select(PhoneNumber).where(and_(
            PhoneNumber.id == phone_id,
            PhoneNumber.active == 1)
        ))
    result = result_frame.scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="Phone number not found or inactive")

    result.phone_number = phone_number_client.phone_number
    result.type_id = phone_number_client.type_id
    result.provider_id = phone_number_client.provider_id
    result.maintenance_fee = phone_number_client.maintenance_fee
    result.installation_fee = phone_number_client.installation_fee
    result.vanity_number_fee = phone_number_client.vanity_number_fee
    await db.commit()
    await db.refresh(result)
    return result


async def delete_phone_number(request, phone_id, db : AsyncSession):
    is_role_admin(request)
    result_frame = await db.execute(
        select(PhoneNumber).where(and_(
            PhoneNumber.id == phone_id,
            PhoneNumber.active == 1)
        ))
    result = result_frame.scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="Phone number not found or inactive")

    result.active = 0
    await db.commit()
    return {"message": "PhoneNumber deleted successfully"}


from sqlalchemy.exc import SQLAlchemyError

async def liquidation_phone_number(request, phone_numbers, db: AsyncSession):
    is_role_admin(request)
    phone_numbers_invalid = []
    successful_phone_numbers = []

    try:
        async with db.begin():  # Bắt đầu transaction
            for phone_number in phone_numbers:
                phone_number = utils_regex.normalize_phone_number(phone_number)
                if not utils_regex.is_valid_phone(phone_number):
                    phone_numbers_invalid.append(phone_number)
                    continue

                phone_number_query = await db.execute(
                    select(PhoneNumber).where(and_(
                        PhoneNumber.phone_number == phone_number,
                        PhoneNumber.active == 1
                    ))
                )
                phone_number_result = phone_number_query.scalars().first()

                if not phone_number_result:
                    phone_numbers_invalid.append(phone_number)
                    continue

                # Truy vấn TypeNumber
                type_number_query = await db.execute(
                    select(TypeNumber).where(TypeNumber.id == phone_number_result.type_id)
                )
                type_number_result = type_number_query.scalars().first()

                # Truy vấn Provider
                provider_query = await db.execute(
                    select(Provider).where(Provider.id == phone_number_result.provider_id)
                )
                provider_result = provider_query.scalars().first()

                #  Truy vấn BookingHistory
                booking_histories_query = await db.execute(
                    select(BookingHistory).where(BookingHistory.phone_number_id == phone_number_result.id)
                )
                booking_histories_result = booking_histories_query.scalars().all()

                for booking_history in booking_histories_result:
                    backup_data = BackupData(
                        phone_number=phone_number_result.phone_number,
                        type_number_name=type_number_result.name if type_number_result else None,
                        provider_name=provider_result.name if provider_result else None,
                        booked_at=booking_history.booked_at,
                        deployment_at=booking_history.released_at,
                        create_phone_number_at=phone_number_result.created_at,
                        name_book=booking_history.user_name,
                        name_release=booking_history.user_name_release,
                        installation_fee=phone_number_result.installation_fee,
                        maintenance_fee=phone_number_result.maintenance_fee,
                        vanity_number_fee=phone_number_result.vanity_number_fee,
                    )
                    db.add(backup_data)

                await db.execute(
                    delete(BookingHistory).where(BookingHistory.phone_number_id == phone_number_result.id)
                )

                await db.execute(
                    delete(PhoneNumber).where(PhoneNumber.id == phone_number_result.id)
                )

                successful_phone_numbers.append(phone_number)

        return {
            "message": "Liquidation process completed successfully",
            "invalid_phone_numbers": phone_numbers_invalid,
            "successful_phone_numbers": successful_phone_numbers
        }

    except SQLAlchemyError as e:
        await db.rollback()
        return {
            "message": "Transaction failed, all changes rolled back",
            "error": str(e),
            "invalid_phone_numbers": phone_numbers_invalid
        }

