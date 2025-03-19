from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from app.database.models import Provider


async def get_providers(db: AsyncSession):
    result = await db.execute(select(Provider).where(Provider.active == 1))
    providers = result.scalars().all()
    return providers


async def get_provider_by_id(provider_id, db: AsyncSession):
    result = await db.execute(select(Provider).filter(Provider.id == provider_id, Provider.active == 1))
    provider = result.scalars().first()
    if not provider:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND.value, detail="Provider not found")

    return provider


async def create_provider(db: AsyncSession, provider):
        if provider.name == "" or provider.description == "":
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="name/description cannot be empty")


        # check xem co name do chua
        result = await db.execute(select(Provider).where(func.upper(Provider.name)  == func.upper(provider.name), Provider.active == 1))
        is_check_provider_exits = result.scalars().first()

        if is_check_provider_exits:
            raise HTTPException(status_code=HTTPStatus.CONFLICT.value, detail="Provider already exists")
        new_provider = Provider(name=provider.name, description=provider.description)
        db.add(new_provider)
        await db.commit()
        await db.refresh(new_provider)
        return new_provider


async def update_provider_by_id(provider_id, db: AsyncSession, providerUpdate):
    if providerUpdate.name == "":
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="name cannot be empty")

    provider = await get_provider_by_id(provider_id, db)
    if provider is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Provider ID is not found")

    if providerUpdate.name is not None:
        provider.name = providerUpdate.name

    if providerUpdate.description is not None:
        provider.description = providerUpdate.description

    await db.commit()
    await db.refresh(provider)
    return provider

async def delete_provider_by_id(provider_id, db: AsyncSession):
    provider = await get_provider_by_id(provider_id, db)
    if provider is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Provider ID is not found")
    provider.active = 0
    await db.commit()
    return {"message": "Provider deleted successfully"}

