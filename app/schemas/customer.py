from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.font import FontOut

class CustomerBase(BaseModel):
    name: str
    phone: str
    phone2: Optional[str] = None
    email: EmailStr
    address: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    phone2: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None

class CustomerOut(CustomerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CustomerDetailOut(CustomerOut):
    fonts: List[FontOut] = []

class AssignFontsRequest(BaseModel):
    font_ids: List[int]
