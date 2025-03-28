from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.services.v1 import  handle_provider

from app.schemas.provider import ProviderResponse, ProviderCreate, ProviderUpdate

router = APIRouter(prefix="/provider", tags=["Provider"])
@router.get("/all", response_model=list[ProviderResponse])
async def get_providers(request : Request, db: AsyncSession = Depends(get_db)):
    return await handle_provider.get_providers(request, db=db)

@router.get("/provider-by-id", response_model=ProviderResponse)
async def get_provider_by_id(provider_id  : int, request : Request, db: AsyncSession = Depends(get_db)):
    return await handle_provider.get_provider_by_id(provider_id=provider_id,request=request  , db=db)

@router.post("", response_model=ProviderCreate)
async def create_provider(request : Request, provider: ProviderCreate, db: AsyncSession = Depends(get_db)):
    return await handle_provider.create_provider(request, db=db, provider=provider)

@router.put("/provider-by-id", response_model=ProviderResponse)
async def update_provider_by_id(request : Request, provider_id: int, provider : ProviderUpdate, db: AsyncSession = Depends(get_db)):
    return await handle_provider.update_provider_by_id(request, provider_id=provider_id, db=db, providerUpdate=provider)

@router.delete("/{provider_id}")
async def delete_provider_by_id(request : Request, provider_id : int, db: AsyncSession = Depends(get_db)):
    return await handle_provider.delete_provider_by_id(request, provider_id=provider_id, db=db)
