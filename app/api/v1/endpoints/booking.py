import asyncio

from fastapi import APIRouter, Query, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.booking import BookingRequest
from app.schemas.release import ReleaseRequest
from app.services.v1 import handle_booking

router = APIRouter(
    prefix="/booking",
    tags=["Booking"]
)

@router.get("/booking-phone-number")
async def booking_phone_number(
    request : Request,
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
        return await asyncio.wait_for(handle_booking.get_booking_by_params(request, filter, telco, limit, offset, db), timeout=20.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timed out (processing took over 20 seconds)")

@router.get("/booking-phone-number-for-option")
async def booking_phone_number_for_option(
        request : Request,
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
        return await asyncio.wait_for(handle_booking.get_booking_phone_number_for_option(request, quantity, option, db, offset), timeout=20.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timed out (processing took over 20 seconds)")


@router.get("/booking-random-by-type-number-and-provider")
async def booking_random(type_number_id : int, provider_id : int, request: Request, quantity_book : int | int = 50, db: AsyncSession = Depends(get_db)):
    if quantity_book > 50:
        quantity_book = 50
    return await handle_booking.booking_random(type_number_id, provider_id, quantity_book, request, db)



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






