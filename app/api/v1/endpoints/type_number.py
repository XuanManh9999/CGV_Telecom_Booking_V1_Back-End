from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.type_number import TypeNumberUpdate, TypeNumberCreate, TypeNumberResponse
from app.services.v1 import handle_type_number

router = APIRouter(prefix="/type_number")

@router.get("/alls", response_model=list[TypeNumberResponse])
async def get_type_numbers(db: AsyncSession = Depends(get_db)):
   return await handle_type_number.get_type_numbers(db=db)

@router.get("/by-id", response_model=TypeNumberResponse)
async def get_type_number_by_id(type_number_id : int,  db: AsyncSession = Depends(get_db)):
   return await handle_type_number.get_type_number_by_id(type_number_id=type_number_id, db=db)

@router.post("", response_model=TypeNumberCreate)
async def create_type_number(request : Request, type_number : TypeNumberCreate , db: AsyncSession = Depends(get_db)):
   return await handle_type_number.create_type_number(request, db=db, type_number_client=type_number)


@router.put("/type-number-by-id", response_model=TypeNumberUpdate)
async def update_type_number_by_id(request : Request, type_number_id : int, type_number : TypeNumberUpdate , db: AsyncSession = Depends(get_db)):
   return await handle_type_number.update_type_number_by_id(request, type_number_id, type_number_client=type_number, db=db)

@router.delete("/{type_number_id }")
async def delete_type_number(request : Request, id_type_number: int, db: AsyncSession = Depends(get_db)):
   return await handle_type_number.delete_type_number_by_id(request, type_number_id=id_type_number, db=db)