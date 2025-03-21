import re
from datetime import date, datetime
from typing import Optional, Union

# Regex patterns
PHONE_REGEX = re.compile(r"^(0?)(3[2-9]|5[5689]|7[06789]|8[0-7689]|9[0-46-9])[0-9]{7}$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
EXCEL_REGEX = re.compile(r"^.*\.(xls|xlsx)$", re.IGNORECASE)

def is_valid_phone(phone: str) -> bool:
    return bool(PHONE_REGEX.match(phone))

def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email))

def is_excel_file(filename: str) -> bool:
    return bool(EXCEL_REGEX.match(filename))

def normalize_phone_number(phone: str) -> str:
    phone = re.sub(r"\D", "", phone)  # Loại bỏ ký tự không phải số

    if len(phone) == 9:
        return "0" + phone

    if phone.startswith("84"):
        return "0" + phone[2:]

    return phone


def get_valid_date(date_input: Optional[Union[str, date]]) -> date:
    """
    Validate a date input. Nếu giá trị truyền vào là một đối tượng date hoặc chuỗi theo định dạng 'YYYY-MM-DD',
    hàm sẽ trả về đối tượng date tương ứng. Nếu không hợp lệ hoặc không có giá trị, sẽ trả về date.today().
    """
    if date_input is None:
        return date.today()

    if isinstance(date_input, date):
        return date_input

    try:
        # Nếu date_input là chuỗi, thử chuyển đổi theo định dạng 'YYYY-MM-DD'
        return datetime.strptime(date_input, '%Y-%m-%d').date()
    except ValueError:
        # Nếu chuyển đổi thất bại, trả về ngày hiện tại
        return date.today()