import logging

from fastapi.concurrency import run_in_threadpool
from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_email_sync(to_email: str, subject: str, body: str) -> None:
    import smtplib
    from email.message import EmailMessage

    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "noreply@metrouni.edu.bd"
    smtp_password = "tnhn uwcm cara ozyl"
    sender_email = "noreply@metrouni.edu.bd"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = to_email
    message.set_content(body)

   

    with smtplib.SMTP(
        smtp_host,
        smtp_port,
        timeout=20,
    ) as server:
        server.starttls()
        server.login(
            smtp_user ,
            smtp_password,
        )
        server.send_message(message)


async def send_otp_email(
    to_email: str,
    otp: str,
    student_id: str,
) -> None:
    subject = "Student Portal - OTP Verification"

    body = (
        f"Dear Student,\n\n"
        f"Your verification code is: {otp}\n\n"
        f"Student ID: {student_id}\n"
        f"This code expires in "
        f"{settings.OTP_EXPIRE_MINUTES} minutes.\n\n"
        f"If you did not request this code, please ignore this email.\n"
    )

    try:
        await run_in_threadpool(
            _send_email_sync,
            to_email,
            subject,
            body,
        )
    except Exception:
        logger.exception("Failed to send OTP email")
        raise