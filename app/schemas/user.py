from pydantic import BaseModel
from typing import List
from pydantic import BaseModel, EmailStr
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from pydantic import BaseModel

class UserResponse(BaseModel):
    #id: int
    student_id: str
    username: str
    email: str
    is_active: bool
    is_superuser: bool
    #role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes=True

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    #role: str

class User(UserBase):
    student_id: str
    is_active: bool
    is_superuser: bool
    #role: str

    class Config:
        orm_mode = True
