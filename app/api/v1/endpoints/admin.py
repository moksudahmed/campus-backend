from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.db.session import get_db
from app.models.student_record import StudentRecord
from app.schemas.student_record import StudentRecordSchema, AllStudentRecordSchema
import os
from fastapi.responses import FileResponse
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.security import create_access_token, verify_password
from app.core.security import generate_reset_token
#from app.utils.email_utils import send_password_reset_email
from app.schemas.auth import Token, UserCreate, UserResponse, StatusUpdate, ResetPasswordRequest, StandardResponse, ResetEmailRequest
from app.models.user import User as UserModel
from app.db.session import get_db
from app.core.security import get_password_hash
import bcrypt
from typing import List
from fastapi.responses import HTMLResponse, JSONResponse
from app.services.PasswordResetService import PasswordResetService
from datetime import datetime, timedelta
from app.utils.email_service import send_account_created_email
import secrets
import string


def generate_random_password(length: int = 10) -> str:
    """
    Generate a secure random password
    """
    characters = string.ascii_letters + string.digits + "!@#$%&*?"
    return ''.join(secrets.choice(characters) for _ in range(length))

router = APIRouter()
PHOTO_DIRECTORY = "C:/xampp/htdocs/muerp/photograph/"

# --------------------
# Helper: Password hashing
# --------------------
"""def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password.decode("utf-8")"""


# --------------------
# Auth Routes
# --------------------
@router.get("/batch-register", response_model=List[StudentRecordSchema])
async def batch_register(db: AsyncSession = Depends(get_db)):

    # Fetch distinct students
    stmt = (
        select(StudentRecord)
        .where(StudentRecord.stu_academicYear > 2018)
        .distinct(StudentRecord.student_id)
    )

    result = await db.execute(stmt)
    students = result.scalars().all()

    if not students:
        raise HTTPException(status_code=404, detail="No student records found")

    # Hash default password once (performance)
    default_hashed_password = get_password_hash("12345678")

    # Create user for each student
    for stu in students:

        # Skip if user already exists
        existing_user = await db.execute(
            select(UserModel).where(UserModel.student_id == stu.student_id)
        )
        if existing_user.scalar_one_or_none():
            continue   # User already exists, skip

        new_user = UserModel(
            student_id=stu.student_id,
            login_id=stu.per_email,  # Assuming per_email exists
            hash_password = default_hashed_password,
            is_active=True,
        )

        db.add(new_user)

    # Commit once for performance
    await db.commit()

    return students

@router.post("/create-user", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new user account and send login credentials via email
    """

    # 1️⃣ Check duplicate user
    existing = await db.execute(
        select(UserModel).where(UserModel.login_id == user.login_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already exists")

    # 2️⃣ Hash password
    # Generate random password
    plain_password = generate_random_password()
    
    # Hash it
    hashed_password = get_password_hash(plain_password)
    #hashed_password = get_password_hash(user.password)
    

    db_user = UserModel(
        student_id=user.student_id,
        login_id=user.login_id,
        hash_password=hashed_password,
        is_active=True
    )

    db.add(db_user)

    try:
        # 3️⃣ Save user first
        await db.commit()
        await db.refresh(db_user)

        # 4️⃣ Send welcome email
        await send_account_created_email(
            to_email=user.login_id,
            student_id=user.student_id,
            login_id=user.login_id,
            plain_password=plain_password
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"User created but email failed: {str(e)}"
        )

    return db_user

@router.post("/create-user2", response_model=UserResponse)
async def create_user2(user: UserCreate, db: AsyncSession = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    db_user = UserModel(
        student_id=user.student_id,
        login_id=user.login_id,  # Assuming per_email exists
        hash_password = hashed_password,
        is_active=True
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
  
@router.post("/reset-password", response_model=StandardResponse)
async def reset_password(request: ResetPasswordRequest):    
    print("HEllo WOrld from POST")

@router.get("/students2", tags=["System"])
async def students():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@router.get("/students", response_model=List[StudentRecordSchema])
async def read_students(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    stmt = select(StudentRecord).offset(skip)
    result = await db.execute(stmt)
    results = result.scalars().all()
    return results

# ✅ Return a single student
@router.get("/students/{student_id}", response_model=StudentRecordSchema)
async def read_student(student_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(StudentRecord).where(StudentRecord.student_id == student_id)
    result = await db.execute(stmt)
    student = result.scalars().first()  # ✅ .first() instead of .all()
    
    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )
    return student  # ✅ return single object, not list

#DEFAULT_PHOTO = "G:/React App/MuErp/mu_erp_backend/default-avatar.jpg"   
#PHOTO_DIRECTORY = "static/photos"
DEFAULT_PHOTO = "static/photos/default-avatar.jpg"


@router.get("/student-photo/{student_id}")
async def get_student_photo(student_id: str):
    """
    Serve a student's photo by their student_id.
    Returns a default photo if the student's photo is not found.
    Example: GET /api/v1/student-photo/111-118-001
    """
    filename = f"{student_id}.jpg"
    filepath = os.path.join(PHOTO_DIRECTORY, filename)

    # Use default photo if student photo does not exist
    if not os.path.exists(filepath):
        filepath = DEFAULT_PHOTO
    
    # Return the image as a FileResponse
    return FileResponse(filepath, media_type="image/jpeg")


@router.get("/student-users/{student_id}", response_model=UserResponse)
async def read_student(student_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(StudentRecord).where(StudentRecord.student_id == student_id)
    result = await db.execute(stmt)
    student = result.scalars().first()  # ✅ .first() instead of .all()
    
    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )
    return student  # ✅ return single object, not list


@router.get("/student-users-account/{student_id}", response_model=UserResponse)
async def get_student_account(student_id: str, db: AsyncSession = Depends(get_db)):
    
    stmt = select(UserModel).where(UserModel.student_id == student_id)
    result = await db.execute(stmt)
    user = result.scalars().first()  # ✅ .first() instead of .all()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")    
    return user

@router.delete("/student-users/{student_id}", status_code=status.HTTP_200_OK)
async def delete_student_user(
    student_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(UserModel).where(UserModel.student_id == student_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student account not found"
        )

    await db.delete(user)
    await db.commit()

    return {
        "message": "Student account deleted successfully",
        "student_id": student_id
    }

@router.put("/student-users/{student_id}/status")
async def update_user_status(
        student_id: str,
        payload: StatusUpdate,
        db: AsyncSession = Depends(get_db),
    ):
        user = await db.get(UserModel, student_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.is_active = payload.usr_active
        await db.commit()
        return {"success": True}