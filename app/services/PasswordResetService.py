from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict
import smtplib
import secrets
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.models.user import User as UserModel
from app.models.password_reset import PasswordResetToken
from app.schemas.auth import StandardResponse
from app.core.security import get_password_hash
from app.db.session import get_db
from sqlalchemy import delete


# ========== CONFIGURATION ==========

@dataclass
class EmailConfig:
    smtp_server: str
    smtp_port: int
    sender_email: str
    sender_password: str
    use_tls: bool = True


# ========== PASSWORD RESET SERVICE ==========

class PasswordResetService:
    def __init__(self, config: EmailConfig):
        self.config = config

    # -----------------------
    # 🔹 User Operations
    # -----------------------
    
    async def get_user_by_id(self, db: AsyncSession, student_id: str) -> Optional[UserModel]:
        """Fetch user from DB by email/login_id"""
        result = await db.execute(select(UserModel).where(UserModel.student_id == student_id))
        return result.scalar_one_or_none()
        
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[UserModel]:
        """Fetch user from DB by email/login_id"""
        result = await db.execute(select(UserModel).where(UserModel.login_id == email.lower()))
        return result.scalar_one_or_none()

    # -----------------------
    # 🔹 Token Management
    # -----------------------

    async def generate_reset_token(
        self, db: AsyncSession, email: str, expiry_hours: int = 1
    ) -> str:
        """
        Generate a password reset token, remove previous tokens,
        and ensure the new token is correctly inserted.
        """
        try:
            token = secrets.token_urlsafe(32)
            expiry = datetime.utcnow() + timedelta(hours=expiry_hours)
            normalized_email = email.lower()

            # 1️⃣ Remove old tokens for this email
            await db.execute(
                delete(PasswordResetToken).where(
                    PasswordResetToken.email == normalized_email
                )
            )

            # 2️⃣ Insert new token
            new_token = PasswordResetToken(
                token=token,
                email=normalized_email,
                expiry=expiry,
                used=False,
                created_at=datetime.utcnow(),
            )

            db.add(new_token)

            # Ensures insert happens before commit
            await db.flush()
            await db.refresh(new_token)

            # 3️⃣ Save changes
            await db.commit()

            return token

        except Exception as e:
            await db.rollback()
            print("❌ ERROR saving reset token:", e)
            raise HTTPException(
                status_code=500,
                detail="Failed to generate password reset token.",
            )


    async def user_exists(self, db: AsyncSession, student_id: str) -> bool:
        """Check if user exists in database"""
        user = await self.get_user_by_id(db, student_id)
        return user #is not None
    
    async def verify_token(self, db: AsyncSession, token: str) -> Optional[str]:
        """
        Validate the provided reset token.
        Returns the associated email (lowercased) when the token exists, is unexpired and not used.
        Returns None otherwise.
        """
        if not token:
            return None

        try:
            result = await db.execute(
                select(PasswordResetToken).where(PasswordResetToken.token == token)
            )
            token_data = result.scalar_one_or_none()

            # not found
            if token_data is None:
                return None

            # already used or expired
            if token_data.used:
                return None

            if datetime.utcnow() > token_data.expiry:
                return None

            # token_data.email should be a string column on the model
            return token_data.email.lower() if token_data.email else None

        except Exception as exc:
            # Replace print with your logger if available
            print(f"Error verifying token: {exc}")
            return None


    async def mark_token_used(self, db: AsyncSession, token: str):
        """Mark token as used"""
        try:
            result = await db.execute(select(PasswordResetToken).where(PasswordResetToken.token == token))
            token_obj = result.scalar_one_or_none()
            if token_obj:
                token_obj.used = True
                await db.commit()
                
        except Exception as exc:
            # Replace print with your logger if available
            print(f"Error verifying token: {exc}")
            return None

    # -----------------------
    # 🔹 Password Update
    # -----------------------

    async def update_password(self, db: AsyncSession, email: str, new_password: str) -> bool:
        """Securely update the user's password."""

        user = await self.get_user_by_email(db, email)
        if not user:
            return False

        user.hash_password = get_password_hash(new_password)        

        try:
            db.add(user)
            await db.commit()
            await db.refresh(user)            
            
            return True
        except Exception:
            await db.rollback()
            return False

    # -----------------------
    # 🔹 Email Sending
    # -----------------------

    def _send_smtp_email(self, message):
        """Send email via SMTP"""
        with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
            if self.config.use_tls:
                server.starttls()
            server.login(self.config.sender_email, self.config.sender_password)
            server.send_message(message)

    async def send_reset_email(self, db: AsyncSession, recipient_email: str, reset_link: str) -> bool:
        """Send password reset email"""
        try:
            user = await self.get_user_by_email(db, recipient_email)
            user_name = getattr(user, "name", "User")

            message = MIMEMultipart("alternative")
            message["Subject"] = "Password Reset Request"
            message["From"] = self.config.sender_email
            message["To"] = recipient_email

            html = self.create_reset_email_html(user_name, reset_link)
            message.attach(MIMEText(html, "html"))

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_smtp_email, message)
            return True
        except Exception as e:
            print(f"❌ Error sending reset email: {e}")
            return False

    def create_reset_email_html(self, user_name: str, reset_link: str) -> str:
        """HTML Template for Email"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; background:#f9f9f9; padding:20px;">
            <div style="background:#fff; padding:30px; border-radius:10px;">
                <h2 style="color:#4F46E5;">Password Reset Request</h2>
                <p>Hello {user_name},</p>
                <p>Click below to reset your password:</p>
                <a href="{reset_link}" style="background:#4F46E5; color:white; padding:10px 20px; border-radius:6px; text-decoration:none;">Reset Password</a>
                <p style="margin-top:20px;">Link expires in 1 hour.</p>
            </div>
        </body>
        </html>
        """
