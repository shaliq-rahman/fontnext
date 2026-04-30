import asyncio
import sys
from sqlalchemy import select
from app.db.database import async_session_maker
from app.db.models import User
from app.core.security import get_password_hash


async def create_user(email: str, password: str, is_staff: bool = True) -> None:
    async with async_session_maker() as db:
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalars().first():
            print(f"User {email} already exists")
            return

        user = User(
            email=email,
            password=get_password_hash(password),
            is_active=True,
            is_staff=is_staff,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"Created user id={user.id} email={user.email}")


if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "user@example.com"
    password = sys.argv[2] if len(sys.argv) > 2 else "string"
    asyncio.run(create_user(email, password))
