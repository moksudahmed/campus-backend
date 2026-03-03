from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator


# ---------- Base ----------
class AdminUserBase(BaseModel):
    loginID: str
    usr_role: str = "basic-user"
    admin_usr_active: bool = True


# ---------- Create ----------
class AdminUserCreate(AdminUserBase):
    personID: int
    password: str = Field(..., min_length=6)
    loginID: str
    usr_role: str = "basic-user"


# ---------- Update Status ----------
class AdminUserStatusUpdate(BaseModel):
    admin_usr_active: bool


# ---------- Password Reset ----------
class AdminUserPasswordReset(BaseModel):
    password: str = Field(..., min_length=6)


# ---------- Response ----------
class AdminUserResponse(AdminUserBase):
    personID: int

    class Config:
        orm_mode = True

class Login(BaseModel):
    loginID: str
    usr_role: str = "basic-user"
    admin_usr_active: bool = True

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    loginID: str

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

class ChangePasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8)

    @validator("new_password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v