from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, require_student
from app.database import get_db
from app.models import (
    RegistrationApplicationDetail,
)
from app.schemas import (
    ApplicationDetailOut,
    DetailCreate,
)
from app.services import (
    add_history,
    check_access,
    commit_or_conflict,
    ensure_editable,
    get_application,
    offered_module_exists,
    recompute_total,
)
from app.routers.registration.helpers import output


router = APIRouter()


# =========================================================
# ADD SUBJECT / MODULE
# POST /{application_id}/details
# =========================================================

@router.post(
    "/{application_id}/details",
    response_model=ApplicationDetailOut,
)
async def add_detail(
    application_id: int,
    payload: DetailCreate,
    user: CurrentUser = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    application = await get_application(db, application_id)

    await check_access(application, user)
    await ensure_editable(application)

    if not await offered_module_exists(
        db,
        payload.offered_module_id,
    ):
        raise HTTPException(
            status_code=404,
            detail="Offered module was not found.",
        )

    detail = RegistrationApplicationDetail(
        application_id=application_id,
        offeredModuleID=payload.offered_module_id,
        apd_credit_hours=payload.credit_hours,
        apd_detail_remarks=payload.remarks,
    )

    db.add(detail)

    try:
        await db.flush()

        await recompute_total(db, application_id)

        await add_history(
            db,
            application,
            user,
            "MODULE_ADDED",
            remarks=payload.remarks,
            metadata={
                "offeredModuleID": payload.offered_module_id,
                "credit_hours": str(payload.credit_hours),
            },
        )

        await commit_or_conflict(
            db,
            "This offered module is already included in the application.",
        )

    except Exception:
        await db.rollback()
        raise

    await db.refresh(application)

    return await output(db, application)


# =========================================================
# REMOVE SUBJECT / MODULE
# DELETE /{application_id}/details/{detail_id}
# =========================================================

@router.delete(
    "/{application_id}/details/{detail_id}",
    response_model=ApplicationDetailOut,
)
async def delete_detail(
    application_id: int,
    detail_id: int,
    user: CurrentUser = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    application = await get_application(db, application_id)

    await check_access(application, user)
    await ensure_editable(application)

    result = await db.execute(
        select(RegistrationApplicationDetail).where(
            RegistrationApplicationDetail.application_id
            == application_id,
            RegistrationApplicationDetail.application_detail_id
            == detail_id,
        )
    )

    detail = result.scalar_one_or_none()

    if detail is None:
        raise HTTPException(
            status_code=404,
            detail="Application detail was not found.",
        )

    module_id = detail.offeredModuleID

    await db.delete(detail)
    await db.flush()

    await recompute_total(db, application_id)

    await add_history(
        db,
        application,
        user,
        "MODULE_REMOVED",
        metadata={
            "offeredModuleID": module_id,
            "application_detail_id": detail_id,
        },
    )

    await db.commit()
    await db.refresh(application)

    return await output(db, application)