from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.models import (
    ResultFinalExam
)
from app.schemas.result_final_exam import ResultFinalExamSchema, FormatedResultSchema

class ResultService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_result(self, student_id:str) -> FormatedResultSchema:
        stmt = select(ResultFinalExam).where(ResultFinalExam.student_id == student_id)
        result = await self.db.execute(stmt)
        results = result.scalars().all()

        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No results found for student ID {student_id}"
            )
        formated_result = self.prepare_result(results)
        return formated_result
    
    def prepare_result(self, results):
        results_list = []
        for val in results:
            result_dict = {
                "offered_module_id": val.offered_module_id,
                "module_code": val.module_code,
                "mod_name": val.mod_name,
                "mod_group": val.mod_group,
                "per_name": val.per_name,
                "letter_grade": val.letter_grade,
                "grade_point": float(val.grade_point) if val.grade_point is not None else None,
                "exm_exam_term": self.determine_term(val.exm_exam_term),
                "exm_exam_year": val.exm_exam_year,
                "exm_type": self.determine_exam_type(val.exm_type),
                "batch_name": str(val.batch_name) + self.get_batch_name_suffix(val.batch_name),
                "section_name": val.section_name,
                "tra_term": self.determine_term(val.tra_term),
                "tra_year": val.tra_year,
                "reg_status": val.reg_status,
                "emr_date": val.emr_date,
                "check_grade_point": float(val.check_grade_point) if val.check_grade_point is not None else None,
                "mod_credit_hour": float(val.mod_credit_hour) if val.mod_credit_hour is not None else None,
                "real_gradepoint": float(val.real_gradepoint) if val.real_gradepoint is not None else None,
                "faculty_id": val.faculty_id,
                "mod_type": val.mod_type
            }
            results_list.append(result_dict)

        return results_list


    def determine_term(self, term):
        if term ==1:
            return 'Spring'
        elif term ==2:
            return 'Summer'
        elif term == 3:
            return 'Autumn'
        else: 
            return 'Not Specified'
    
    def determine_exam_type(self, type):
        if type == 1:
            return 'final'
        elif type == 2:
            return 'supple'
        elif type == 3:
            return 'special supple'      
    
    def get_batch_name_suffix(self, batch: int) -> str:
        ends = ["th", "st", "nd", "rd", "th", "th", "th", "th", "th", "th"]

        # Special case for 11, 12, 13
        if 11 <= (batch % 100) <= 13:
            return "th"
        else:
            return ends[batch % 10]
