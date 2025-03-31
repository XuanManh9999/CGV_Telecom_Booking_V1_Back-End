from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, Float, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.db import Base

# class User(Base):
#     __tablename__ = "users"
#
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(255), unique=True, nullable=False)
#     description = Column(Text)
#
#     booking_userid = relationship("BookingHistory", back_populates="user")

class Provider(Base):
    __tablename__ = "providers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    active = Column(Integer, default=1)
    phone_numbers = relationship("PhoneNumber", back_populates="provider")


class TypeNumber(Base):
    __tablename__ = "type_numbers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    active = Column(Integer, default=1)
    phone_numbers = relationship("PhoneNumber", back_populates="type_number")
    booking_expiration = Column(BigInteger, default=259200, nullable=False)# 3 ngay
    def scalars(self):
        pass

class PhoneNumber(Base):
    __tablename__ = "phone_numbers"
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False)
    status = Column(String(20), default='available')  # available, booked, expired, released
    booked_until = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    type_id = Column(Integer, ForeignKey("type_numbers.id"), nullable=False)
    provider = relationship("Provider", back_populates="phone_numbers")
    type_number = relationship("TypeNumber", back_populates="phone_numbers")
    active=Column(Integer, default=1)
    installation_fee = Column(Float, default=None)
    maintenance_fee = Column(Float, default=None)
    vanity_number_fee = Column(Float, default=None)
    booking_histories = relationship("BookingHistory", back_populates="phone_number")



class BookingHistory(Base):
    __tablename__ = "booking_history"
    id = Column(Integer, primary_key=True, index=True)
    # user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_name = Column(String(255), nullable=False)
    phone_number_id = Column(Integer, ForeignKey("phone_numbers.id"), nullable=False)
    booked_at = Column(TIMESTAMP, default=func.now())
    released_at = Column(TIMESTAMP)
    active = Column(Integer, default=1)
    status = Column(String(20), default='active')  # active, released, expired
    contract_code = Column(String(255), default='')
    user_name_release = Column(String(255), default='')
    phone_number = relationship("PhoneNumber", back_populates="booking_histories")
    # user = relationship("User", back_populates="booking_histories")


class BackupData(Base):
    __tablename__ = "backup_data"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    phone_number = Column(String(20), nullable=False)
    type_number_name = Column(String(255), nullable=False)
    provider_name = Column(String(255), nullable=False)
    booked_at = Column(TIMESTAMP, nullable=True)  # Ngày đặt số
    deployment_at = Column(TIMESTAMP, nullable=True)  # Ngày triển khai
    create_phone_number_at = Column(TIMESTAMP, nullable=True)  # Ngày tạo số
    name_book = Column(String(255), nullable=False)
    name_release = Column(String(255), nullable=True)
    installation_fee = Column(Float, default=0)
    maintenance_fee = Column(Float, default=0)
    vanity_number_fee = Column(Float, default=0)
    created_at = Column(TIMESTAMP, default=func.now()) # Ngày thanh lý