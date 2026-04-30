from fastapi import APIRouter
from app.api.routes import auth, fonts, customers, sales, dashboard

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(fonts.router, prefix="/fonts", tags=["fonts"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(sales.router, prefix="/sales", tags=["sales"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
