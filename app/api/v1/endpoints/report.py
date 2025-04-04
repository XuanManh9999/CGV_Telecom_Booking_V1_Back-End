from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.services.v1 import handle_report

router = APIRouter(
    prefix="/report",
    tags=["Report"]
)


@router.get("/booking-by-current")
async def get_booking_by_user(request :  Request,
                              option : str,
                              limit: int = Query(20, ge=1, le=100, description="Number of records per page"),
                              offset: int = Query(0, ge=0, description="Offset for pagination"),
                              year : int | None = None,
                              month : int | None = None,
                              day : int | None = None,
                              db: AsyncSession = Depends(get_db)):
    return await handle_report.get_booking_report_by_user(request, option, year, month, day, limit, offset,  db)


@router.get("/dashboard")
async def get_dashboard(year : int, month : int, day : int | None = None, db: AsyncSession = Depends(get_db)):
    return await handle_report.get_dashboard(year, month, day, db=db)

# extract role người người dùng để xem chi tiết nếu là 1 là admin thì đc xem 0 thì không cho xem
@router.get("/detail-report-by-option")
async def get_booking_report_by_role(request : Request, option : str,
                                     limit: int = Query(20, ge=1, le=100, description="Number of records per page"),
                                     offset: int = Query(0, ge=0, description="Offset for pagination"),
                                     year : int | None = None,
                                     month : int | None = None,
                                     day : int | None = None,
                                     db: AsyncSession = Depends(get_db)):
    return await handle_report.get_booking_report_by_option(request, option, year, month, day, limit, offset, db)


