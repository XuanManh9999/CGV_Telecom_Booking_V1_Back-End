from fastapi import APIRouter, File, UploadFile, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.v1 import handle_phone_number
from app.schemas.phone_number import PhoneNumberResponse, PhoneNumberCreate
from app.database.db import get_db
router = APIRouter(prefix="/phone", tags=["PhoneNumber"])

@router.get("/by-id")
async def get_phone_number_by_id(phone_id : int, db: AsyncSession = Depends(get_db)):
    return await handle_phone_number.get_phone_number_by_id(phone_id, db)

@router.post("/upload-phone-number")
async def read_file(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    return await handle_phone_number.process_excel_file(file, db)


# , response_model=PhoneNumberResponse
@router.post("", response_model=PhoneNumberResponse)
async def create_phone_number(phone_number_client : PhoneNumberCreate,  db: AsyncSession = Depends(get_db)):
    return await handle_phone_number.create_phone_number(phone_number_client, db)






