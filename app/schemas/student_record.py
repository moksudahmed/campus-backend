from pydantic import BaseModel
from datetime import date
from typing import Optional


class StudentRecordSchema(BaseModel):
    student_id: Optional[str]
    personID:  Optional[int]
    per_name: Optional[str]
    per_gender: Optional[str]
    per_dateOfBirth: Optional[date]
    per_bloodGroup: Optional[str]
    per_fathersName: Optional[str]
    per_mothersName: Optional[str]
    per_presentAddress: Optional[str]
    per_mobile: Optional[str]
    stu_academicTerm: Optional[int]
    stu_academicYear: Optional[int]
    pro_name: Optional[str]
    pro_shortName: Optional[str]
    batchName: Optional[int]
    sectionName: Optional[str]
    adm_date: Optional[date]
    programmeCode: Optional[str]
    per_permanentAddress: Optional[str]
    stu_guardiansMobile: Optional[str]
    per_nationality: Optional[str]
    pro_officialName: Optional[str]
    per_title: Optional[str]
    dpt_officalNameforCertificate: Optional[str]

    class Config:
        orm_mode = True
