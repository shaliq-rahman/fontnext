from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from app.db.database import get_db
from app.db.models import Sale, Font, Customer, User
from app.schemas.sale import SaleCreate, SaleOut, SaleCountOut
from app.api.dependencies import get_current_user

router = APIRouter()

@router.get("/", response_model=List[SaleOut])
async def list_sales(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Sale))
    return result.scalars().all()

@router.post("/", response_model=SaleOut, status_code=status.HTTP_201_CREATED)
async def create_sale(sale: SaleCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Validate customer
    customer_result = await db.execute(select(Customer).where(Customer.id == sale.customer))
    if not customer_result.scalars().first():
        raise HTTPException(status_code=404, detail="Customer not found")
        
    # Validate font and get price
    font_result = await db.execute(select(Font).where(Font.id == sale.font))
    font = font_result.scalars().first()
    if not font:
        raise HTTPException(status_code=404, detail="Font not found")
        
    new_sale = Sale(
        customer_id=sale.customer,
        font_id=sale.font,
        quantity=sale.quantity,
        price_at_sale=font.price
    )
    db.add(new_sale)
    await db.commit()
    await db.refresh(new_sale)
    return new_sale

@router.get("/{sale_id}/", response_model=SaleOut)
async def get_sale(sale_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Sale).where(Sale.id == sale_id))
    sale = result.scalars().first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale

@router.get("/today/count/", response_model=SaleCountOut)
async def today_sales_count(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = datetime.now(timezone.utc).date()
    # Cast sale_date to date for counting
    stmt = select(func.count(Sale.id)).where(func.date(Sale.sale_date) == today)
    result = await db.execute(stmt)
    count = result.scalar() or 0
    return {"count": count}

@router.get("/total/count/", response_model=SaleCountOut)
async def total_sales_count(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(func.count(Sale.id))
    result = await db.execute(stmt)
    count = result.scalar() or 0
    return {"count": count}
