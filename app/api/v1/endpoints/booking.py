from fastapi import APIRouter, Query, Depends, HTTPException, Request
from app.database.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.v1 import handle_booking
from app.schemas.booking import BookingRequest
from app.schemas.release import ReleaseRequest

import asyncio
router = APIRouter(
    prefix="/booking",
    tags=["Booking"]
)

@router.get("/booking-phone-number")
async def booking_phone_number(
    filter: str = Query(None, description="Filter for phone numbers"),
    telco: str = Query(None, description="Telco provider"),
    limit: int = Query(20, ge=1, le=100, description="Number of records per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    try:
        if limit > 100:
            limit = 100
        if offset < 0:
            offset = 0
        return await asyncio.wait_for(handle_booking.get_booking_by_params(filter, telco, limit, offset, db), timeout=20.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timed out (processing took over 20 seconds)")

@router.get("/booking-phone-number-for-option")
async def booking_phone_number_for_option(
        quantity : int = Query(50, ge=1, le=100, description="Number of records per page"),
        option : str = Query("available", description="Available options"),
        db: AsyncSession = Depends(get_db),
        offset: int = Query(0, ge=0, description="Offset for pagination")
):
    try:
        if quantity > 100:
            quantity = 100
        if offset < 0:
            offset = 0
        return await asyncio.wait_for(handle_booking.get_booking_phone_number_for_option(quantity, option, db, offset), timeout=20.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timed out (processing took over 20 seconds)")


@router.post("")
async def booking(booking : BookingRequest, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        if len(booking.dict()['id_phone_numbers']) <= 0:
            raise HTTPException(status_code=404, detail="No phone numbers available")
        return await asyncio.wait_for(handle_booking.add_booking_in_booking_history(booking.dict(), request, db), timeout=10)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timed out (processing took over 10 seconds)")



@router.post("/release-phone-number")
async def release_phone_number(release : ReleaseRequest, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        if len(release.dict()['data_releases']) <= 0:
            raise HTTPException(status_code=404, detail="No phone numbers")
        return await asyncio.wait_for(handle_booking.release_phone_number(release.dict(), request, db), timeout=10)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timed out (processing took over 10 seconds)")






