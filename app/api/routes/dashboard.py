from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timezone
from app.db.database import get_db
from app.db.models import Sale, Font, Customer, User
from app.schemas.sale import DashboardSummaryOut, TrendingFontOut
from app.api.dependencies import get_current_user

router = APIRouter()

@router.get("/summary/", response_model=DashboardSummaryOut)
async def dashboard_summary(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = datetime.now(timezone.utc).date()
    
    today_sales_stmt = select(func.count(Sale.id)).where(func.date(Sale.sale_date) == today)
    total_sales_stmt = select(func.count(Sale.id))
    total_customers_stmt = select(func.count(Customer.id))
    total_fonts_stmt = select(func.count(Font.id))
    
    # Ideally these can be executed concurrently
    today_sales_count = (await db.execute(today_sales_stmt)).scalar() or 0
    total_sales_count = (await db.execute(total_sales_stmt)).scalar() or 0
    total_customers = (await db.execute(total_customers_stmt)).scalar() or 0
    total_fonts = (await db.execute(total_fonts_stmt)).scalar() or 0
    
    return {
        "today_sales_count": today_sales_count,
        "total_sales_count": total_sales_count,
        "total_customers": total_customers,
        "total_fonts": total_fonts
    }

@router.get("/trending-fonts/", response_model=List[TrendingFontOut])
async def trending_fonts(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Group sales by font_id, count items, and join with Font
    stmt = (
        select(Font, func.count(Sale.id).label("sales_count"))
        .join(Sale, Sale.font_id == Font.id)
        .group_by(Font.id)
        .order_by(desc("sales_count"))
        .limit(10) # Generally trending indicates top N, e.g. 10
    )
    result = await db.execute(stmt)
    
    trending = []
    for font, sales_count in result.all():
        data = font.__dict__.copy()
        data["sales_count"] = sales_count
        trending.append(data)
        
    return trending
