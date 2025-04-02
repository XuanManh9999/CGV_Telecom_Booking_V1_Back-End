from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from app.database.models import Provider
from app.utils.utils_token import is_role_admin
from app.utils.utils_token import exact_token


async def get_providers(request, db: AsyncSession):
    role = exact_token(request)["role"]

    # Lấy danh sách nhà cung cấp đang hoạt động
    result = await db.execute(select(Provider).where(Provider.active == 1))
    providers = result.scalars().all()

    if role == 1:
        return providers
    else:
        return [{"id": provider.id, "name": provider.name.split('_')[0], "description" : provider.description} for provider in providers]


async def get_provider_by_id(provider_id, request, db: AsyncSession):
    role = exact_token(request)["role"]

    result = await db.execute(select(Provider).filter(Provider.id == provider_id, Provider.active == 1))
    provider = result.scalars().first()

    if not provider:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND.value, detail="Provider not found")

    if role == 1:
        return provider
    else:
        return {"id": provider.id, "name": provider.name.split("_")[0]}

async def create_provider(request, db: AsyncSession, provider):
        is_role_admin(request)
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


async def update_provider_by_id(request, provider_id, db: AsyncSession, providerUpdate):
    is_role_admin(request)
    if providerUpdate.name == "":
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="name cannot be empty")

    provider = await get_provider_by_id(provider_id, request, db)
    if provider is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Provider ID is not found")

    if providerUpdate.name is not None:
        provider.name = providerUpdate.name

    if providerUpdate.description is not None:
        provider.description = providerUpdate.description

    await db.commit()
    await db.refresh(provider)
    return provider

async def delete_provider_by_id(request, provider_id, db: AsyncSession):
    is_role_admin(request)
    provider = await get_provider_by_id(provider_id, request, db)
    if provider is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Provider ID is not found")
    provider.active = 0
    await db.commit()
    return {"message": "Provider deleted successfully"}

