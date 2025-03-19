import re

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