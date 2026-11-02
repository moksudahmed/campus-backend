from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.db.session import get_db
from app.models.course_enrollment import CourseEnrollment
from app.schemas.course_enrollment import CourseEnrollmentSchema
from app.services.OptionService import OptionService

# Import your token verification function
from app.core.security import verify_token


router = APIRouter()

security = HTTPBearer()


# ==========================================================
# Get all course enrollments for a student
# ==========================================================

@router.get(
    "/{student_id}",
    response_model=List[CourseEnrollmentSchema]
)
async def read_course_enrollment_by_student(
    student_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all course enrollments for a specific student.

    Requires:
        Authorization: Bearer <access_token>
    """

    # ------------------------------------------------------
    # 1. Get Bearer token
    # ------------------------------------------------------

    token = credentials.credentials

    # ------------------------------------------------------
    # 2. Verify token
    # ------------------------------------------------------

    token_record = await verify_token(
        db=db,
        token=token,
    )

    # ------------------------------------------------------
    # 3. Make sure token belongs to requested student
    # ------------------------------------------------------

    if str(token_record.tokenable_id) != str(student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access these course enrollments.",
        )

    # ------------------------------------------------------
    # 4. Get enrollments
    # ------------------------------------------------------

    stmt = (
        select(CourseEnrollment)
        .where(
            CourseEnrollment.student_id == student_id
        )
        .order_by(
            CourseEnrollment.tra_year.asc(),
            CourseEnrollment.tra_term.asc(),
        )
    )

    result = await db.execute(stmt)

    enrollments = result.scalars().all()

    # ------------------------------------------------------
    # 5. No enrollments
    # ------------------------------------------------------

    if not enrollments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No course enrollments found",
        )

    return enrollments


# ==========================================================
# Get current-term course enrollments
# ==========================================================

@router.get(
    "/enrolled/{student_id}",
    response_model=List[CourseEnrollmentSchema]
)
async def read_course_enrollment_by_term(
    student_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    Get course enrollments for a specific student
    filtered by the current academic term and year.

    Requires:
        Authorization: Bearer <access_token>
    """

    # ------------------------------------------------------
    # 1. Get Bearer token
    # ------------------------------------------------------

    token = credentials.credentials

    # ------------------------------------------------------
    # 2. Verify token
    # ------------------------------------------------------

    token_record = await verify_token(
        db=db,
        token=token,
    )

    # ------------------------------------------------------
    # 3. Make sure token belongs to requested student
    # ------------------------------------------------------

    if str(token_record.tokenable_id) != str(student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access these course enrollments.",
        )

    # ------------------------------------------------------
    # 4. Get current academic year and term
    # ------------------------------------------------------

    option_service = OptionService(db)

    option_year = await option_service.get_by_name(
        "current_year"
    )

    option_term = await option_service.get_by_name(
        "current_term"
    )

    if not option_year or not option_term:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Current academic year or term is not configured",
        )

    # ------------------------------------------------------
    # 5. Validate configuration
    # ------------------------------------------------------

    try:
        current_year = int(
            option_year.option_value
        )

        current_term = int(
            option_term.option_value
        )

    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid current_year or current_term configuration",
        )

    # ------------------------------------------------------
    # 6. Get current-term enrollments
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # 7. No enrollments
    # ------------------------------------------------------

    if not enrollments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No course enrollments found",
        )

    return enrollments