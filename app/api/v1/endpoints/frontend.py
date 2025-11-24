from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Dict
import os
import asyncio
from dataclasses import dataclass
from app.services.PasswordResetService import PasswordResetService
from app.schemas.auth import StandardResponse, ForgotPasswordRequest, TokenVerifyResponse, ResetPasswordRequest, ResetRequestWithToken
from fastapi import APIRouter, Depends, HTTPException, status
from app.db.session import get_db

router = APIRouter()
# ============= CONFIGURATION =============

@dataclass
class EmailConfig:
    smtp_server: str
    smtp_port: int
    sender_email: str
    sender_password: str
    use_tls: bool = True

# Initialize service
config = EmailConfig(
    smtp_server=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    smtp_port=int(os.getenv('SMTP_PORT', 587)),
    sender_email=os.getenv('SENDER_EMAIL', 'noreply@metrouni.edu.bd'),
    sender_password=os.getenv('SENDER_PASSWORD', 'tnhn uwcm cara ozyl'),
    use_tls=True
)


reset_service = PasswordResetService(config)

# ============= API ENDPOINTS =============

@router.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Password Reset API",
        "version": "1.0.0",
        "endpoints": {
            "forgot_password": "POST /api/forgot-password",
            "verify_token": "GET /api/verify-token",
            "reset_password": "POST /api/reset-password",
            "reset_page": "GET /reset-password?token=xxx",
            "health": "GET /health",
            "docs": "GET /docs"
        }
    }

@router.post("/api/forgot-password", response_model=StandardResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request a password reset email
    
    - **email**: Valid email address of the user
    """
    try:
        #email = request.email.lower()
        student_id = request.student_id
        #print(email)
        # Check if user exists
        user_found = await reset_service.user_exists(db, student_id)
        
        if not user_found:
            # Don't reveal if user doesn't exist (security)
            return StandardResponse(
                success=True,
                message="If the email exists, a reset link has been sent"
            )
        
        email = user_found.login_id
        
        # Generate token
        token = await reset_service.generate_reset_token(db, email)
        
        # Create reset link
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        reset_link = f"{frontend_url}/reset-password?token={token}"
        
        # Send email asynchronously
        email_sent = await reset_service.send_reset_email(db, email, reset_link)
        
        if email_sent:
            return StandardResponse(
                success=True,
                message="Password reset email sent successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email. Please try again later."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Forgot password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing your request"
        )


@router.get("/api/verify-token", response_model=TokenVerifyResponse)
async def verify_token(token: str = Query(..., description="Reset token to verify"), db: AsyncSession = Depends(get_db)):
    """
    Verify if a reset token is valid
    
    - **token**: The reset token from the email link
    """    
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is required"
        )
    
    email = await reset_service.verify_token(db,token)
    
    if email:
        return TokenVerifyResponse(
            valid=True,
            message="Token is valid",
            email=email
        )
    else:
        return TokenVerifyResponse(
            valid=False,
            message="Token is invalid or expired",
            email=None
        )

    
@router.post("/api/reset-password", response_model=StandardResponse)
async def reset_password(
    request: ResetRequestWithToken,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password using a valid token
    
    - **token**: Valid reset token
    - **new_password**: New password (minimum 8 characters)
    """
    try:        
        # Verify token
        email = await reset_service.verify_token(db, request.token)
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token"
            )
        
        # Update password in database
        password_updated = await reset_service.update_password(
            db, email, request.new_password
        )
        
        if password_updated:                   
            reset_service.mark_token_used(db, request.token)            
            return StandardResponse(
                success=True,
                message="Password reset successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset password"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Reset password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing your request"
        )

@router.get("/reset-password", response_class=HTMLResponse, tags=["Frontend"])
async def reset_password_page(token: str = Query(..., description="Reset token"), db: AsyncSession = Depends(get_db)):
    """
    Password reset page (HTML form)
    
    This endpoint handles: http://localhost:3000/reset-password?token=xxx
    """
    # Verify token
    email = reset_service.verify_token(token)
    
    if not email:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Invalid Token</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }
                .container {
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 400px;
                }
                .error { color: #e74c3c; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="error">❌ Invalid or Expired Token</h1>
                <p>This password reset link is invalid or has expired.</p>
                <p>Please request a new password reset.</p>
            </div>
        </body>
        </html>
        """, status_code=400)
    
    # Render password reset form
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Reset Password</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                width: 100%;
                max-width: 400px;
            }}
            h1 {{ color: #333; margin-bottom: 10px; font-size: 24px; }}
            .email {{ color: #666; font-size: 14px; margin-bottom: 20px; word-break: break-all; }}
            input {{
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }}
            input:focus {{
                outline: none;
                border-color: #4CAF50;
            }}
            button {{
                width: 100%;
                padding: 12px;
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
                margin-top: 10px;
            }}
            button:hover {{ background: #45a049; }}
            button:disabled {{
                background: #ccc;
                cursor: not-allowed;
            }}
            .message {{
                padding: 12px;
                margin: 15px 0;
                border-radius: 5px;
                display: none;
            }}
            .success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
            .requirements {{
                font-size: 12px;
                color: #666;
                margin-top: 5px;
                text-align: left;
            }}
            .loader {{
                border: 3px solid #f3f3f3;
                border-top: 3px solid #4CAF50;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                animation: spin 1s linear infinite;
                display: none;
                margin: 0 auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔒 Reset Your Password</h1>
            <p class="email">For: {email}</p>
            
            <div id="message" class="message"></div>
            <div id="loader" class="loader"></div>
            
            <form id="resetForm">
                <input type="password" id="password" placeholder="New Password" required>
                <div class="requirements">
                    • Minimum 8 characters
                </div>
                <input type="password" id="confirmPassword" placeholder="Confirm Password" required>
                <button type="submit" id="submitBtn">Reset Password</button>
            </form>
        </div>
        
        <script>
            const form = document.getElementById('resetForm');
            const submitBtn = document.getElementById('submitBtn');
            const loader = document.getElementById('loader');
            const messageDiv = document.getElementById('message');
            
            form.addEventListener('submit', async (e) => {{
                e.preventDefault();
                
                const password = document.getElementById('password').value;
                const confirmPassword = document.getElementById('confirmPassword').value;
                
                // Hide previous messages
                messageDiv.style.display = 'none';
                
                // Validation
                if (password !== confirmPassword) {{
                    showMessage('Passwords do not match', 'error');
                    return;
                }}
                
                if (password.length < 8) {{
                    showMessage('Password must be at least 8 characters', 'error');
                    return;
                }}
                
                // Show loader
                submitBtn.disabled = true;
                submitBtn.textContent = 'Resetting...';
                loader.style.display = 'block';
                
                try {{
                    const response = await fetch('/api/reset-password', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            token: '{token}',
                            new_password: password
                        }})
                    }});
                    
                    const data = await response.json();
                    
                    if (response.ok && data.success) {{
                        showMessage('✅ Password reset successfully! You can now login with your new password.', 'success');
                        form.style.display = 'none';
                    }} else {{
                        showMessage(data.message || data.detail || 'Failed to reset password', 'error');
                        submitBtn.disabled = false;
                        submitBtn.textContent = 'Reset Password';
                    }}
                }} catch (error) {{
                    showMessage('An error occurred. Please try again.', 'error');
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Reset Password';
                }} finally {{
                    loader.style.display = 'none';
                }}
            }});
            
            function showMessage(text, type) {{
                messageDiv.className = 'message ' + type;
                messageDiv.textContent = text;
                messageDiv.style.display = 'block';
            }}
        </script>
    </body>
    </html>
    """)
# ============= HEALTH CHECK =============

@router.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}