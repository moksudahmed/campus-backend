import hashlib
import secrets
import time

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.email import send_otp_email

from app.models.student_user import StudentUser


def current_timestamp() -> int:
    return int(time.time())


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(
    student_id: str,
    otp: str,
) -> str:

    raw = f"{student_id}:{otp}"

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


def mask_email(email: str) -> str:

    if not email or "@" not in email:
        return "your registered email"

    local, domain = email.split("@", 1)

    if len(local) <= 2:
        masked = "*" * len(local)
    else:
        masked = (
            local[0]
            + "*" * (len(local) - 2)
            + local[-1]
        )

    return f"{masked}@{domain}"


async def get_student_user(
    db: AsyncSession,
    student_id: str,
):

    result = await db.execute(
        select(StudentUser).where(
            StudentUser.studentID == student_id
        )
    )

    return result.scalar_one_or_none()


async def create_and_send_otp(
    db: AsyncSession,
    student_id: str,
    email: str,
):

    student_user = await get_student_user(
        db,
        student_id,
    )

    if student_user is None:

        raise HTTPException(
            status_code=404,
            detail="Student account not found.",
        )

    if not student_user.usr_active:

        raise HTTPException(
            status_code=403,
            detail="This student account is inactive.",
        )

    now = current_timestamp()

    otp = generate_otp()

    otp_hash = hash_otp(
        student_id,
        otp,
    )

    expires_at = (
        now
        + settings.OTP_EXPIRE_MINUTES * 60
    )

    resend_at = (
        now
        + settings.OTP_RESEND_SECONDS
    )

    student_user.usr_otp = otp_hash

    student_user.usr_otpExpire = expires_at

    student_user.usr_otpAttempts = 0

    student_user.usr_otpResendAt = resend_at

    await db.commit()

    try:

        await send_otp_email(
            to_email=email,
            otp=otp,
            student_id=student_id,
        )

    except Exception:

        # Do not leave a usable OTP
        # if email delivery fails.

        student_user.usr_otp = None

        student_user.usr_otpExpire = None

        student_user.usr_otpAttempts = 0

        student_user.usr_otpResendAt = None

        await db.commit()

        raise HTTPException(
            status_code=503,
            detail=(
                "Unable to send the verification code. "
                "Please try again later."
            ),
        )

    return {
        "email": mask_email(email),
        "expires_in":
            settings.OTP_EXPIRE_MINUTES * 60,
    }


async def verify_student_otp(
    db: AsyncSession,
    student_id: str,
    otp: str,
):

    student_user = await get_student_user(
        db,
        student_id,
    )

    if student_user is None:

        raise HTTPException(
            status_code=400,
            detail="Invalid verification request.",
        )

    if not student_user.usr_active:

        raise HTTPException(
            status_code=403,
            detail="This student account is inactive.",
        )

    if not student_user.usr_otp:

        raise HTTPException(
            status_code=400,
            detail=(
                "No active verification code found. "
                "Please login again."
            ),
        )

    now = current_timestamp()

    # ------------------------------------------------
    # EXPIRY
    # ------------------------------------------------

    if (
        not student_user.usr_otpExpire
        or student_user.usr_otpExpire <= now
    ):

        student_user.usr_otp = None

        student_user.usr_otpExpire = None

        student_user.usr_otpAttempts = 0

        student_user.usr_otpResendAt = None

        await db.commit()

        raise HTTPException(
            status_code=400,
            detail=(
                "The verification code has expired. "
                "Please login again."
            ),
        )

    # ------------------------------------------------
    # ATTEMPTS
    # ------------------------------------------------

    attempts = (
        student_user.usr_otpAttempts or 0
    )

    if attempts >= settings.OTP_MAX_ATTEMPTS:

        student_user.usr_otp = None

        student_user.usr_otpExpire = None

        student_user.usr_otpAttempts = 0

        student_user.usr_otpResendAt = None

        await db.commit()

        raise HTTPException(
            status_code=429,
            detail=(
                "Too many incorrect attempts. "
                "Please login again."
            ),
        )

    # ------------------------------------------------
    # FORMAT
    # ------------------------------------------------

    otp = str(otp).strip()

    if (
        len(otp) != 6
        or not otp.isdigit()
    ):

        student_user.usr_otpAttempts = attempts + 1

        await db.commit()

        raise HTTPException(
            status_code=400,
            detail="Enter the 6-digit verification code.",
        )

    # ------------------------------------------------
    # HASH
    # ------------------------------------------------

    expected_hash = hash_otp(
        student_id,
        otp,
    )

    # ------------------------------------------------
    # CONSTANT-TIME COMPARISON
    # ------------------------------------------------

    if not secrets.compare_digest(
        expected_hash,
        student_user.usr_otp,
    ):

        student_user.usr_otpAttempts = (
            attempts + 1
        )

        await db.commit()

        remaining = (
            settings.OTP_MAX_ATTEMPTS
            - student_user.usr_otpAttempts
        )

        if remaining <= 0:

            student_user.usr_otp = None

            student_user.usr_otpExpire = None

            student_user.usr_otpAttempts = 0

            student_user.usr_otpResendAt = None

            await db.commit()

            raise HTTPException(
                status_code=429,
                detail=(
                    "Too many incorrect attempts. "
                    "Please login again."
                ),
            )

        raise HTTPException(
            status_code=400,
            detail=(
                "Incorrect verification code. "
                f"{remaining} attempt(s) remaining."
            ),
        )

    # ------------------------------------------------
    # SUCCESS
    # ------------------------------------------------

    # IMPORTANT:
    # OTP can never be used twice.

    student_user.usr_otp = None

    student_user.usr_otpExpire = None

    student_user.usr_otpAttempts = 0

    student_user.usr_otpResendAt = None

    await db.commit()

    return True


async def resend_student_otp(
    db: AsyncSession,
    student_id: str,
    email: str,
):

    student_user = await get_student_user(
        db,
        student_id,
    )

    if student_user is None:

        raise HTTPException(
            status_code=400,
            detail="Invalid verification request.",
        )

    now = current_timestamp()

    resend_at = (
        student_user.usr_otpResendAt
    )

    if resend_at and resend_at > now:

        remaining = resend_at - now

        raise HTTPException(
            status_code=429,
            detail=(
                f"Please wait {remaining} seconds "
                "before requesting another code."
            ),
        )

    return await create_and_send_otp(
        db=db,
        student_id=student_id,
        email=email,
    )