from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, require_registrar
from app.database import get_db
from app.models import (
    RegistrationApplication,
    RegistrationApplicationDetail,
)
from app.schemas import (
    ApplicationDetailOut,
    ReviewRequest,
)
from app.services import (
    add_history,
    commit_or_conflict,
    get_application,
    now_utc,
)
from app.routers.registration.helpers import output


router = APIRouter()


# =========================================================
# LIST ALL APPLICATIONS
# GET /api/v1/registration-applications
# =========================================================

@router.get(
    "",
    response_model=list[ApplicationDetailOut],
)
async def list_all(
    application_status: str | None = Query(
        None,
        alias="status",
    ),
    term: int | None = Query(None, gt=0),
    year: int | None = Query(None, gt=0),
    student_id: str | None = Query(None, max_length=15),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_registrar),
    db: AsyncSession = Depends(get_db),
):
    allowed_statuses = {
        "DRAFT",
        "SUBMITTED",
        "UNDER_REVIEW",
        "CHANGES_REQUESTED",
        "APPROVED",
        "REJECTED",
        "CANCELLED",
    }

    if (
        application_status
        and application_status not in allowed_statuses
    ):
        raise HTTPException(
            status_code=422,
            detail="Invalid application status filter.",
        )

    query = select(RegistrationApplication)

    if application_status:
        query = query.where(
            RegistrationApplication.apl_application_status
            == application_status
        )

    if term is not None:
        query = query.where(
            RegistrationApplication.apl_term == term
        )

    if year is not None:
        query = query.where(
            RegistrationApplication.apl_year == year
        )

    if student_id:
        query = query.where(
            RegistrationApplication.studentID == student_id
        )

    result = await db.execute(
        query
        .order_by(
            RegistrationApplication.apl_created_at.desc()
        )
        .limit(limit)
        .offset(offset)
    )

    applications = result.scalars().all()

    return [
        await output(db, application)
        for application in applications
    ]


# =========================================================
# START APPLICATION REVIEW
# POST /{application_id}/review/start
# =========================================================

@router.post(
    "/{application_id}/review/start",
    response_model=ApplicationDetailOut,
)
async def start_review(
    application_id: int,
    payload: ReviewRequest,
    user: CurrentUser = Depends(require_registrar),
    db: AsyncSession = Depends(get_db),
):
    application = await get_application(db, application_id)

    if application.apl_application_status != "SUBMITTED":
        raise HTTPException(
            status_code=409,
            detail="Only submitted applications can enter review.",
        )

    old_status = application.apl_application_status

    application.apl_application_status = "UNDER_REVIEW"
    application.apl_reviewed_by = user.user_id[:100]
    application.apl_reviewed_at = now_utc()
    application.apl_reviewer_remarks = payload.remarks

    await add_history(
        db,
        application,
        user,
        "REVIEW_STARTED",
        "UNDER_REVIEW",
        remarks=payload.remarks,
        previous_status=old_status,
    )

    await db.commit()
    await db.refresh(application)

    return await output(db, application)


# =========================================================
# REQUEST CHANGES
# POST /{application_id}/review/request-changes
# =========================================================

@router.post(
    "/{application_id}/review/request-changes",
    response_model=ApplicationDetailOut,
)
async def request_changes(
    application_id: int,
    payload: ReviewRequest,
    user: CurrentUser = Depends(require_registrar),
    db: AsyncSession = Depends(get_db),
):
    application = await get_application(db, application_id)

    allowed_statuses = {
        "SUBMITTED",
        "UNDER_REVIEW",
    }

    if application.apl_application_status not in allowed_statuses:
        raise HTTPException(
            status_code=409,
            detail=(
                "Only submitted or under-review applications "
                "can be returned for changes."
            ),
        )

    if not payload.remarks or not payload.remarks.strip():
        raise HTTPException(
            status_code=422,
            detail="Reviewer remarks are required when requesting changes.",
        )

    old_status = application.apl_application_status

    application.apl_application_status = "CHANGES_REQUESTED"
    application.apl_reviewed_by = user.user_id[:100]
    application.apl_reviewed_at = now_utc()
    application.apl_reviewer_remarks = payload.remarks

    await add_history(
        db,
        application,
        user,
        "CHANGES_REQUESTED",
        "CHANGES_REQUESTED",
        remarks=payload.remarks,
        previous_status=old_status,
    )

    await db.commit()
    await db.refresh(application)

    return await output(db, application)


# =========================================================
# APPROVE APPLICATION
# POST /{application_id}/review/approve
# =========================================================

@router.post(
    "/{application_id}/review/approve",
    response_model=ApplicationDetailOut,
)
async def approve(
    application_id: int,
    payload: ReviewRequest,
    user: CurrentUser = Depends(require_registrar),
    db: AsyncSession = Depends(get_db),
):
    application = await get_application(db, application_id)

    if application.apl_application_status != "UNDER_REVIEW":
        raise HTTPException(
            status_code=409,
            detail="Only applications under review can be approved.",
        )

    result = await db.execute(
        select(
            RegistrationApplicationDetail.application_detail_id
        )
        .where(
            RegistrationApplicationDetail.application_id
            == application_id
        )
        .limit(1)
    )

    if result.first() is None:
        raise HTTPException(
            status_code=400,
            detail="An application without subjects cannot be approved.",
        )

    old_status = application.apl_application_status

    application.apl_application_status = "APPROVED"
    application.apl_reviewed_by = user.user_id[:100]
    application.apl_reviewed_at = now_utc()
    application.apl_reviewer_remarks = payload.remarks

    await add_history(
        db,
        application,
        user,
        "APPLICATION_APPROVED",
        "APPROVED",
        remarks=payload.remarks,
        metadata={
            "official_registration_created": False,
        },
        previous_status=old_status,
    )

    await db.commit()
    await db.refresh(application)

    return await output(db, application)


# =========================================================
# REJECT APPLICATION
# POST /{application_id}/review/reject
# =========================================================

@router.post(
    "/{application_id}/review/reject",
    response_model=ApplicationDetailOut,
)
async def reject(
    application_id: int,
    payload: ReviewRequest,
    user: CurrentUser = Depends(require_registrar),
    db: AsyncSession = Depends(get_db),
):
    application = await get_application(db, application_id)

    allowed_statuses = {
        "SUBMITTED",
        "UNDER_REVIEW",
    }

    if application.apl_application_status not in allowed_statuses:
        raise HTTPException(
            status_code=409,
            detail=(
                "Only submitted or under-review applications "
                "can be rejected."
            ),
        )

    if not payload.remarks or not payload.remarks.strip():
        raise HTTPException(
            status_code=422,
            detail="Reviewer remarks are required when rejecting an application.",
        )

    old_status = application.apl_application_status

    application.apl_application_status = "REJECTED"
    application.apl_reviewed_by = user.user_id[:100]
    application.apl_reviewed_at = now_utc()
    application.apl_reviewer_remarks = payload.remarks

    await add_history(
        db,
        application,
        user,
        "APPLICATION_REJECTED",
        "REJECTED",
        remarks=payload.remarks,
        previous_status=old_status,
    )

    await db.commit()
    await db.refresh(application)

    return await output(db, application)