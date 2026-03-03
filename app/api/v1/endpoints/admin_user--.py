from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from typing import List

from app.models.admin_user import AdminUser  # SQLAlchemy model from previous step
from app.schemas.admin_user import AdminUserCreate, AdminUserResponse
from app.db.session import get_db
from app.core.security import create_access_token, verify_password

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/users", tags=["Users"])

# --------------------
# LOGIN
# --------------------
@router.post("/login")
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AdminUser).where(AdminUser.loginID == form_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(form_data.password, user.hash_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login ID or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = await create_access_token(db, user.loginID, name="login", abilities=["user-login"])
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "personID": user.personID,
        "loginID": user.loginID,
        "usr_role": user.usr_role,
    }

# --------------------
# CREATE USER
# --------------------
@router.post("/", response_model=AdminUserResponse)
async def create_user(user: AdminUserCreate, db: AsyncSession = Depends(get_db)):
    hashed_password = pwd_context.hash(user.usr_password) if user.usr_password else None
    db_user = AdminUser(
        personID=user.personID,
        loginID=user.loginID,
        usr_role=user.usr_role or "faculty",
        usr_active=user.usr_active if user.usr_active is not None else True,
        usr_password=user.usr_password,
        hash_password=hashed_password,
        usr_otp=user.usr_otp,
        usr_otpExpire=user.usr_otpExpire,
        usr_resetToken=user.usr_resetToken,
        usr_resetTokenExpire=user.usr_resetTokenExpire,
        usr_lastLoginIP=user.usr_lastLoginIP,
        usr_lastLoingMAC=user.usr_lastLoingMAC,
        usr_loginLog=user.usr_loginLog,
        usr_lastLoginAt=user.usr_lastLoginAt,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# --------------------
# GET USER BY ID
# --------------------
@router.get("/{personID}", response_model=AdminUserResponse)
async def get_user(personID: int, db: AsyncSession = Depends(get_db)):
    stmt = select(AdminUser).where(AdminUser.personID == personID)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# --------------------
# UPDATE USER
# --------------------
@router.put("/{personID}", response_model=AdminUserResponse)
async def update_user(personID: int, user_update: AdminUserCreate, db: AsyncSession = Depends(get_db)):
    stmt = select(AdminUser).where(AdminUser.personID == personID)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update fields
    for field, value in user_update.dict(exclude_unset=True).items():
        if field == "usr_password" and value:
            setattr(user, "hash_password", pwd_context.hash(value))
            setattr(user, field, value)
        else:
            setattr(user, field, value)

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# --------------------
# DELETE USER
# --------------------
@router.delete("/{personID}")
async def delete_user(personID: int, db: AsyncSession = Depends(get_db)):
    stmt = select(AdminUser).where(AdminUser.personID == personID)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    return {"detail": "User deleted successfully"}

# --------------------
# RESET PASSWORD
# --------------------
@router.put("/{personID}/password")
async def reset_password(personID: int, password: str, db: AsyncSession = Depends(get_db)):
    stmt = select(AdminUser).where(AdminUser.personID == personID)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = pwd_context.hash(password)
    user.hash_password = hashed_password
    user.usr_password = password
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"detail": "Password reset successfully"}

# --------------------
# TOGGLE ACTIVE STATUS
# --------------------
@router.put("/{personID}/status")
async def toggle_status(personID: int, usr_active: bool, db: AsyncSession = Depends(get_db)):
    stmt = select(AdminUser).where(AdminUser.personID == personID)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.usr_active = usr_active
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"detail": f"Account {'activated' if usr_active else 'deactivated'} successfully"}

@router.post("/generate-password/{login_id}")
async def generate_password(login_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdminUser).where(AdminUser.loginID == login_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hash_password = pwd_context.hash('12345678')
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user