from http import HTTPStatus
from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from app.database.models import TypeNumber


async def get_type_numbers (db: AsyncSession):
    result = await db.execute(select(TypeNumber).where(TypeNumber.active == 1))
    type_numbers = result.scalars().all()
    return type_numbers

async def get_type_number_by_id(type_number_id, db: AsyncSession):
    result = await db.execute(select(TypeNumber).where(
        TypeNumber.id == type_number_id, TypeNumber.active == 1))
    if result is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Type number not found")
    type_number = result.scalars().first()
    return type_number

async def create_type_number(db: AsyncSession, type_number_client):
    if  type_number_client.name == "":
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="name cannot be empty")

    result = await db.execute(select(TypeNumber).where(
        func.upper(TypeNumber.name)
              == func.upper(type_number_client.name), TypeNumber.active == 1))
    is_check_type_number_exit = result.scalars().first()
    if is_check_type_number_exit:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail="Type number already exists")

    booking_expiration = (
        type_number_client.booking_expiration
        if type_number_client.booking_expiration and type_number_client.booking_expiration > 0
        else 259200
    )

    new_type_number = TypeNumber(
        name=type_number_client.name,
        description=type_number_client.description,
        booking_expiration= booking_expiration,
    )
    db.add(new_type_number)
    await db.commit()
    await db.refresh(new_type_number)

    return new_type_number


async def update_type_number_by_id(type_number_id, type_number_client, db: AsyncSession):
    if type_number_client.name == "":
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="name cannot be empty")

    result = await get_type_number_by_id(type_number_id, db)
    if result is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Type number not found")

    booking_expiration = (
        type_number_client.booking_expiration
        if type_number_client.booking_expiration and type_number_client.booking_expiration > 0
        else 259200
    )

    result.name = type_number_client.name
    result.description = type_number_client.description
    result.booking_expiration = booking_expiration
    await db.commit()
    await db.refresh(result)
    return result

async def delete_type_number_by_id(type_number_id, db: AsyncSession):
    result = await get_type_number_by_id(type_number_id, db)
    if result is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Type number not found")
    result.active = 0
    await db.commit()
    return {"message": "type_number deleted successfully"}