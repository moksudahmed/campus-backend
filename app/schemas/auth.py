from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator

# --------------------
# Token Schema
# --------------------
class Token(BaseModel):
    access_token: str
    token_type: str
    #usr_role: str
    student_id: str
    email: str


# --------------------
# User Schemas
# --------------------
class UserCreate(BaseModel):
    student_id: str
    login_id: str
    password: str
    #usr_role: Optional[str] = "faculty"


class UserUpdate(BaseModel):
    login_id: Optional[str] = None
    password: Optional[str] = None
    #usr_role: Optional[str] = None
    is_active: Optional[bool] = None
    usr_otp: Optional[str] = None
    usr_otp_expire: Optional[int] = None
    usr_reset_token: Optional[str] = None
    usr_reset_token_expire: Optional[int] = None
    usr_last_login_ip: Optional[str] = None
    usr_last_login_mac: Optional[str] = None
    usr_last_login_at: Optional[int] = None


class UserInDB(BaseModel):
    student_id: str
    login_id: str
    #usr_role: str
    is_active: bool

    class Config:
        orm_mode = True


class User(BaseModel):
    student_id: str
    login_id: str
    #usr_role: str
    is_active: bool

    class Config:
        orm_mode = True


class UserResponse(BaseModel):
    student_id: str
    login_id: str
    #usr_role: str
    is_active: bool

    class Config:
        orm_mode = True

class StandardResponse(BaseModel):
    success: bool
    message: str
# --------------------
# Role & Password Schemas
# --------------------
class RoleAssignRequest(BaseModel):
    usr_role: str


class ResetPasswordRequest(BaseModel):
    new_password: str



class ForgotPasswordRequest(BaseModel):
    #email: EmailStr
    student_id: str

    """class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }"""


class ResetPasswordRequest(BaseModel):
    #token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    student_id: str

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    """class Config:
        json_schema_extra = {
            "example": {
                "token": "xajOhUeDRor3lb9ETfUOIjE5rdRARMKqpNsWPKIjLBc",
                "new_password": "newSecurePass123"
            }
        }"""


class ResetEmailRequest(BaseModel):
    #token: str = Field(..., min_length=1)
    email: str
    student_id: str
   


class TokenVerifyResponse(BaseModel):
    valid: bool
    message: str
    email: Optional[str] = None


class StandardResponse(BaseModel):
    success: bool
    message: str