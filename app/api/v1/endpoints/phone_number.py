from fastapi import APIRouter, File, UploadFile, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.phone_number import PhoneNumberResponse, PhoneNumberCreate, PhoneNumberUpdate
from app.schemas.liquidation import LiquidationRequest
from app.services.v1 import handle_phone_number

router = APIRouter(prefix="/phone", tags=["PhoneNumber"])

@router.get("/by-id")
async def get_phone_number_by_id(phone_id : int, db: AsyncSession = Depends(get_db)):
    return await handle_phone_number.get_phone_number_by_id(phone_id, db)

@router.get("/quantity-available")
async def get_phone_number_available_quantity(db: AsyncSession = Depends(get_db)):
    return await handle_phone_number.get_phone_number_available_quantity(db)

@router.get("/report-phone-number-by-time")
async def get_report_phone_number_by_time(year: int, month : int | None = None, day: int | None = None, db: AsyncSession = Depends(get_db)):
    if (month is not None and  month > 12) or (day is not  None and day > 31):
        raise HTTPException(status_code=400, detail="Invalid month or day")
    return await handle_phone_number.get_report_phone_number_by_time(year=year, month=month, day=day, db=db)

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

@router.delete("/liquidation")
async def liquidation_phone_number(
    request: Request,
    phone_numbers: LiquidationRequest,  # Đây là một instance của LiquidationRequest
    db: AsyncSession = Depends(get_db)
):
    return await handle_phone_number.liquidation_phone_number(request, phone_numbers.phone_numbers, db)



