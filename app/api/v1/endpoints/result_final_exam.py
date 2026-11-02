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
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_token

#router = APIRouter(prefix="/results", tags=["Exam Results"])
router = APIRouter()
security = HTTPBearer()
# Get all results

"""@router.get("/", response_model=List[ResultFinalExamSchema])
async def read_results(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    stmt = select(ResultFinalExam).offset(skip).limit(limit)
    
    # Execute query asynchronously
    result = await db.execute(stmt)
    results = result.scalars().all()

    return results"""
@router.get(
    "/{student_id}",
    response_model=List[FormatedResultSchema]
)
async def get_results_by_student(
    student_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    # --------------------------------------------------
    # 1. Get Bearer token
    # --------------------------------------------------
    token = credentials.credentials

    # --------------------------------------------------
    # 2. Verify token
    # --------------------------------------------------
    token_record = await verify_token(
        db=db,
        token=token,
    )

    # --------------------------------------------------
    # 3. Verify token belongs to requested student
    # --------------------------------------------------
    if str(token_record.tokenable_id) != str(student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access these results.",
        )

    # --------------------------------------------------
    # 4. Get results
    # --------------------------------------------------
    service = ResultService(db)

    results = await service.generate_result(student_id)

    return results


@router.get(
    "/current_term_results/{student_id}",
    response_model=List[FormatedResultSchema]
)
async def get_current_term_results_by_student(
    student_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    # --------------------------------------------------
    # 1. Get Bearer token
    # --------------------------------------------------
    token = credentials.credentials

    # --------------------------------------------------
    # 2. Verify token
    # --------------------------------------------------
    token_record = await verify_token(
        db=db,
        token=token,
    )

    # --------------------------------------------------
    # 3. Verify token belongs to requested student
    # --------------------------------------------------
    if str(token_record.tokenable_id) != str(student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access these results.",
        )

    # --------------------------------------------------
    # 4. Get current term results
    # --------------------------------------------------
    service = ResultService(db)

    results = await service.generate_current_term_result(
        student_id
    )

    return results
