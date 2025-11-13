from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import FastAPI, HTTPException, Query, Request
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Dict
import asyncio
from dataclasses import dataclass
from app.schemas.auth import Token, UserCreate, UserResponse, UserUpdate, RoleAssignRequest, ResetPasswordRequest, StandardResponse
from app.models.user import User as UserModel
from app.db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from app.core.security import get_password_hash
# Password hashing context
#pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============= CONFIGURATION =============

@dataclass
class EmailConfig:
    smtp_server: str
    smtp_port: int
    sender_email: str
    sender_password: str
    use_tls: bool = True



# ============= PASSWORD RESET SERVICE =============

class PasswordResetService:
    def __init__(self, config: EmailConfig):
        self.config = config
        # In production, use Redis or a database for tokens
        self.reset_tokens: Dict = {}
    
    async def get_user_by_id(self, db: AsyncSession, student_id: str) -> Optional[UserModel]:
        """Fetch user from database by email/login_id"""
        try:
            result = await db.execute(
                select(UserModel).where(UserModel.student_id == student_id)
            )
            user = result.scalar_one_or_none()
            return user
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None
        
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[UserModel]:
        """Fetch user from database by email/login_id"""
        try:
            result = await db.execute(
                select(UserModel).where(UserModel.login_id == email)
            )
            user = result.scalar_one_or_none()
            return user
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None
    async def user_exists(self, db: AsyncSession, student_id: str) -> bool:
        """Check if user exists in database"""
        user = await self.get_user_by_id(db, student_id)
        return user #is not None
    
    def generate_reset_token(self, user_email: str, expiry_hours: int = 1) -> str:
        """Generate a secure password reset token"""
        token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(hours=expiry_hours)
        
        self.reset_tokens[token] = {
            'email': user_email.lower(),
            'expiry': expiry,
            'used': False,
            'created_at': datetime.now()
        }
        
        return token
    
    def create_reset_email_html(self, user_name: str, reset_link: str) -> str:
        """Create HTML email template"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background-color: #f9f9f9;
                    border-radius: 5px;
                    padding: 30px;
                    border: 1px solid #ddd;
                }}
                .header {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                    margin: -30px -30px 20px -30px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                    font-weight: bold;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border: 1px solid #ffc107;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <p>Hello {user_name},</p>
                <p>We received a request to reset your password. Click the button below:</p>
                <div style="text-align: center;">
                    <a href="{reset_link}" class="button">Reset Password</a>
                </div>
                <p>Or copy this link: <br><code style="word-break: break-all;">{reset_link}</code></p>
                <div class="warning">
                    <strong>⚠️ Important:</strong>
                    <ul>
                        <li>This link expires in 1 hour</li>
                        <li>If you didn't request this, ignore this email</li>
                        <li>Never share this link with anyone</li>
                    </ul>
                </div>
                <p style="margin-top: 30px; color: #777; font-size: 12px;">
                    This is an automated message, please do not reply.
                </p>
            </div>
        </body>
        </html>
        """
        return html
    
    async def send_reset_email(self, db: AsyncSession, recipient_email: str, reset_link: str) -> bool:
        """Send password reset email asynchronously"""
        try:
            # Fetch user from database
            user = await self.get_user_by_email(db, recipient_email)
            
            # Use user's name from database or default to 'User'
            user_name = user.name if user and hasattr(user, 'name') else 'User'
            
            message = MIMEMultipart('alternative')
            message['Subject'] = 'Password Reset Request'
            message['From'] = self.config.sender_email
            message['To'] = recipient_email
            
            html_content = self.create_reset_email_html(user_name, reset_link)
            part = MIMEText(html_content, 'html')
            message.attach(part)
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_smtp_email, message)
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def _send_smtp_email(self, message):
        """Synchronous SMTP email sending"""
        with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
            if self.config.use_tls:
                server.starttls()
            server.login(self.config.sender_email, self.config.sender_password)
            server.send_message(message)
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify reset token validity"""
        if token not in self.reset_tokens:
            return None
        
        token_data = self.reset_tokens[token]
        
        if token_data['used']:
            return None
        
        if datetime.now() > token_data['expiry']:
            return None
        
        return token_data['email']
    
    def mark_token_used(self, token: str):
        """Mark token as used"""
        if token in self.reset_tokens:
            self.reset_tokens[token]['used'] = True
    
    async def update_password(self, db: AsyncSession, email: str, new_password: str) -> bool:
        """Update user password in database"""
        try:
            # Fetch user from database
            user = await self.get_user_by_email(db, email)
            
            if not user:
                return False
            
            # Hash the new password
            hashed_password = get_password_hash(new_password)
            
            # Update user password
            user.hash_password  = hashed_password
            #user.updated_at = datetime.now()
            
            # Commit changes
            await db.commit()
            await db.refresh(user)
            
            return True
            
        except Exception as e:
            await db.rollback()
            print(f"Error updating password: {e}")
            return False