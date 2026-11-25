from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from app.api.v1.endpoints.registration_auth import (
    CurrentUser,
    get_current_user,
    require_student,
)
from typing import List
from decimal import Decimal
from app.api.v1.endpoints.registration_helpers import output

from app.db.session import get_db

from app.models import (
    RegistrationApplication,
    RegistrationApplicationDetail,
    
    
)
from app.models.user import User as UserModel

from app.schemas import (
    ApplicationCreate,
    ApplicationDetailOut,
    ApplicationUpdate,
    ReviewRequest,
    
)
from app.models.course_offer_list import CourseOfferList
from app.schemas.registration_application import RegistrationApplicationOut
from app.schemas.registration_application import (
    RegistrationApplicationDetailCreate
)
from app.services.registration_service import (
    add_history,
    check_access,
    commit_or_conflict,
    ensure_editable,
    get_application,
    make_application_no,
    now_utc,
    student_exists,
)



from app.models.registration_application import RegistrationApplication
from app.models.registration_application_history import RegistrationApplicationHistory

router = APIRouter()


# =========================================================
# CREATE APPLICATION
# POST /api/v1/registration-applications
# =========================================================

@router.post(
    "",
    response_model=ApplicationDetailOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_application(
    payload: ApplicationCreate,
    user: CurrentUser = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    sid = user.student_id
    print("Test", payload.application_type)
    if not sid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student ID is missing from the authenticated user.",
        )

    if len(sid) > 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student ID exceeds the database column length.",
        )

    if not await student_exists(db, sid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student record was not found.",
        )

    application = RegistrationApplication(
        application_no=make_application_no(),
        studentID=sid,
        apl_term=payload.term,
        apl_year=payload.year,
        apl_application_status="DRAFT",
        apl_total_credit_hours=0,
        apl_student_remarks=payload.student_remarks,
        apl_application_type = payload.application_type
    )

    db.add(application)

    try:
        await db.flush()

        await add_history(
            db,
            application,
            user,
            "APPLICATION_CREATED",
            "DRAFT",
            remarks=payload.student_remarks,
            metadata={
                "term": payload.term,
                "year": payload.year                
            },
            application_type = payload.application_type,
            previous_status=None,
        )

        await commit_or_conflict(
            db,
            "An active application already exists for this student, term, and year.",
        )

    except Exception:
        await db.rollback()
        raise

    await db.refresh(application)

    return await output(db, application)


# =========================================================
# LIST STUDENT APPLICATIONS
# GET /api/v1/registration-applications/mine
# =========================================================
@router.get(
    "/mine",
    response_model=List[RegistrationApplicationOut],
)
async def list_mine(
    user: UserModel = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RegistrationApplication)
        .where(
            RegistrationApplication.studentID == user.student_id
        )
        .order_by(
            RegistrationApplication.apl_created_at.desc()
        )
    )

    applications = result.scalars().all()

    response = []

    for application in applications:
        response.append(
            await output(db, application)
        )

    return response

# =========================================================
# GET SINGLE APPLICATION
# GET /api/v1/registration-applications/{application_id}
# =========================================================
@router.get(
    "/mine/{application_id}",
    response_model=ApplicationDetailOut,
)
async def get_one(
    application_id: int,
    user: UserModel = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    
    application = await get_application(db, application_id)

    await check_access(application, user)

    return await output(db, application)


@router.get("/available-subjects")
async def get_available_subjects(
    regi_type: int = Query(..., ge=1, le=7),
    term: int = Query(..., ge=1),
    year: int = Query(..., ge=2000),
    user: UserModel = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve available subjects according to registration type.

    Registration types:
        1 = Regular
        2 = Supplementary
        3 = Retake
        4 = Improvement
        5 = Other (not configured)
        6 = Special-Supplementary (not configured)
    """
    
    
    student_id = user.student_id
   
    # Validate supported registration types
    supported_types = (1, 2, 3, 4)

    if regi_type not in supported_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration type {regi_type} is not configured yet.",
        )

    try:
        query = text("""
            SELECT *
            FROM public.fn_get_available_registration_subjects(
                :student_id,
                :regi_type,
                :term,
                :year
            )
        """)

        result = await db.execute(
            query,
            {
                "student_id": student_id,
                "regi_type": regi_type,
                "term": term,
                "year": year,
            },
        )

        subjects = result.mappings().all()      
        return {
            "total": len(subjects),
            "student_id": student_id,
            "regi_type": regi_type,
            "term": term,
            "year": year,
            "subjects": [
                {
                    "offeredModuleID": row["offeredModuleID"],
                    "moduleRegistrationID": row["moduleRegistrationID"],
                    "moduleCode": row["moduleCode"],
                    "mod_name": row["mod_name"],
                    "mod_creditHour": row["mod_creditHour"],
                    "mod_group": row["mod_group"],
                    "mod_type": row["mod_type"],
                    "status": row["letterGrade"],
                    "gradePoint": row["gradePoint"],
                }
                for row in subjects
            ],
        }

    except Exception as e:
        print(
            f"[AVAILABLE SUBJECTS ERROR] "
            f"Student: {student_id}, "
            f"Registration Type: {regi_type}, "
            f"Error: {str(e)}"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve available subjects.",
        )

# Add subject

# ---------------------------------------------------------
# GET: Retrieve application details
# ---------------------------------------------------------


# ---------------------------------------------------------
# GET: Retrieve application details
# ---------------------------------------------------------
@router.get("/{application_id}/details")
async def get_application_details(
    application_id: int,
    user=Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    sid = user.student_id

    if not sid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student ID is missing.",
        )

    # 1. Verify application ownership
    result = await db.execute(
        select(RegistrationApplication).where(
            RegistrationApplication.application_id == application_id,
            RegistrationApplication.studentID == sid,
        )
    )

    application = result.scalar_one_or_none()

    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration application not found.",
        )

    # 2. Retrieve application details with course information
    result = await db.execute(
        select(
            RegistrationApplicationDetail,
            CourseOfferList.moduleCode,
            CourseOfferList.mod_name,
            CourseOfferList.mod_creditHour,
            CourseOfferList.mod_group,
            CourseOfferList.mod_type,
        )
        .outerjoin(
            CourseOfferList,
            RegistrationApplicationDetail.offeredModuleID
            == CourseOfferList.offeredModuleID,
        )
        .where(
            RegistrationApplicationDetail.application_id == application_id
        )
        .order_by(
            RegistrationApplicationDetail.application_detail_id
        )
    )

    rows = result.all()

    details = []

    for item, module_code, module_name, credit_hour, module_group, module_type in rows:
        details.append(
            {
                "application_detail_id": item.application_detail_id,
                "application_id": item.application_id,
                "offeredModuleID": item.offeredModuleID,
                "moduleCode": module_code,
                "mod_name": module_name,
                "apd_credit_hours": float(item.apd_credit_hours or 0),
                "mod_creditHour": (
                    float(credit_hour) if credit_hour is not None else None
                ),
                "mod_group": module_group,
                "mod_type": module_type,
                "apd_detail_remarks": item.apd_detail_remarks,
                "apd_created_at": item.apd_created_at,
            }
        )

    return {
        "application_id": application.application_id,
        "application_no": application.application_no,
        "student_id": sid,
        "term": application.apl_term,
        "year": application.apl_year,
        "status": application.apl_application_status,
        "total_credit_hours": float(
            application.apl_total_credit_hours or 0
        ),
        "total": len(details),
        "details": details,
    }


# ---------------------------------------------------------
# POST: Add a subject to a registration application
# ---------------------------------------------------------

# =========================================================
# ADD SUBJECT TO REGISTRATION APPLICATION
# POST /api/v1/registration-applications/{application_id}/details
# =========================================================

@router.post(
    "/{application_id}/details",
    status_code=status.HTTP_201_CREATED,
)
async def add_application_detail(
    application_id: int,
    payload: RegistrationApplicationDetailCreate,
    user: UserModel = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    sid = user.student_id

    if not sid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student ID is missing.",
        )

    # =====================================================
    # 1. VERIFY APPLICATION OWNERSHIP
    # =====================================================

    result = await db.execute(
        select(RegistrationApplication).where(
            RegistrationApplication.application_id == application_id,
            RegistrationApplication.studentID == sid,
        )
    )

    application = result.scalar_one_or_none()

    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration application not found.",
        )

    # =====================================================
    # 2. CHECK APPLICATION STATUS
    # =====================================================

    if application.apl_application_status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft applications can be modified.",
        )

    # =====================================================
    # 3. DETERMINE REGISTRATION TYPE
    # =====================================================

    # Type 3 = Supplementary
    is_supplementary = (
        int(application.apl_application_type) == 3
    )

    offered_module_id = None
    module_registration_id = None
    offered_module = None

    # =====================================================
    # 4. SUPPLEMENTARY REGISTRATION
    # =====================================================

    if is_supplementary:

        if payload.moduleRegistrationID is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Module Registration ID is required "
                    "for supplementary registration."
                ),
            )

        if payload.offeredModuleID is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Offered Module ID must be empty "
                    "for supplementary registration."
                ),
            )

        # IMPORTANT:
        # Assign the actual previous module registration ID.
        module_registration_id = payload.moduleRegistrationID

        # -------------------------------------------------
        # 4.1 VERIFY STUDENT OWNERSHIP
        # -------------------------------------------------

        result = await db.execute(
            text("""
                SELECT v."studentID"
                FROM public.vw_result_final_exam v
                WHERE v."moduleRegistrationID" = :module_registration_id
                LIMIT 1
            """),
            {
                "module_registration_id": module_registration_id
            },
        )

        registered_student = result.mappings().first()

        if registered_student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module registration not found.",
            )

        if str(registered_student["studentID"]) != str(sid):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This module registration does not belong to you.",
            )

        # -------------------------------------------------
        # 4.2 GET ORIGINAL OFFERED MODULE ID
        # -------------------------------------------------

        result = await db.execute(
            text("""
                SELECT mr."offeredModuleID"
                FROM public.tbl_s_moduleregistration mr
                WHERE mr."moduleRegistrationID" = :module_registration_id
                LIMIT 1
            """),
            {
                "module_registration_id": module_registration_id
            },
        )

        previous_registration = result.mappings().first()

        if previous_registration is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Previous module registration was not found.",
            )

        original_offered_module_id = (
            previous_registration["offeredModuleID"]
        )

        if original_offered_module_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Original offered module was not found.",
            )

        # -------------------------------------------------
        # 4.3 GET ORIGINAL COURSE INFORMATION
        # -------------------------------------------------

        # Do not filter by the current application term/year.
        # Supplementary uses a previous module registration.

        result = await db.execute(
            select(CourseOfferList).where(
                CourseOfferList.offeredModuleID
                == original_offered_module_id
            )
        )   

        offered_module = result.scalar_one_or_none()

    # =====================================================
    # 5. REGULAR / OTHER REGISTRATION TYPES
    # =====================================================

    else:
        print("HEllo Offered", payload.offeredModuleID)
        if payload.offeredModuleID is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Offered Module ID is required "
                    "for this registration type."
                ),
            )

        if payload.moduleRegistrationID is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Module Registration ID must be empty "
                    "for this registration type."
                ),
            )

        offered_module_id = payload.offeredModuleID

        # -------------------------------------------------
        # 5.1 VERIFY CURRENT OFFERED MODULE
        # -------------------------------------------------

        result = await db.execute(
            select(CourseOfferList).where(
                CourseOfferList.offeredModuleID == offered_module_id,
                CourseOfferList.ofm_term == application.apl_term,
                CourseOfferList.ofm_year == application.apl_year,
            )
        )

        offered_module = result.scalar_one_or_none()

    # =====================================================
    # 6. VERIFY COURSE AND CREDIT HOURS
    # =====================================================

    if offered_module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course information could not be found.",
        )

    if offered_module.mod_creditHour is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credit hours are not available for this subject.",
        )

    # Always use database credit hours.
    credit_hours = Decimal(
        str(offered_module.mod_creditHour)
    )

    # =====================================================
    # 7. PREVENT DUPLICATE SUBJECTS
    # =====================================================

    duplicate_conditions = [
        RegistrationApplicationDetail.application_id
        == application_id
    ]

    if is_supplementary:

        duplicate_conditions.append(
            RegistrationApplicationDetail.moduleRegistrationID
            == module_registration_id
        )

    else:

        duplicate_conditions.append(
            RegistrationApplicationDetail.offeredModuleID
            == offered_module_id
        )

    result = await db.execute(
        select(RegistrationApplicationDetail).where(
            *duplicate_conditions
        )
    )

    existing_detail = result.scalar_one_or_none()

    if existing_detail is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This subject has already been added.",
        )

    # =====================================================
    # 8. DETERMINE REGISTRATION STATUS
    # =====================================================

    if is_supplementary:
        registration_status = "Supple"
    else:
        registration_status = (
            payload.apd_reg_status or "Regular"
        )

    allowed_statuses = {
        "Regular",
        "Retake",
        "Retaken",
        "Exempted",
        "Expelled",
        "Improve",
        "Supple",
        "Special-Supple",
    }

    if registration_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subject registration status.",
        )

    # =====================================================
    # 9. INSERT APPLICATION DETAIL
    # =====================================================

    detail = RegistrationApplicationDetail(
        application_id=application_id,

        # Supplementary: NULL
        # Other types: actual offeredModuleID
        offeredModuleID=offered_module_id,

        # Supplementary: actual moduleRegistrationID
        # Other types: NULL
        moduleRegistrationID=module_registration_id,

        apd_credit_hours=credit_hours,

        apd_detail_remarks=payload.apd_detail_remarks,

        apd_reg_status=registration_status,
    )

    try:
        db.add(detail)

        # Update total application credit hours.
        current_total = Decimal(
            str(application.apl_total_credit_hours or 0)
        )

        application.apl_total_credit_hours = (
            current_total + credit_hours
        )

        await db.flush()
        await db.commit()

        await db.refresh(detail)
        await db.refresh(application)

    except Exception:
        await db.rollback()
        raise

    # =====================================================
    # 10. RETURN RESPONSE
    # =====================================================

    return {
        "message": "Subject added successfully.",

        "application_id": application.application_id,

        "detail": {
            "application_detail_id": detail.application_detail_id,

            "offeredModuleID": detail.offeredModuleID,

            "moduleRegistrationID": detail.moduleRegistrationID,

            "moduleCode": offered_module.moduleCode,

            "mod_name": offered_module.mod_name,

            "apd_credit_hours": float(
                detail.apd_credit_hours
            ),

            "apd_reg_status": detail.apd_reg_status,

            "apd_detail_remarks": detail.apd_detail_remarks,

            "apd_created_at": detail.apd_created_at,
        },

        "total_credit_hours": float(
            application.apl_total_credit_hours
        ),
    }

# =========================================================
# UPDATE APPLICATION
# PATCH /api/v1/registration-applications/{application_id}
# =========================================================

@router.patch(
    "/{application_id}",
    response_model=ApplicationDetailOut,
)
async def update_one(
    application_id: int,
    payload: ApplicationUpdate,
    user: CurrentUser = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    application = await get_application(db, application_id)

    await check_access(application, user)
    await ensure_editable(application)

    application.apl_student_remarks = payload.student_remarks

    await add_history(
        db,
        application,
        user,
        "APPLICATION_UPDATED",
        remarks=payload.student_remarks,
    )

    await db.commit()
    await db.refresh(application)

    return await output(db, application)


@router.delete(
    "/{application_id}/details/{detail_id}",
    status_code=status.HTTP_200_OK
)
async def delete_registration_application_detail(
    application_id: int,
    detail_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Delete a subject from a registration application.

    Only the owner of a DRAFT application can remove subjects.
    """

    # 1. Verify application ownership
    application_query = await db.execute(
        select(RegistrationApplication).where(
            RegistrationApplication.application_id == application_id,
            RegistrationApplication.studentID == current_user.student_id
        )
    )

    application = application_query.scalar_one_or_none()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration application not found."
        )

    # 2. Only DRAFT applications can be modified
    if application.apl_application_status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft registration applications can be modified."
        )

    # 3. Find the requested subject detail
    detail_query = await db.execute(
        select(RegistrationApplicationDetail).where(
            RegistrationApplicationDetail.application_detail_id == detail_id,
            RegistrationApplicationDetail.application_id == application_id
        )
    )

    detail = detail_query.scalar_one_or_none()

    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject registration detail not found."
        )

    # 4. Delete subject registration detail
    try:
        await db.delete(detail)
        await db.commit()

        return {
            "success": True,
            "message": "Subject removed successfully.",
            "application_id": application_id,
            "detail_id": detail_id
        }

    except Exception:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to remove subject registration."
        )

# =========================================================
# SUBMIT APPLICATION
# POST /api/v1/registration-applications/{application_id}/submit
# =========================================================

@router.post(
    "/{application_id}/submit",
    response_model=ApplicationDetailOut,
)
async def submit(
    application_id: int,
    user: CurrentUser = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    application = await get_application(db, application_id)

    await check_access(application, user)
    await ensure_editable(application)

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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add at least one subject before submitting.",
        )

    old_status = application.apl_application_status

    application.apl_application_status = "SUBMITTED"
    application.apl_submitted_at = now_utc()

    await add_history(
        db,
        application,
        user,
        "APPLICATION_SUBMITTED",
        "SUBMITTED",
        previous_status=old_status,
    )

    await commit_or_conflict(
        db,
        "An active application already exists for this student, term, and year.",
    )

    await db.refresh(application)

    return await output(db, application)


# =========================================================
# CANCEL APPLICATION
# POST /api/v1/registration-applications/{application_id}/cancel
# =========================================================

from typing import Optional
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


class CancelRequest(BaseModel):
    remarks: Optional[str] = None


@router.post(
    "/{application_id}/cancel",
    response_model=ApplicationDetailOut,
)
async def cancel(
    application_id: int,
    payload: Optional[CancelRequest] = None,
    user: CurrentUser = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    application = await get_application(db, application_id)

    await check_access(application, user)

    allowed_statuses = {
        "DRAFT",
        "SUBMITTED",
        "CHANGES_REQUESTED",
    }

    if application.apl_application_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This application can no longer be cancelled by the student.",
        )

    old_status = application.apl_application_status

    remarks = payload.remarks if payload else None

    application.apl_application_status = "CANCELLED"
    application.apl_reviewer_remarks = remarks

    await add_history(
        db,
        application,
        user,
        "APPLICATION_CANCELLED",
        "CANCELLED",
        remarks=remarks,
        previous_status=old_status,
    )

    await db.commit()
    await db.refresh(application)

    return await output(db, application)


@router.get("/{application_id}/history")
async def get_application_history(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_student),
):
    # Verify application ownership
    result = await db.execute(
        select(RegistrationApplication).where(
            RegistrationApplication.application_id == application_id,
            RegistrationApplication.studentID == user.student_id,
        )
    )

    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    # Fetch application history
    result = await db.execute(
        select(RegistrationApplicationHistory)
        .where(
            RegistrationApplicationHistory.application_id == application_id
        )
        .order_by(
            RegistrationApplicationHistory.aph_action_at.desc(),
            RegistrationApplicationHistory.history_id.desc(),
        )
    )

    history_records = result.scalars().all()

    return {
        "application_id": application.application_id,
        "application_no": application.application_no,
        "student_id": application.studentID,
        "total": len(history_records),
        "history": [
            {
                "history_id": item.history_id,
                "previous_status": item.aph_previous_status,
                "new_status": item.aph_new_status,
                "action_type": item.aph_action_type,
                "action_by": item.aph_action_by,
                "action_by_role": item.aph_action_by_role,
                "remarks": item.aph_action_remarks,
                "metadata": item.aph_action_metadata,
                "action_at": item.aph_action_at,
            }
            for item in history_records
        ],
    }