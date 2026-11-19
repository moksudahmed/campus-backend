from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.registration_application import RegistrationApplication
from app.models.registration_application_detail import (
    RegistrationApplicationDetail,
)
from app.models.registration_application_history import (
    RegistrationApplicationHistory,
)


# =========================================================
# DATE / TIME
# =========================================================

def now_utc() -> datetime:
    """
    Return the current UTC datetime.
    """
    return datetime.now(timezone.utc)


# =========================================================
# APPLICATION NUMBER
# =========================================================

def make_application_no() -> str:
    """
    Generate a unique registration application number.

    Example:
        REG-20261102-A1B2C3D4
    """
    date_part = now_utc().strftime("%Y%m%d")
    random_part = uuid4().hex[:8].upper()

    return f"REG-{date_part}-{random_part}"


# =========================================================
# CHECK STUDENT EXISTS
# =========================================================

async def student_exists(
    db: AsyncSession,
    student_id: str,
) -> bool:
    """
    Check whether a student exists in tbl_o_student.

    Assumed database column:
        public.tbl_o_student."studentID"
    """

    result = await db.execute(
        text("""
            SELECT 1
            FROM public.tbl_o_student
            WHERE "studentID" = :student_id
            LIMIT 1
        """),
        {
            "student_id": student_id,
        },
    )

    return result.first() is not None


# =========================================================
# GET APPLICATION
# =========================================================

async def get_application(
    db: AsyncSession,
    application_id: int,
) -> RegistrationApplication:
    """
    Retrieve a registration application by its ID.
    """

    result = await db.execute(
        select(RegistrationApplication).where(
            RegistrationApplication.application_id == application_id
        )
    )

    application = result.scalar_one_or_none()

    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration application not found.",
        )

    return application


# =========================================================
# CHECK APPLICATION ACCESS
# =========================================================
async def check_access(
    application: RegistrationApplication,
    user,
) -> bool:
    """
    Verify that the authenticated user can access an application.

    Student:
        Can only access their own applications.
    """

    user_student_id = getattr(user, "student_id", None)

    if not user_student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access is required.",
        )

    if str(application.studentID).strip() != str(user_student_id).strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this application.",
        )

    return True

async def check_access2(
    application: RegistrationApplication,
    user,
) -> bool:
    """
    Verify that the authenticated user can access an application.

    Students:
        Can only access their own applications.

    Registrar/Admin:
        Can access applications if their endpoint dependency
        has authorized their role.

    Other roles:
        Access is denied.
    """

    user_role = (
        getattr(user, "usr_role", "") or ""
    ).strip().lower()

    if user_role == "student":

        user_student_id = getattr(user, "student_id", None)

        if (
            not user_student_id
            or str(application.studentID) != str(user_student_id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to access this application.",
            )

    elif user_role not in {
        "registrar",
        "admin",
        "super-admin",
    }:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access registration applications.",
        )

    return True


# =========================================================
# CHECK WHETHER APPLICATION CAN BE EDITED
# =========================================================

async def ensure_editable(
    application: RegistrationApplication,
) -> bool:
    """
    Allow editing only when the application is in:

        DRAFT
        CHANGES_REQUESTED
    """

    allowed_statuses = {
        "DRAFT",
        "CHANGES_REQUESTED",
    }

    current_status = application.apl_application_status

    if current_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This application cannot be modified "
                "in its current status."
            ),
        )

    return True


# =========================================================
# ADD APPLICATION HISTORY
# =========================================================

async def add_history(
    db: AsyncSession,
    application: RegistrationApplication,
    user,
    action_type: str,
    new_status: str | None = None,
    remarks: str | None = None,
    metadata: dict | None = None,
    application_type: int | None = None,
    previous_status: str | None = None,
) -> RegistrationApplicationHistory:
    """
    Add an application history record.

    The history record is committed together with the
    corresponding application transaction.
    """

    action_by = (
        getattr(user, "student_id", None)
        or getattr(user, "login_id", None)
        or "SYSTEM"
    )

    action_by_role = getattr(user, "usr_role", None)

    history = RegistrationApplicationHistory(
        application_id=application.application_id,
        aph_previous_status=previous_status,
        aph_new_status=(
            new_status or application.apl_application_status
        ),
        aph_action_type=action_type,
        aph_action_by=str(action_by),
        aph_action_by_role=action_by_role,
        aph_action_remarks=remarks,
        aph_action_metadata=metadata or {},
        #apl_application_type=application_type,
        aph_action_at=now_utc(),
    )

    db.add(history)

    return history


# =========================================================
# COMMIT WITH DUPLICATE APPLICATION HANDLING
# =========================================================

async def commit_or_conflict(
    db: AsyncSession,
    conflict_message: str,
) -> None:
    """
    Commit the transaction.

    Handle database integrity violations as HTTP 409.
    Roll back the transaction if any error occurs.
    """

    try:
        await db.commit()

    except IntegrityError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_message,
        ) from exc

    except Exception:
        await db.rollback()
        raise


# =========================================================
# LOAD APPLICATION WITH DETAILS
# =========================================================

async def bundle(
    db: AsyncSession,
    application: RegistrationApplication,
) -> tuple[RegistrationApplication, list[RegistrationApplicationDetail]]:
    """
    Load an application and its associated subject details.

    Returns:
        (
            application,
            details
        )
    """

    result = await db.execute(
        select(RegistrationApplicationDetail)
        .where(
            RegistrationApplicationDetail.application_id
            == application.application_id
        )
        .order_by(
            RegistrationApplicationDetail.application_detail_id.asc()
        )
    )

    details = result.scalars().all()

    return application, details
