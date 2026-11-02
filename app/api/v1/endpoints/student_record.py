from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.db.session import get_db
from app.models.student_record import StudentRecord
from app.schemas.student_record import StudentRecordSchema
import os
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_token

security = HTTPBearer()


router = APIRouter()

PHOTO_DIRECTORY = "D:/htdocs/muerp/photograph"

# ✅ Return list of students
@router.get("/", response_model=List[StudentRecordSchema])
async def read_students(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    stmt = select(StudentRecord).offset(skip).limit(limit)
    result = await db.execute(stmt)
    results = result.scalars().all()
    return results


# ✅ Return a single student
# ✅ Return a single student — requires valid token
@router.get("/{student_id}", response_model=StudentRecordSchema)
async def read_student(
    student_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    # --------------------------------------------------
    # 1. Get token from Authorization: Bearer <token>
    # --------------------------------------------------
    token = credentials.credentials
    print("TEStSTESTETSET")
    # --------------------------------------------------
    # 2. Verify token
    # --------------------------------------------------
    token_record = await verify_token(
        db=db,
        token=token,
    )

    # --------------------------------------------------
    # 3. Make sure token belongs to the requested student
    # --------------------------------------------------
    if str(token_record.tokenable_id) != str(student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this student record.",
        )

    # --------------------------------------------------
    # 4. Get student record
    # --------------------------------------------------
    stmt = select(StudentRecord).where(
        StudentRecord.student_id == student_id
    )

    result = await db.execute(stmt)

    student = result.scalars().first()

    # --------------------------------------------------
    # 5. Student not found
    # --------------------------------------------------
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # --------------------------------------------------
    # 6. Return student record
    # --------------------------------------------------
    return student


#DEFAULT_PHOTO = "G:/React App/MuErp/mu_erp_backend/default-avatar.jpg"   
#PHOTO_DIRECTORY = "static/photos"
DEFAULT_PHOTO = "static/photos/default-avatar.jpg"

@router.get("/student-photo/{student_id}")
async def get_student_photo(
    student_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    Serve a student's photo by student_id.

    Requires:
        Authorization: Bearer <access_token>

    Returns:
        Student photo if available.
        Default photo if the student's photo does not exist.
    """

    # --------------------------------------------------
    # 1. Get Bearer token
    # --------------------------------------------------
    token = credentials.credentials

    # --------------------------------------------------
    # 2. Verify token
    # --------------------------------------------------
    token_record = await verify_token(
        db=db,
        token=token,
    )

    # --------------------------------------------------
    # 3. Make sure token belongs to requested student
    # --------------------------------------------------
    if str(token_record.tokenable_id) != str(student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this student's photo.",
        )

    # --------------------------------------------------
    # 4. Build student photo path
    # --------------------------------------------------
    filename = f"{student_id}.jpg"
    filepath = os.path.join(
        PHOTO_DIRECTORY,
        filename,
    )

    # --------------------------------------------------
    # 5. Use default photo if student photo doesn't exist
    # --------------------------------------------------
    if not os.path.exists(filepath):
        filepath = DEFAULT_PHOTO

    # --------------------------------------------------
    # 6. Return image
    # --------------------------------------------------
    return FileResponse(
        filepath,
        media_type="image/jpeg",
    )
"""@router.get("/{student_id}", response_model=StudentRecordSchema)
def read_student(student_id: int, db: Session = Depends(get_db)):
    student = crud.get_student_record_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.get("/search/", response_model=List[StudentRecordSchema])
def search_students(name: str, db: Session = Depends(get_db)):
    students = crud.search_student_records(db, name=name)
    if not students:
        raise HTTPException(status_code=404, detail="No students found")
    return students"""
