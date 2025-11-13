from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from app.db.session import get_db
from decimal import Decimal
from app.models.result_final_exam import ResultFinalExam
from app.schemas.result_final_exam import ResultFinalExamSchema, FormatedResultSchema
from app.services.ResultService import ResultService
#router = APIRouter(prefix="/results", tags=["Exam Results"])
router = APIRouter()

# Get all results

"""@router.get("/", response_model=List[ResultFinalExamSchema])
async def read_results(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    stmt = select(ResultFinalExam).offset(skip).limit(limit)
    
    # Execute query asynchronously
    result = await db.execute(stmt)
    results = result.scalars().all()

    return results"""

@router.get("/{student_id}", response_model=List[FormatedResultSchema])
async def get_results_by_student(
    student_id: str,
    db: AsyncSession = Depends(get_db)
):
    service = ResultService(db)    
    results = await service.generate_result(student_id)

    return results
