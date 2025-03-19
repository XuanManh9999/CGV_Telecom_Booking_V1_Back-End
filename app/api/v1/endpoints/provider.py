from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.services.v1 import  handle_provider

from app.schemas.provider import ProviderResponse, ProviderCreate, ProviderUpdate

router = APIRouter(prefix="/provider", tags=["Provider"])
@router.get("/all", response_model=list[ProviderResponse])
async def get_providers(db: AsyncSession = Depends(get_db)):
    return await handle_provider.get_providers(db=db)

@router.get("/provider-by-id", response_model=ProviderResponse)
async def get_provider_by_id(provider_id  : int, db: AsyncSession = Depends(get_db)):
    return await handle_provider.get_provider_by_id(provider_id=provider_id, db=db)

@router.post("", response_model=ProviderCreate)
async def create_provider(provider: ProviderCreate, db: AsyncSession = Depends(get_db)):
    return await handle_provider.create_provider(db=db, provider=provider)

@router.put("/provider-by-id", response_model=ProviderResponse)
async def update_provider_by_id(provider_id: int, provider : ProviderUpdate, db: AsyncSession = Depends(get_db)):
    return await handle_provider.update_provider_by_id(provider_id=provider_id, db=db, providerUpdate=provider)

@router.delete("/{provider_id}")
async def delete_provider_by_id(provider_id : int, db: AsyncSession = Depends(get_db)):
    return await handle_provider.delete_provider_by_id(provider_id=provider_id, db=db)
