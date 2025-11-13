from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.schemas.auth import UserCreate
from app.core.security import get_password_hash

class CRUDUser:
    async def get_by_username(self, db: AsyncSession, username: str) -> User | None:
        result = await db.execute(select(User).filter(User.username == username))
        return result.scalars().first()

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def create(self, db: AsyncSession, user_in: UserCreate) -> User:
        db_user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

crud_user = CRUDUser()
