from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import Token, UserLogin, UserOut, TokenRefresh, UserCreate
from app.schemas.common import success_response
from app.core.security import verify_password, create_access_token, create_refresh_token, get_password_hash
from app.api.dependencies import get_current_user
from app.core.config import settings
import jwt

router = APIRouter()

@router.post("/login/")
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalars().first()
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    data = {
        "access": access_token,
        "refresh": refresh_token,
        "user": {
            "id": user.id,
            "email": user.email,
        },
    }
    return success_response(data=data, message="Login successful")

@router.post("/refresh/")
async def refresh_token(request: TokenRefresh, db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(
            request.refresh, settings.SECRET_KEY, algorithms=["HS256"]
        )
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )

    access_token = create_access_token(subject=user.id)
    return success_response(data={"access": access_token}, message="Token refreshed successfully")

@router.get("/me/")
async def get_me(current_user: User = Depends(get_current_user)):
    data = UserOut.model_validate({"id": current_user.id, "email": current_user.email}).model_dump()
    return success_response(data=data, message="User retrieved successfully")

@router.post("/logout/")
async def logout():
    return success_response(data=None, message="Successfully logged out")

@router.post("/create-superadmin/")
async def create_superadmin(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalars().first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists.",
        )

    new_user = User(
        email=user_in.email,
        password=get_password_hash(user_in.password),
        is_staff=True,
        is_superuser=True,
        is_active=True,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    data = UserOut.model_validate({"id": new_user.id, "email": new_user.email}).model_dump()
    return success_response(data=data, message="Superadmin created successfully")
