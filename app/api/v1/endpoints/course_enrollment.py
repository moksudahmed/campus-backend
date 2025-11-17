from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.db.session import get_db
from app.models.course_enrollment import CourseEnrollment
from app.schemas.course_enrollment import CourseEnrollmentSchema

router = APIRouter()

"""@router.get("/", response_model=List[CourseEnrollmentSchema])
async def read_course_enrollments(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    
    stmt = select(CourseEnrollment).offset(skip).limit(limit)
    result = await db.execute(stmt)
    enrollments = result.scalars().all()
    return enrollments """


@router.get("/{student_id}", response_model=List[CourseEnrollmentSchema])
async def read_course_enrollment_by_student(
    student_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all course enrollments for a specific student
    """
    #stmt = select(CourseEnrollment).where(CourseEnrollment.student_id == student_id)
    stmt = (
        select(CourseEnrollment)
        .where(CourseEnrollment.student_id == student_id)
        .order_by(
            CourseEnrollment.tra_year.asc(),
            CourseEnrollment.tra_term.asc(),
        )
    )
    result = await db.execute(stmt)
    enrollments = result.scalars().all()

    if not enrollments:
        raise HTTPException(status_code=404, detail="No course enrollments found")

    return enrollments
