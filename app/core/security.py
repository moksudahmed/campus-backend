from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import secrets
import hashlib
from datetime import datetime, timedelta
from app.models.personal_access_tokens import PersonalAccessToken
from fastapi import HTTPException
from sqlalchemy import delete
from jose import jwt



# to get a string like this run: openssl rand -hex 32
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 3

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

"""def get_password_hash(password):
    return pwd_context.hash(password)"""

def get_password_hash(password):
    password = password[:72]
    return pwd_context.hash(password)

def create_access_token2(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def create_access_token(
    db: AsyncSession,
    user_id: str,
    name: str = "access-token",
    abilities: str = None,
    expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES,
) -> str:
    """
    Generate a secure API access token, store it in personal_access_tokens,
    delete old tokens for the same user, and return the raw token.
    """

    try:
        # --------------------------------------------------
        # 1️⃣ Generate secure raw token
        # --------------------------------------------------
        raw_token = secrets.token_urlsafe(40)
        

        # Hash token before storing (like Laravel Sanctum)
        hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()

        # --------------------------------------------------
        # 2️⃣ Set expiration time
        # --------------------------------------------------
        expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)

        # --------------------------------------------------
        # 3️⃣ Remove previous tokens for this user
        # --------------------------------------------------
        await db.execute(
            delete(PersonalAccessToken).where(
                PersonalAccessToken.tokenable_id == str(user_id)
            )
        )

        # --------------------------------------------------
        # 4️⃣ Insert new access token row
        # --------------------------------------------------
        new_token = PersonalAccessToken(
            tokenable_type="User",
            tokenable_id=str(user_id),
            name=name,
            token=hashed_token,        # Secure hashed token
            abilities=abilities,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        db.add(new_token)

        # Guarantees the row exists before commit
        await db.flush()
        await db.refresh(new_token)

        # --------------------------------------------------
        # 5️⃣ Commit the transaction
        # --------------------------------------------------
        await db.commit()

        # --------------------------------------------------
        # Return raw token (only user sees this)
        # --------------------------------------------------
        return raw_token

    except Exception as e:
        await db.rollback()
        print("❌ ERROR generating access token:", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate access token.",
        )

def generate_reset_token(email: str) -> str:
    """
    Generate a short-lived JWT token for password reset.
    """
    expire = datetime.utcnow() + timedelta(minutes=15)  # Token valid for 15 minutes
    payload = {"sub": email, "exp": expire, "scope": "password_reset"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_reset_token(token: str) -> str | None:
    """
    Verify a password reset token and return email if valid.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("scope") != "password_reset":
            return None
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None