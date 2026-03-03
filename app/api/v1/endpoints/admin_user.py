from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from typing import List

from app.models.admin_user import AdminUser  # SQLAlchemy model from previous step
from app.schemas.admin_user import AdminUserCreate, AdminUserResponse, AdminUserPasswordReset, AdminUserStatusUpdate, ChangePasswordRequest
from app.schemas.auth import Token
from app.db.session import get_db
from app.core.security import create_access_token, verify_password, get_password_hash

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
#router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/create-user", response_model=AdminUserResponse)
async def create_admin_user(
    payload: AdminUserCreate,
    db: AsyncSession = Depends(get_db),
):
    exists = await db.execute(
        select(AdminUser).where(AdminUser.loginID == payload.loginID)
    )
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Login ID already exists")

    admin = AdminUser(
        personID=payload.personID,
        loginID=payload.loginID,
        usr_role=payload.usr_role,
        hash_password=get_password_hash(payload.password),
    )

    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin
# --------------------
# Admin Auth Routes
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
    access_token = await create_access_token(db, form_data.username, name="login", abilities="['user-login']")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "personID": user.personID,
        "loginID": user.loginID,
        "usr_role": user.usr_role,
    }



@router.put("/{person_id}/status")
async def update_admin_status(
    person_id: int,
    payload: AdminUserStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AdminUser).where(AdminUser.personID == person_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Admin user not found")

    user.admin_usr_active = payload.admin_usr_active
    await db.commit()

    return {
        "message": "Admin status updated",
        "admin_usr_active": user.admin_usr_active,
    }

@router.put("/{person_id}/password")
async def reset_admin_password(
    person_id: int,
    payload: AdminUserPasswordReset,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AdminUser).where(AdminUser.personID == person_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Admin user not found")

    user.hash_password = get_password_hash(payload.password)
    await db.commit()

    return {"message": "Password updated successfully"}

@router.post("/generate-password/{login_id}", response_model=AdminUserResponse)
async def generate_default_password(
    login_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AdminUser).where(AdminUser.loginID == login_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hash_password = get_password_hash("12345678")
    await db.commit()
    await db.refresh(user)

    return user

@router.delete("/{person_id}")
async def delete_admin_user(
    person_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AdminUser).where(AdminUser.personID == person_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Admin user not found")

    await db.delete(user)
    await db.commit()

    return {"message": "Admin user deleted successfully"}

    
@router.put("/change-password/{login_id}")
async def change_password(
    login_id: str,
    request: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AdminUser).where(AdminUser.loginID == login_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hash_password = get_password_hash(request.new_password)
    db.add(user)
    await db.commit()

    return {"message": "Password updated successfully"}
