from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class CourseEnrollmentSchema(BaseModel):
    moduleRegistration_ID: Optional[int]
    student_id: str
    batch_name: Optional[int]
    section_name: Optional[str]
    tra_term: Optional[int]
    tra_year: Optional[int]
    module_code: Optional[str]
    mod_name: Optional[str]
    mod_credit_hour:  Optional[Decimal]
    mod_lab_included: Optional[bool]
    mod_major: Optional[str]
    mod_group: Optional[str]
    faculty_name: Optional[str]
    fac_designation: Optional[str]
    dpt_code: Optional[str]
    reg_status: Optional[str]
    reg_type: Optional[int]

    class Config:
        orm_mode = True
