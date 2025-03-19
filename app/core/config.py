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

settings = Settings()

