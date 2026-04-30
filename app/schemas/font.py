from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FontBase(BaseModel):
    name: str
    price: float
    weight: float

class FontCreate(FontBase):
    pass

class FontUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    weight: Optional[float] = None

class FontOut(FontBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
