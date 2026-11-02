from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import FastAPI, HTTPException, Query, Request
#from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security import (
    OAuth2PasswordRequestForm,
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from app.core.security import (
    create_access_token,
    verify_password,
    verify_token,
    generate_reset_token,
    get_password_hash,
    get_current_token
)
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.security import create_access_token, verify_password
from app.core.security import generate_reset_token
#from app.utils.email_utils import send_password_reset_email
from app.schemas.auth import Token, UserCreate, UserResponse, UserUpdate, RoleAssignRequest, ResetPasswordRequest, StandardResponse, ResetEmailRequest
from app.models.user import User as UserModel
from app.db.session import get_db
from app.core.security import get_password_hash
import bcrypt
from typing import List
from fastapi.responses import HTMLResponse, JSONResponse
from app.services.PasswordResetService import PasswordResetService
from sqlalchemy import delete
from app.models.personal_access_tokens import PersonalAccessToken
#from app.services.create_and_send_otp import otp_service
from app.services.otp_service import create_and_send_otp, verify_student_otp
from app.models.otp_model import VerifyOTPRequest
import secrets
import time
from pwdlib import PasswordHash




router = APIRouter()
security = HTTPBearer()

# --------------------
# Helper: Password hashing
# --------------------
"""def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password.decode("utf-8")"""


# --------------------
# Auth Routes
# --------------------

@router.post("/login")
async def login_for_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    Authenticate a student and initiate email OTP verification.

    Expected request:
        Content-Type: application/x-www-form-urlencoded
        username=<student_id>
        password=<password>
    """

    # ------------------------------------------------------------
    # 1. Validate input
    # ------------------------------------------------------------
    student_id = (form_data.username or "").strip()
    password = form_data.password or ""

    if not student_id or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student ID and password are required.",
        )

    # ------------------------------------------------------------
    # 2. Find student account
    # ------------------------------------------------------------
    stmt = select(UserModel).where(
        UserModel.student_id == student_id
    )

    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # IMPORTANT: Check for None before accessing user attributes.
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Student ID not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ------------------------------------------------------------
    # 3. Verify password
    # ------------------------------------------------------------
    if not verify_password(password, user.hash_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ------------------------------------------------------------
    # 4. Get registered email
    # ------------------------------------------------------------
    student_email = user.login_id

    if not student_email or not student_email.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email address is registered for this student.",
        )

    student_email = student_email.strip()

    # ------------------------------------------------------------
    # 5. Generate and send OTP
    # ------------------------------------------------------------
    otp_result = await create_and_send_otp(
        db=db,
        student_id=user.student_id,
        email=student_email,
    )

    if not otp_result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=otp_result.get(
                "message",
                "Unable to send the verification code.",
            ),
        )

    # ------------------------------------------------------------
    # 6. Return OTP challenge
    # ------------------------------------------------------------
    return {
        "success": True,
        "requires_otp": True,
        "student_id": user.student_id,
        "email": student_email,
        "expires_in": otp_result["expires_in"],
        "message": (
            "A verification code has been sent "
            "to your registered email address."
        ),
    }
    """if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Student ID not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(
        form_data.password,
        user.hash_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    """
    
    # ------------------------------------------------------------
    # Create access token
    # ------------------------------------------------------------

    """access_token = await create_access_token(
        db,
        form_data.username,
        name="login",
        abilities="['student-login']",
    )"""

    # ------------------------------------------------------------
    # Return authentication response
    # ------------------------------------------------------------
    
    """return {
        "access_token": access_token,
        "token_type": "bearer",
        "student_id": user.student_id,
        "email": user.login_id,
    }"""



@router.post("/verify-otp")
async def verify_otp_login(
    payload: VerifyOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    student_id = payload.student_id.strip()
    otp = payload.otp.strip()
    print(otp)
    if not student_id or not otp:
        raise HTTPException(
            status_code=422,
            detail="Student ID and OTP are required.",
        )

    # 1. Verify the OTP.
    # This helper should raise HTTPException for an invalid,
    # expired, or already-used OTP.
    await verify_student_otp(
        db=db,
        student_id=student_id,
        otp=otp,
    )
    
    # 2. Confirm the student account exists.
    result = await db.execute(
        select(UserModel).where(
            UserModel.student_id == student_id
        )
    )

    student_user = result.scalar_one_or_none()

    if student_user is None:
        raise HTTPException(
            status_code=404,
            detail="Student account not found.",
        )

    # 3. Create tokens only after OTP verification succeeds.
    access_token = await create_access_token(
        db=db,
        user_id=student_id,
        name="student-access-token",
        abilities="['student-login']",
    )

    """refresh_token = await create_refresh_token(
        db=db,
        student_id=student_id,
    )"""

    # 4. Update login information.
    student_user.usr_lastLoginAt = int(time.time())

    forwarded_for = request.headers.get("X-Forwarded-For")

    client_ip = (
        forwarded_for.split(",")[0].strip()
        if forwarded_for
        else request.client.host if request.client else None
    )

    if client_ip:
        student_user.usr_lastLoginIP = client_ip[:20]

    await db.commit()

    # 5. Return tokens in the format expected by the frontend.
    return {
        "success": True,
        "message": "Login successful.",
        "access_token": access_token,
        "refresh_token": access_token,
        "token_type": "bearer",
        "student_id": student_id,
    }


@router.post("/resend-otp")
async def resend_otp(
    payload: ResendOTPRequest,
    db: AsyncSession = Depends(get_db),
):

    student_id = payload.student_id.strip()

    result = await db.execute(
        select(
            StudentUser,
            Student.email,
        )
        .join(
            Student,
            Student.studentID
            == StudentUser.studentID,
        )
        .where(
            StudentUser.studentID
            == student_id
        )
    )

    row = result.first()

    if row is None:

        raise HTTPException(
            status_code=400,
            detail="Invalid verification request.",
        )

    student_user, email = row

    if not student_user.usr_active:

        raise HTTPException(
            status_code=403,
            detail="Your account is inactive.",
        )

    if not email:

        raise HTTPException(
            status_code=400,
            detail=(
                "No registered email address "
                "is available."
            ),
        )

    result = await resend_student_otp(
        db=db,
        student_id=student_id,
        email=email,
    )

    return {
        "success": True,

        "message":
            "A new verification code has been sent.",

        "email":
            result["email"],

        "expires_in":
            result["expires_in"],
    }

@router.post("/logout")
async def logout(
    token_record=Depends(get_current_token),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    Logout the currently authenticated user.
    """

    token = credentials.credentials

    # Remove the current token from database
    hashed_token = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    await db.execute(
        delete(PersonalAccessToken).where(
            PersonalAccessToken.token == hashed_token
        )
    )

    await db.commit()

    return {
        "success": True,
        "message": "Logged out successfully",
    }
# --------------------
# User CRUD
# --------------------
@router.post("/create-user", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    db_user = UserModel(
        person_id=user.student_id,
        login_id=user.login_id,
        usr_password=hashed_password,       
        usr_active=True,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    db_user = UserModel(
        person_id=user.student_id,
        login_id=user.login_id,
        hash_password = hashed_password,        
        usr_active=True,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.post("/batch-register", response_model=UserResponse)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserModel))

    hashed_password = get_password_hash('12345678')
    db_user = UserModel(
        person_id=user.student_id,
        login_id=user.login_id,
        hash_password = hashed_password,        
        usr_active=True,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.put("/update-user/{student_id}", response_model=UserResponse)
async def update_user(student_id: str, user_update: UserUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserModel).where(UserModel.student_id == student_id))
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_update.login_id:
        db_user.login_id = user_update.login_id
    if user_update.password:
        db_user.hash_password = get_password_hash(user_update.password)   
    if user_update.is_active is not None:
        db_user.usr_active = user_update.is_active

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.get("/", response_model=List[UserResponse])
async def read_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    stmt = select(UserModel).offset(skip).limit(limit)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return users


@router.post("/assign-role/{student_id}", response_model=UserResponse)
async def assign_role(student_id: str, request: RoleAssignRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserModel).where(UserModel.student_id == student_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.usr_role = request.role
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.post(
    "/change-password/{student_id}",
    response_model=UserResponse
)
async def change_password(
    student_id: str,
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    token_record=Depends(get_current_token),
):
    if str(token_record.tokenable_id) != str(student_id):
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to change this password.",
        )

    result = await db.execute(
        select(UserModel).where(
            UserModel.student_id == student_id
        )
    )

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user.hash_password = get_password_hash(
        request.new_password
    )

    db.add(user)

    await db.commit()
    await db.refresh(user)

    return user

@router.post(
    "/change-email/{student_id}",
    response_model=UserResponse
)
async def change_email(
    student_id: str,
    request: ResetEmailRequest,
    db: AsyncSession = Depends(get_db),
    token_record=Depends(get_current_token),
):
    if str(token_record.tokenable_id) != str(student_id):
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to change this email.",
        )

    result = await db.execute(
        select(UserModel).where(
            UserModel.student_id == student_id
        )
    )

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user.login_id = request.email

    db.add(user)

    await db.commit()
    await db.refresh(user)

    return user


@router.post("/generate-password/{student_id}", response_model=UserResponse)
async def generate_password(student_id: str, request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserModel).where(UserModel.student_id == student_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hash_password = get_password_hash(request.new_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.post("/forgot-password2/{email}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def forgot_password2(email: str, db: AsyncSession = Depends(get_db)):
    """
    Forgot Password Endpoint
    Validates user email and sends a password reset link with a short-lived token.
    """
    try:
        # 🔍 Check if user exists
        result = await db.execute(select(UserModel).where(UserModel.login_id == email))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No user found with the provided email or login ID."
            )

        # 🔐 Generate reset token
        reset_token = generate_reset_token(user.login_id)
        print(reset_token)
        # 📧 Send reset link via email
        #await send_password_reset_email(user.login_id, reset_token)

        return user

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Forgot password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request."
        )


@router.post("/forgot-password/{email}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def forgot_password(email: str, db: AsyncSession = Depends(get_db)):
    # Configuration (use environment variables in production)    
    try:
         # 🔍 Check if user exists
        result = await db.execute(select(UserModel).where(UserModel.login_id == email))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No user found with the provided email or login ID."
            )

        SMTP_SERVER = "smtp.gmail.com"
        SMTP_PORT = 587
        SENDER_EMAIL = "noreply@metrouni.edu.bd"
        SENDER_PASSWORD = "tnhn uwcm cara ozyl"  # Use app password for Gmail
        
        # Initialize service
        reset_service = PasswordResetService(
            smtp_server=SMTP_SERVER,
            smtp_port=SMTP_PORT,
            sender_email=SENDER_EMAIL,
            sender_password=SENDER_PASSWORD
        )
        
        # Send reset email
        email_sent = reset_service.send_reset_email(
            recipient_email=email,
            recipient_name="Khondakar Moksud Ahmed"
        )
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send password reset email."
            )

        return user

        """if success:
            print("\n✓ Email sent successfully!")
        else:
            print("\n✗ Failed to send email.") """

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Forgot password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request."
        )

"""@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password(token: str):
     print(token)
     print("HEllo WOrld")"""

@router.get("/reset-password", response_class=HTMLResponse, tags=["Frontend"])
async def reset_password_page(token: str = Query(..., description="Reset token")):
    """
    Password reset page (HTML form)
    
    This endpoint handles: http://localhost:3000/reset-password?token=xxx
    """
    print(token)
    # Verify token
    email = PasswordResetService.verify_token(token)
    
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



@router.post("/reset-password", response_model=StandardResponse)
async def reset_password(request: ResetPasswordRequest):    
    print("HEllo WOrld from POST")