from pydantic import BaseModel
from datetime import datetime
from app.schemas.customer import CustomerOut
from app.schemas.font import FontOut

class SaleBase(BaseModel):
    quantity: int
    price_at_sale: float

class SaleCreate(BaseModel):
    customer: int # Corresponds to handoff "customer": 10
    font: int     # Corresponds to handoff "font": 1
    quantity: int

class SaleOut(SaleBase):
    id: int
    customer_id: int
    font_id: int
    sale_date: datetime
    # Nested fields can be added if needed, e.g. CustomerOut, FontOut

    class Config:
        from_attributes = True

class SaleCountOut(BaseModel):
    count: int

class DashboardSummaryOut(BaseModel):
    today_sales_count: int
    total_sales_count: int
    total_customers: int
    total_fonts: int

class TrendingFontOut(FontOut):
    sales_count: int
