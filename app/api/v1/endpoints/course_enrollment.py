from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.db.session import get_db
from app.models.course_enrollment import CourseEnrollment
from app.schemas.course_enrollment import CourseEnrollmentSchema
from app.services.OptionService import OptionService

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

    
@router.get("/enrolled/{student_id}", response_model=List[CourseEnrollmentSchema])
async def read_course_enrollment_by_term(
    student_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get course enrollments for a specific student
    filtered by current term and year
    """

    option_service = OptionService(db)

    # Fetch options
    option_year = await option_service.get_by_name("current_year")
    option_term = await option_service.get_by_name("current_term")

    if not option_year or not option_term:
        raise HTTPException(
            status_code=500,
            detail="Current academic year or term is not configured"
        )

    try:
        current_year = int(option_year.option_value)
        current_term = int(option_term.option_value)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=500,
            detail="Invalid current_year or current_term configuration"
        )

    stmt = (
        select(CourseEnrollment)
        .where(
            CourseEnrollment.student_id == student_id,
            CourseEnrollment.tra_term == current_term,
            CourseEnrollment.tra_year == current_year,
        )
        .order_by(
            CourseEnrollment.tra_year.asc(),
            CourseEnrollment.tra_term.asc(),
        )
    )

    result = await db.execute(stmt)
    enrollments = result.scalars().all()

    if not enrollments:
        raise HTTPException(
            status_code=404,
            detail="No course enrollments found"
        )

    return enrollments