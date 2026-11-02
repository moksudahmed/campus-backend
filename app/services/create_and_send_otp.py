import os
import secrets
import hashlib
import smtplib

from email.message import EmailMessage


class OTPService:
    def __init__(self):
        self.otp_length = 6
        self.otp_expiry_seconds = 300  # 5 minutes

    @staticmethod
    def hash_otp(otp: str) -> str:
        """Hash the OTP before storing it in PostgreSQL."""
        return hashlib.sha256(otp.encode("utf-8")).hexdigest()

    def generate_otp(self) -> str:
        """Generate a cryptographically secure 6-digit OTP."""
        return f"{secrets.randbelow(1_000_000):06d}"

    def send_email(self, recipient_email: str, otp: str) -> None:
        """Send OTP through the configured SMTP server."""
        
        smtp_host = "smtp.gmail.com"
        smtp_port = 587
        smtp_user = "noreply@metrouni.edu.bd"
        smtp_password = "tnhn uwcm cara ozyl"
        sender_email = "noreply@metrouni.edu.bd"

        if not all(
            [smtp_host, smtp_user, smtp_password, sender_email]
        ):
            raise RuntimeError(
                "SMTP configuration is incomplete. "
                "Check SMTP_HOST, SMTP_PORT, SMTP_USERNAME, "
                "SMTP_PASSWORD, and SMTP_FROM_EMAIL."
            )

        message = EmailMessage()
        message["Subject"] = "Metropolitan University - Login OTP"
        message["From"] = sender_email
        message["To"] = recipient_email

        message.set_content(
            f"""Dear Student,

Your verification code is: {otp}

This code expires in 5 minutes.

If you did not request this code, please ignore this email.

Metropolitan University
"""
        )

        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(message)


otp_service = OTPService()





import os
import secrets
import hashlib
import smtplib
import hmac

from datetime import datetime, timezone
from email.message import EmailMessage

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User  # Adjust if your model is in another file


class OTPService:
    OTP_EXPIRY_SECONDS = 300  # 5 minutes
    OTP_RESEND_COOLDOWN = 60   # 60 seconds
    OTP_MAX_ATTEMPTS = 5
    
    @staticmethod
    def hash_otp(otp: str) -> str:
        return hashlib.sha256(otp.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_otp() -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

    @staticmethod
    def current_timestamp() -> int:
        return int(datetime.now(timezone.utc).timestamp())

    def send_email(self, recipient_email: str, otp: str) -> None:       

        smtp_host = "smtp.gmail.com"
        smtp_port = 587
        smtp_user = "noreply@metrouni.edu.bd"
        smtp_password = "tnhn uwcm cara ozyl"
        sender_email = "noreply@metrouni.edu.bd"

        if not all(
            [smtp_host, smtp_user, smtp_password, sender_email]
        ):
            raise RuntimeError("SMTP configuration is incomplete.")

        message = EmailMessage()
        message["Subject"] = "Metropolitan University - Login OTP"
        message["From"] = sender_email
        message["To"] = recipient_email
        message.set_content(
            f"""Dear Student,

Your login verification code is: {otp}

This code expires in 5 minutes.

If you did not request this code, please ignore this email.

Metropolitan University
"""
        )

        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(message)

    async def create_and_send_otp(
        self,
        db: AsyncSession,
        student_id: str,
        recipient_email: str,
    ) -> dict:
        """
        Generate an OTP, store its hash and expiry, and send it by email.

        The OTP is not returned to the client.
        """

        if not recipient_email:
            return {
                "success": False,
                "message": "A registered email address is required.",
            }

        result = await db.execute(
            select(User)
            .where(User.student_id == student_id)
            .with_for_update()
        )
        user = result.scalar_one_or_none()

        if user is None:
            return {
                "success": False,
                "message": "Student account not found.",
            }

        if not user.is_active:
            return {
                "success": False,
                "message": "This account is inactive.",
            }

        now = self.current_timestamp()

        # Prevent repeated OTP requests.
        resend_at = getattr(user, "usr_otp_resend_at", None)
        if resend_at is not None and now < resend_at:
            await db.rollback()
            return {
                "success": False,
                "message": "Please wait before requesting another OTP.",
            }

        otp = self.generate_otp()

        user.usr_otp = self.hash_otp(otp)
        user.usr_otp_expire = now + self.OTP_EXPIRY_SECONDS
        user.usr_otp_attempts = 0
        user.usr_otp_resend_at = now + self.OTP_RESEND_COOLDOWN

        try:
            await db.commit()

            # SMTP is synchronous, so run it in a worker thread.
            import asyncio

            await asyncio.to_thread(
                self.send_email,
                recipient_email,
                otp,
            )

        except Exception:
            await db.rollback()

            # Invalidate the OTP if email delivery fails.
            try:
                result = await db.execute(
                    select(User).where(User.student_id == student_id)
                )
                user = result.scalar_one_or_none()

                if user is not None:
                    user.usr_otp = None
                    user.usr_otp_expire = None
                    user.usr_otp_attempts = 0
                    user.usr_otp_resend_at = None
                    await db.commit()
            except Exception:
                await db.rollback()

            raise

        return {
            "success": True,
            "message": "OTP sent successfully.",
            "expires_in": self.OTP_EXPIRY_SECONDS,
        }
    

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
    async def verify_student_otp(
        db: AsyncSession,
        student_id: str,
        otp: str,
    ) -> bool:
        """
        Verify a student's OTP using the SHA-256 hash generated by
        hash_otp(student_id, otp).

        Enforces expiration and maximum attempts.
        Clears the OTP after expiration, lockout, or successful use.
        """

        student_id = str(student_id).strip()
        otp = str(otp or "").strip()

        # 1. Retrieve the student account.
        student_user = await get_student_user(
            db=db,
            student_id=student_id,
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

        stored_otp = student_user.usr_otp

        if not stored_otp:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No active verification code found. "
                    "Please login again."
                ),
            )

        now = current_timestamp()

        # 2. Check OTP expiration.
        if (
            not student_user.usr_otpExpire
            or int(student_user.usr_otpExpire) <= now
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

        # 3. Check the number of failed attempts.
        attempts = student_user.usr_otpAttempts or 0
        max_attempts = settings.OTP_MAX_ATTEMPTS

        if attempts >= max_attempts:
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

        # 4. Validate the six-digit OTP format.
        if len(otp) != 6 or not otp.isdigit():
            student_user.usr_otpAttempts = attempts + 1

            if student_user.usr_otpAttempts >= max_attempts:
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

            await db.commit()

            remaining = max_attempts - (attempts + 1)

            raise HTTPException(
                status_code=400,
                detail=(
                    "Enter the 6-digit verification code. "
                    f"{remaining} attempt(s) remaining."
                ),
            )

        # 5. Hash the submitted OTP using the same algorithm
        #    and student ID used when generating the OTP.
        expected_hash = hash_otp(
            student_id=student_id,
            otp=otp,
        )

        # 6. Compare the calculated hash with the stored hash.
        if not secrets.compare_digest(
            expected_hash,
            str(stored_otp).strip(),
        ):
            student_user.usr_otpAttempts = attempts + 1

            if student_user.usr_otpAttempts >= max_attempts:
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

            await db.commit()

            remaining = max_attempts - (attempts + 1)

            raise HTTPException(
                status_code=400,
                detail=(
                    "Incorrect verification code. "
                    f"{remaining} attempt(s) remaining."
                ),
            )

        # 7. OTP verified successfully. Invalidate it immediately.
        student_user.usr_otp = None
        student_user.usr_otpExpire = None
        student_user.usr_otpAttempts = 0
        student_user.usr_otpResendAt = None

        await db.commit()

        return True


otp_service = OTPService()