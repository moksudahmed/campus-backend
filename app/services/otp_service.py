
import hashlib
import logging
import secrets
import time

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.email import send_otp_email
from app.models.user import User

logger = logging.getLogger(__name__)


# --------------------------------------------------
# CONFIGURATION HELPERS
# --------------------------------------------------

def current_timestamp() -> int:
    return int(time.time())


def generate_otp() -> str:
    """Generate a cryptographically secure six-digit OTP."""
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(student_id: str, otp: str) -> str:
    """Hash the OTP consistently with the student ID."""
    raw = f"{student_id.strip()}:{str(otp).strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def mask_email(email: str) -> str:
    """Mask an email address before returning it to the frontend."""
    if not email or "@" not in email:
        return "your registered email"

    local, domain = email.split("@", 1)

    if len(local) <= 2:
        masked = "*" * len(local)
    else:
        masked = local[0] + "*" * (len(local) - 2) + local[-1]

    return f"{masked}@{domain}"


def clear_student_otp(user: User) -> None:
    """Invalidate the OTP and reset its associated state."""
    user.usr_otp = None
    user.usr_otp_expire = None
    user.usr_otp_attempts = 0
    user.usr_otp_resend_at = None


# --------------------------------------------------
# DATABASE HELPERS
# --------------------------------------------------

async def get_student_user(
    db: AsyncSession,
    student_id: str,
    *,
    lock: bool = False,
) -> User | None:
    """Retrieve a student account by ID."""
    query = select(User).where(
        User.student_id == student_id.strip()
    )

    if lock:
        query = query.with_for_update()

    result = await db.execute(query)
    return result.scalar_one_or_none()


# --------------------------------------------------
# CREATE AND SEND OTP
# --------------------------------------------------

async def create_and_send_otp(
    db: AsyncSession,
    student_id: str,
    email: str,
) -> dict:
    """Generate an OTP, store its hash, and email the OTP."""
    student_id = str(student_id or "").strip()
    email = str(email or "").strip()

    if not student_id:
        raise HTTPException(
            status_code=400,
            detail="Student ID is required.",
        )

    if not email or "@" not in email:
        raise HTTPException(
            status_code=400,
            detail="A valid registered email address is required.",
        )

    try:
        user = await get_student_user(db, student_id, lock=True)

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="Student account not found.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=403,
                detail="This student account is inactive.",
            )

        now = current_timestamp()
        resend_at = user.usr_otp_resend_at

        if resend_at is not None and now < int(resend_at):
            remaining = int(resend_at) - now
            raise HTTPException(
                status_code=429,
                detail=f"Please wait {remaining} seconds before requesting another OTP.",
            )

        otp = generate_otp()
        expiry_seconds = int(settings.OTP_EXPIRE_MINUTES * 60)
        resend_seconds = int(settings.OTP_RESEND_SECONDS)

        user.usr_otp = hash_otp(student_id, otp)
        user.usr_otp_expire = now + expiry_seconds
        user.usr_otp_attempts = 0
        user.usr_otp_resend_at = now + resend_seconds

        await db.commit()

    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        logger.exception("Failed to create OTP")
        raise HTTPException(
            status_code=500,
            detail="Unable to create verification code.",
        )

    # Send the email after committing the OTP.
    try:
        await send_otp_email(
            to_email=email,
            otp=otp,
            student_id=student_id,
        )
    except Exception:
        logger.exception("Failed to send OTP email for student %s", student_id)

        try:
            user = await get_student_user(db, student_id, lock=True)
            if user is not None:
                clear_student_otp(user)
                await db.commit()
        except Exception:
            await db.rollback()
            logger.exception("Failed to clear OTP after email delivery failure")

        raise HTTPException(
            status_code=503,
            detail="Unable to send the verification code. Please try again later.",
        )

    return {
        "success": True,
        "message": "OTP sent successfully.",
        "email": mask_email(email),
        "expires_in": expiry_seconds,
    }


# --------------------------------------------------
# VERIFY OTP
# --------------------------------------------------

async def verify_student_otp(
    db: AsyncSession,
    student_id: str,
    otp: str,
) -> bool:
    """Verify the OTP and invalidate it after success or lockout."""
    student_id = str(student_id or "").strip()
    otp = str(otp or "").strip()

    if not student_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification request.",
        )

    try:
        user = await get_student_user(db, student_id, lock=True)

        if user is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid verification request.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=403,
                detail="This student account is inactive.",
            )

        stored_otp = user.usr_otp

        if not stored_otp:
            raise HTTPException(
                status_code=400,
                detail="No active verification code found. Please login again.",
            )

        now = current_timestamp()
        expiry = user.usr_otp_expire

        if expiry is None or int(expiry) <= now:
            clear_student_otp(user)
            await db.commit()
            raise HTTPException(
                status_code=400,
                detail="The verification code has expired. Please login again.",
            )

        max_attempts = int(settings.OTP_MAX_ATTEMPTS)
        attempts = int(user.usr_otp_attempts or 0)

        if attempts >= max_attempts:
            clear_student_otp(user)
            await db.commit()
            raise HTTPException(
                status_code=429,
                detail="Too many incorrect attempts. Please login again.",
            )

        if len(otp) != 6 or not otp.isdigit():
            attempts += 1
            user.usr_otp_attempts = attempts

            if attempts >= max_attempts:
                clear_student_otp(user)
                await db.commit()
                raise HTTPException(
                    status_code=429,
                    detail="Too many incorrect attempts. Please login again.",
                )

            await db.commit()
            raise HTTPException(
                status_code=400,
                detail=f"Enter the 6-digit verification code. {max_attempts - attempts} attempt(s) remaining.",
            )

        expected_hash = hash_otp(student_id, otp)

        if not secrets.compare_digest(expected_hash, str(stored_otp).strip()):
            attempts += 1
            user.usr_otp_attempts = attempts

            if attempts >= max_attempts:
                clear_student_otp(user)
                await db.commit()
                raise HTTPException(
                    status_code=429,
                    detail="Too many incorrect attempts. Please login again.",
                )

            await db.commit()
            raise HTTPException(
                status_code=400,
                detail=f"Incorrect verification code. {max_attempts - attempts} attempt(s) remaining.",
            )

        # Correct OTP: invalidate it to prevent reuse.
        clear_student_otp(user)
        await db.commit()

        return True

    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        logger.exception("OTP verification failed for student %s", student_id)
        raise HTTPException(
            status_code=500,
            detail="Unable to verify the code. Please try again.",
        )


# --------------------------------------------------
# RESEND OTP
# --------------------------------------------------

async def resend_student_otp(
    db: AsyncSession,
    student_id: str,
    email: str,
) -> dict:
    """Resend an OTP subject to the configured cooldown."""
    student_id = str(student_id or "").strip()

    user = await get_student_user(db, student_id)

    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification request.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="This student account is inactive.",
        )

    now = current_timestamp()
    resend_at = user.usr_otp_resend_at

    if resend_at is not None and int(resend_at) > now:
        remaining = int(resend_at) - now
        raise HTTPException(
            status_code=429,
            detail=f"Please wait {remaining} seconds before requesting another OTP.",
        )

    return await create_and_send_otp(
        db=db,
        student_id=student_id,
        email=email,
    )
