import cx_Oracle
import os
import base64
from hashlib import sha1
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.core.config import settings

# Cấu hình JWT
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_HOURS = settings.JWT_REFRESH_TOKEN_EXPIRE_HOURS
# Cấu hình mã hóa password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_oracle_connection():
    try:
        connection = cx_Oracle.connect(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASSWORD,
            dsn=settings.ORACLE_DNS
        )
        return connection
    except cx_Oracle.Error as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {str(error)}"
        )


def authenticate_user(username: str, password: str):
    try:
        # Mã hóa password theo định dạng của hệ thống
        password = sha1(password.encode()).digest()
        password = base64.b64encode(password)
        password = password.decode('utf-8')

        connection = get_oracle_connection()
        cursor = connection.cursor()

        query = """
        SELECT decode(b.user_id,null,a.user_id,b.user_id) user_id,
               a.user_name,
               a.email,
               decode(b.is_role,null,case when a.user_id = 623 then 1 else decode(role_id,2,1,88,2,4) end,b.is_role) role,
               decode(a.chat_id,null,1291548626,a.chat_id) chat_id 
        FROM users a 
        LEFT JOIN (SELECT * FROM sale_group WHERE status=1) b ON a.user_id=b.user_id
        WHERE a.status=1 AND a.user_name = UPPER(:username) AND a.password = :password
        """

        cursor.execute(query, username=username.upper(), password=password)
        user_record = cursor.fetchone()

        if not user_record:
            return None

        # Tạo user object với dữ liệu từ DB
        user = {
            "user_id": user_record[0],
            "username": user_record[1],
            "email": user_record[2],
            "role": user_record[3],
            "chat_id": user_record[4]
        }
        print(user)

        return user

    except cx_Oracle.Error as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(error)}"
        )
    finally:
        try:
            cursor.close()
            connection.close()
        except:
            pass


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=REFRESH_TOKEN_EXPIRE_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        exp: int = payload.get("exp")

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Kiểm tra token đã hết hạn hay chưa
        if exp < datetime.utcnow().timestamp():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return username

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
