from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class AdminUserBase(BaseModel):
    loginID: str
    usr_role: Optional[str] = "faculty"
    usr_active: Optional[bool] = True

class AdminUserCreate(AdminUserBase):
    usr_password: Optional[str] = None
    hash_password: Optional[str] = None
    usr_otp: Optional[str] = None
    usr_otpExpire: Optional[int] = None
    usr_resetToken: Optional[str] = None
    usr_resetTokenExpire: Optional[int] = None
    usr_lastLoginIP: Optional[str] = None
    usr_lastLoingMAC: Optional[str] = None
    usr_loginLog: Optional[Dict[str, Any]] = None
    usr_lastLoginAt: Optional[int] = None

class AdminUserResponse(AdminUserBase):
    personID: int
    usr_password: Optional[str] = None
    hash_password: Optional[str] = None
    usr_otp: Optional[str] = None
    usr_otpExpire: Optional[int] = None
    usr_resetToken: Optional[str] = None
    usr_resetTokenExpire: Optional[int] = None
    usr_lastLoginIP: Optional[str] = None
    usr_lastLoingMAC: Optional[str] = None
    usr_loginLog: Optional[Dict[str, Any]] = None
    usr_lastLoginAt: Optional[int] = None

    class Config:
        orm_mode = True

class AdminUserResponse(AdminUserBase):
    personID: Optional[int] = None
    loginID: Optional[str] = None    
    usr_active: Optional[bool] = None

    class Config:
        orm_mode = True