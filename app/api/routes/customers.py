from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, delete
from app.db.database import get_db
from app.db.models import Customer, Font, Sale, User
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerOut, CustomerDetailOut, AssignFontsRequest
from app.schemas.font import FontOut
from app.schemas.common import success_response
from app.api.dependencies import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

async def check_customer_duplicates(db: AsyncSession, email: str = None, phone: str = None, phone2: str = None, exclude_id: int = None):
    conditions = []
    if email:
        conditions.append(Customer.email == email)
    if phone:
        conditions.append(Customer.phone == phone)
    if phone2:
        conditions.append(Customer.phone2 == phone2)

    if not conditions:
        return

    stmt = select(Customer).where(or_(*conditions))
    if exclude_id:
        stmt = stmt.where(Customer.id != exclude_id)

    result = await db.execute(stmt)
    duplicates = result.scalars().all()
    for d in duplicates:
        if email and d.email == email:
            raise HTTPException(status_code=400, detail="Customer with this email already exists")
        if phone and d.phone == phone:
            raise HTTPException(status_code=400, detail="Customer with this phone already exists")
        if phone2 and d.phone2 == phone2:
            raise HTTPException(status_code=400, detail="Customer with this phone2 already exists")

async def _assign_fonts_internal(db: AsyncSession, customer_id: int, font_ids: List[int]):
    existing_sales_stmt = select(Sale.font_id).where(
        and_(Sale.customer_id == customer_id, Sale.font_id.in_(font_ids))
    )
    existing_sales_result = await db.execute(existing_sales_stmt)
    existing_font_ids = set(existing_sales_result.scalars().all())

    new_font_ids = set(font_ids) - existing_font_ids

    if not new_font_ids:
        return 0

    fonts_stmt = select(Font).where(Font.id.in_(new_font_ids))
    fonts_result = await db.execute(fonts_stmt)
    fonts = fonts_result.scalars().all()

    new_sales = []
    for font in fonts:
        new_sales.append(
            Sale(
                customer_id=customer_id,
                font_id=font.id,
                quantity=1,
                price_at_sale=font.price,
            )
        )

    if new_sales:
        db.add_all(new_sales)
        await db.commit()

    return len(new_sales)

async def _replace_fonts_internal(db: AsyncSession, customer_id: int, font_ids: List[int]):
    target_ids = set(font_ids)

    existing_stmt = select(Sale.font_id).where(Sale.customer_id == customer_id)
    existing_result = await db.execute(existing_stmt)
    existing_ids = set(existing_result.scalars().all())

    to_remove = existing_ids - target_ids
    to_add = target_ids - existing_ids

    if to_remove:
        await db.execute(
            delete(Sale).where(
                and_(Sale.customer_id == customer_id, Sale.font_id.in_(to_remove))
            )
        )

    added = 0
    if to_add:
        fonts_stmt = select(Font).where(Font.id.in_(to_add))
        fonts_result = await db.execute(fonts_stmt)
        fonts = fonts_result.scalars().all()
        new_sales = [
            Sale(
                customer_id=customer_id,
                font_id=font.id,
                quantity=1,
                price_at_sale=font.price,
            )
            for font in fonts
        ]
        if new_sales:
            db.add_all(new_sales)
            added = len(new_sales)

    if to_remove or to_add:
        await db.commit()

    return {"added": added, "removed": len(to_remove)}

@router.get("/")
async def list_customers(
    search: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    exclude_font_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Customer)

    if search:
        stmt = stmt.where(Customer.name.ilike(f"%{search}%"))
    if phone:
        stmt = stmt.where(or_(Customer.phone == phone, Customer.phone2 == phone))
    if email:
        stmt = stmt.where(Customer.email == email)
    if exclude_font_id:
        subq = select(Sale.customer_id).where(Sale.font_id == exclude_font_id)
        stmt = stmt.where(Customer.id.notin_(subq))

    result = await db.execute(stmt)
    customers = result.scalars().all()
    data = [CustomerOut.model_validate(c).model_dump(mode="json") for c in customers]
    return success_response(data=data, message="Customers retrieved successfully")

@router.get("/by-phone/")
async def get_customer_by_phone(
    phone: str = Query(..., description="Phone number to search for"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Customer).where(or_(Customer.phone == phone, Customer.phone2 == phone))
    result = await db.execute(stmt)
    customer = result.scalars().first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    fonts_stmt = select(Font).join(Sale, Sale.font_id == Font.id).where(Sale.customer_id == customer.id)
    fonts_result = await db.execute(fonts_stmt)

    response = CustomerDetailOut.model_validate(customer)
    response.fonts = fonts_result.scalars().all()
    return success_response(data=response.model_dump(mode="json"), message="Customer retrieved successfully")

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer: CustomerCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    await check_customer_duplicates(db, email=customer.email, phone=customer.phone, phone2=customer.phone2)

    new_customer = Customer(**customer.model_dump(exclude={"font_ids"}))
    db.add(new_customer)
    await db.commit()
    await db.refresh(new_customer)

    if customer.font_ids:
        await _assign_fonts_internal(db, new_customer.id, customer.font_ids)

    data = CustomerOut.model_validate(new_customer).model_dump(mode="json")
    return success_response(data=data, message="Customer created successfully")

@router.get("/{customer_id}/")
async def get_customer(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalars().first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    data = CustomerOut.model_validate(customer).model_dump(mode="json")
    return success_response(data=data, message="Customer retrieved successfully")

@router.get("/{customer_id}/fonts/")
async def get_customer_fonts(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(Font).join(Sale, Sale.font_id == Font.id).where(Sale.customer_id == customer_id)
    result = await db.execute(stmt)
    fonts = result.scalars().all()
    data = [FontOut.model_validate(f).model_dump(mode="json") for f in fonts]
    return success_response(data=data, message="Customer fonts retrieved successfully")

@router.patch("/{customer_id}/")
async def partial_update_customer(customer_id: int, customer_update: CustomerUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalars().first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    update_data = customer_update.model_dump(exclude_unset=True)
    await check_customer_duplicates(
        db,
        email=update_data.get("email"),
        phone=update_data.get("phone"),
        phone2=update_data.get("phone2"),
        exclude_id=customer_id,
    )

    for key, value in update_data.items():
        setattr(customer, key, value)

    await db.commit()
    await db.refresh(customer)
    data = CustomerOut.model_validate(customer).model_dump(mode="json")
    return success_response(data=data, message="Customer updated successfully")

@router.put("/{customer_id}/")
async def update_customer(customer_id: int, customer_update: CustomerCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalars().first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    await check_customer_duplicates(
        db,
        email=customer_update.email,
        phone=customer_update.phone,
        phone2=customer_update.phone2,
        exclude_id=customer_id,
    )

    for key, value in customer_update.model_dump(exclude={"font_ids"}).items():
        setattr(customer, key, value)

    await db.commit()
    await db.refresh(customer)

    if customer_update.font_ids is not None:
        await _replace_fonts_internal(db, customer_id, customer_update.font_ids)

    data = CustomerOut.model_validate(customer).model_dump(mode="json")
    return success_response(data=data, message="Customer updated successfully")

@router.delete("/{customer_id}/")
async def delete_customer(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalars().first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    await db.delete(customer)
    await db.commit()
    return success_response(data=None, message="Customer deleted successfully")

@router.post("/{customer_id}/assign-fonts/")
async def assign_fonts(customer_id: int, request: AssignFontsRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalars().first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    changes = await _replace_fonts_internal(db, customer_id, request.font_ids)

    if changes["added"] == 0 and changes["removed"] == 0:
        return success_response(data=None, message="Customer fonts already match the requested assignment")

    return success_response(
        data=None,
        message=f"Fonts updated: {changes['added']} added, {changes['removed']} removed",
    )
