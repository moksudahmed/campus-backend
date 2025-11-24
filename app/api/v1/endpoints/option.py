# app/services/ad_option_service.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.db.session import get_db
from app.models.option import Option
from app.schemas.option import OptionBase, OptionResponse

router = APIRouter()

# ✅ Return a single student
@router.get("/{name}", response_model=OptionResponse)
async def read_student(name: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Option).where(Option.option_name == name)
    result = await db.execute(stmt)
    student = result.scalars().first()  # ✅ .first() instead of .all()
    
    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )
    return student  # ✅ return single object, not list
