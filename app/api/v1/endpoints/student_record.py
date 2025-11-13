from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.db.session import get_db
from app.models.student_record import StudentRecord
from app.schemas.student_record import StudentRecordSchema
import os
from fastapi.responses import FileResponse

router = APIRouter()

PHOTO_DIRECTORY = "C:/xampp/htdocs/muerp/photograph/"

# ✅ Return list of students
@router.get("/", response_model=List[StudentRecordSchema])
async def read_students(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    stmt = select(StudentRecord).offset(skip).limit(limit)
    result = await db.execute(stmt)
    results = result.scalars().all()
    return results


# ✅ Return a single student
@router.get("/{student_id}", response_model=StudentRecordSchema)
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

DEFAULT_PHOTO = "G:/React App/MuErp/mu_erp_backend/default-avatar.jpg"   

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
