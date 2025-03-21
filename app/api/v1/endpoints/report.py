from datetime import date

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.services.v1 import handle_report
from app.utils.utils_regex import get_valid_date

router = APIRouter(
    prefix="/report",
    tags=["Report"]
)

# tham số nhận vào là date.now() tìm ra những số đã được người này book dựa vào giá trị truyền vào
# nếu trong tháng thì bắt đầu từ ngày mùng 1 -> thời điểm hiên tại
@router.get("/booking-by-user")
async def get_booking_by_user(request : Request, input_date : date | None = None, db: AsyncSession = Depends(get_db)):
    input_date = get_valid_date(input_date)
    return await handle_report.get_booking_by_user(input_date, request, db)


# nhận vào date.now trả về những thông tin sau các số được book, số chưa được book, so đã được triển khai dựa
# vào ngày
@router.get("/dartboard")
async def get_dartboard(year : int, month : int, day : int | None = None, db: AsyncSession = Depends(get_db)):
    return await handle_report.get_dartboard(year, month, day, db=db)

# extract role người người dùng để xem chi tiết nếu là 1 là admin thì đc xem 0 thì không cho xem
@router.get("/detail-report-by-role")
async def get_booking_report_by_role(request :  Request, input_date : date | None = None, db: AsyncSession = Depends(get_db)):
    input_date = get_valid_date(input_date)
    return await handle_report.get_booking_report_by_role(input_date, request, db)
