from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.db.models import Font, Sale, Customer, User
from app.schemas.font import FontCreate, FontUpdate, FontOut
from app.schemas.customer import CustomerOut
from app.api.dependencies import get_current_user

router = APIRouter()

@router.get("/", response_model=List[FontOut])
async def list_fonts(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Font))
    return result.scalars().all()

@router.post("/", response_model=FontOut, status_code=status.HTTP_201_CREATED)
async def create_font(font: FontCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check for duplicate
    result = await db.execute(select(Font).where(Font.name == font.name))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Font with this name already exists")
    
    new_font = Font(**font.model_dump())
    db.add(new_font)
    await db.commit()
    await db.refresh(new_font)
    return new_font

@router.get("/{font_id}/", response_model=FontOut)
async def get_font(font_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Font).where(Font.id == font_id))
    font = result.scalars().first()
    if not font:
        raise HTTPException(status_code=404, detail="Font not found")
    return font

@router.put("/{font_id}/", response_model=FontOut)
async def update_font(font_id: int, font_update: FontCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Font).where(Font.id == font_id))
    font = result.scalars().first()
    if not font:
        raise HTTPException(status_code=404, detail="Font not found")
    
    # Check duplicate on name change
    if font.name != font_update.name:
        dup_check = await db.execute(select(Font).where(Font.name == font_update.name))
        if dup_check.scalars().first():
            raise HTTPException(status_code=400, detail="Font with this name already exists")
    
    for key, value in font_update.model_dump().items():
        setattr(font, key, value)
    
    await db.commit()
    await db.refresh(font)
    return font

@router.patch("/{font_id}/", response_model=FontOut)
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
    return font

@router.delete("/{font_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_font(font_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Font).where(Font.id == font_id))
    font = result.scalars().first()
    if not font:
        raise HTTPException(status_code=404, detail="Font not found")
    await db.delete(font)
    await db.commit()
    return None

@router.get("/{font_id}/customers/", response_model=List[CustomerOut])
async def get_font_customers(font_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Customers who purchased a specific font
    stmt = (
        select(Customer)
        .join(Sale, Sale.customer_id == Customer.id)
        .where(Sale.font_id == font_id)
        .distinct()
    )
    result = await db.execute(stmt)
    return result.scalars().all()
