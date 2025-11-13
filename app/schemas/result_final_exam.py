from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class FormatedResultSchema(BaseModel):
    #student_id: str
    offered_module_id: int
    #examination_id: int

    module_code: Optional[str]
    mod_name: Optional[str]
    mod_group: Optional[str]
    per_name: Optional[str]

    
    letter_grade: Optional[str]
    grade_point: Optional[Decimal]

    exm_exam_term: Optional[str]
    exm_exam_year: Optional[int]
    exm_type: Optional[str]

    batch_name: Optional[str]
    section_name: Optional[str]

    tra_term: Optional[str]
    tra_year: Optional[int]

    reg_status: Optional[str]
    emr_date: Optional[datetime]

    check_grade_point: Optional[Decimal]
    mod_credit_hour: Optional[Decimal]
    real_gradepoint: Optional[Decimal]

    faculty_id: Optional[int]
    mod_type: Optional[str]

class ResultFinalExamSchema(BaseModel):
    #student_id: str
    offered_module_id: int
    #examination_id: int

    module_code: Optional[str]
    mod_name: Optional[str]
    mod_group: Optional[str]
    per_name: Optional[str]

    
    letter_grade: Optional[str]
    grade_point: Optional[Decimal]

    exm_exam_term: Optional[int]
    exm_exam_year: Optional[int]
    exm_type: Optional[int]

    batch_name: Optional[int]
    section_name: Optional[str]

    tra_term: Optional[int]
    tra_year: Optional[int]

    reg_status: Optional[str]
    emr_date: Optional[datetime]

    check_grade_point: Optional[Decimal]
    mod_credit_hour: Optional[Decimal]
    real_gradepoint: Optional[Decimal]

    faculty_id: Optional[int]
    mod_type: Optional[str]

    #mark_first_half: Optional[Decimal]
    #mark_final: Optional[Decimal]
    """ total: Optional[Decimal]
    letter_grade: Optional[str]
    grade_point: Optional[Decimal]

    exm_exam_term: Optional[str]
    exm_exam_year: Optional[int]
    exm_type: Optional[str]

    programme_code: Optional[str]
    batch_name: Optional[str]
    section_name: Optional[str]
    ofm_term: Optional[str]
    ofm_year: Optional[int]
    tra_term: Optional[str]
    tra_year: Optional[int]
    ex_adm_active: Optional[bool]
    reg_status: Optional[str]
    emr_date: Optional[datetime]
    user_id: Optional[int]
    check_grade_point: Optional[Decimal]
    mod_credit_hour: Optional[Decimal]
    real_gradepoint: Optional[Decimal]
    faculty_id: Optional[int]
    mod_type: Optional[str]
    term_admission_id: Optional[int]"""

    class Config:
        orm_mode = True
        json_encoders = {
            Decimal: float  # Convert Decimal to float when returning JSON
        }
