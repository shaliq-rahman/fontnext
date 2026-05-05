from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.db.models import Font, Sale, Customer, User
from app.schemas.font import FontCreate, FontUpdate, FontOut
from app.schemas.customer import CustomerOut
from app.schemas.common import success_response
from app.api.dependencies import get_current_user

router = APIRouter()

@router.get("/")
async def list_fonts(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Font))
    fonts = result.scalars().all()
    data = [FontOut.model_validate(f).model_dump(mode="json") for f in fonts]
    return success_response(data=data, message="Fonts retrieved successfully")

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_font(font: FontCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Font).where(Font.name == font.name))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Font with this name already exists")

    new_font = Font(**font.model_dump())
    db.add(new_font)
    await db.commit()
    await db.refresh(new_font)
    data = FontOut.model_validate(new_font).model_dump(mode="json")
    return success_response(data=data, message="Font created successfully")

@router.get("/{font_id}/")
async def get_font(font_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Font).where(Font.id == font_id))
    font = result.scalars().first()
    if not font:
        raise HTTPException(status_code=404, detail="Font not found")
    data = FontOut.model_validate(font).model_dump(mode="json")
    return success_response(data=data, message="Font retrieved successfully")

@router.put("/{font_id}/")
async def update_font(font_id: int, font_update: FontCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Font).where(Font.id == font_id))
    font = result.scalars().first()
    if not font:
        raise HTTPException(status_code=404, detail="Font not found")

    if font.name != font_update.name:
        dup_check = await db.execute(select(Font).where(Font.name == font_update.name))
        if dup_check.scalars().first():
            raise HTTPException(status_code=400, detail="Font with this name already exists")

    for key, value in font_update.model_dump().items():
        setattr(font, key, value)

    await db.commit()
    await db.refresh(font)
    data = FontOut.model_validate(font).model_dump(mode="json")
    return success_response(data=data, message="Font updated successfully")

@router.patch("/{font_id}/")
async def partial_update_font(font_id: int, font_update: FontUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Font).where(Font.id == font_id))
    font = result.scalars().first()
    if not font:
        raise HTTPException(status_code=404, detail="Font not found")

    update_data = font_update.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != font.name:
        dup_check = await db.execute(select(Font).where(Font.name == update_data["name"]))
        if dup_check.scalars().first():
            raise HTTPException(status_code=400, detail="Font with this name already exists")

    for key, value in update_data.items():
        setattr(font, key, value)

    await db.commit()
    await db.refresh(font)
    data = FontOut.model_validate(font).model_dump(mode="json")
    return success_response(data=data, message="Font updated successfully")

@router.delete("/{font_id}/")
async def delete_font(font_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Font).where(Font.id == font_id))
    font = result.scalars().first()
    if not font:
        raise HTTPException(status_code=404, detail="Font not found")
    await db.delete(font)
    await db.commit()
    return success_response(data=None, message="Font deleted successfully")

@router.get("/{font_id}/customers/")
async def get_font_customers(font_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = (
        select(Customer)
        .join(Sale, Sale.customer_id == Customer.id)
        .where(Sale.font_id == font_id)
        .distinct()
    )
    result = await db.execute(stmt)
    customers = result.scalars().all()
    data = [CustomerOut.model_validate(c).model_dump(mode="json") for c in customers]
    return success_response(data=data, message="Font customers retrieved successfully")
