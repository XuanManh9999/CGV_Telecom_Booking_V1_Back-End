# Cấu hình chung (env, settings)
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Cấu hình cơ bản
    PROJECT_NAME: str = os.getenv("APP_NAME")
    VERSION: str = os.getenv("APP_VERSION")

    # Cấu hình database
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # Cấu hình oracle
    ORACLE_CLIENT_PATH: str = os.getenv("ORACLE_CLIENT_PATH")
    ORACLE_USER: str = os.getenv("ORACLE_USER")
    ORACLE_PASSWORD: str = os.getenv("ORACLE_PASSWORD")
    ORACLE_DNS: str = os.getenv("ORACLE_DNS")
    # Cấu hình JWT
    ALGORITHM: str = os.getenv("JWT_ALGORITHM")
    SECRET_KEY: str = os.getenv("JWT_SECRET")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    JWT_REFRESH_TOKEN_EXPIRE_HOURS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_HOURS", 24))


TelegramConfig = {
    'TECH_TOKEN': os.getenv("TECH_TOKEN"),   #@CGVTechBot
    'SALE_TOKEN': os.getenv("SALE_TOKEN"),   #@CGVSaleBot
    'TECH_GROUP_ID': int(os.getenv("TECH_GROUP_ID")),  #Monitor_group
    'MAX_RETRIES': int(os.getenv("MAX_RETRIES")), #Số lần retry khi gửi tin nhắn
    'RETRY_DELAY': int(os.getenv("RETRY_DELAY")), #Thời gian delay giữa các lần retry
    'TOKEN_TELEGRAM': os.getenv("TOKEN_TELEGRAM"),
    'CHAT_ID': int(os.getenv("CHAT_ID")),
}



settings = Settings()

