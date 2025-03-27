from fastapi import APIRouter, File, UploadFile, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.phone_number import PhoneNumberResponse, PhoneNumberCreate, PhoneNumberUpdate
from app.services.v1 import handle_phone_number

router = APIRouter(prefix="/phone", tags=["PhoneNumber"])

@router.get("/by-id")
async def get_phone_number_by_id(phone_id : int, db: AsyncSession = Depends(get_db)):
    return await handle_phone_number.get_phone_number_by_id(phone_id, db)

@router.get("/quantity-available")
async def get_phone_number_available_quantity(db: AsyncSession = Depends(get_db)):
    return await handle_phone_number.get_phone_number_available_quantity(db)


@router.post("/upload-phone-number")
async def read_file(request : Request, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    return await handle_phone_number.process_excel_file(request, file, db)

@router.post("", response_model=PhoneNumberResponse)
async def create_phone_number(request : Request, phone_number_client : PhoneNumberCreate,  db: AsyncSession = Depends(get_db)):
    return await handle_phone_number.create_phone_number(request, phone_number_client, db)

@router.put("", response_model=PhoneNumberResponse)
async def update_phone_number (request : Request, phone_number_client : PhoneNumberUpdate, phone_id: int, db: AsyncSession = Depends(get_db)):
    return await handle_phone_number.update_phone_number(request, phone_number_client, phone_id, db)

@router.delete("")
async def delete_phone_number(request : Request, phone_id : int, db: AsyncSession = Depends(get_db)):
    return await handle_phone_number.delete_phone_number(request, phone_id, db)




