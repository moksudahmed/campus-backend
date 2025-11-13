from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Numeric
from app.db.base import Base


class ResultFinalExam(Base):
    __tablename__ = "vw_result_final_exam"

    # Composite PK for uniqueness
    student_id = Column("studentID", String, primary_key=True)
    offered_module_id = Column("offeredModuleID", Integer, primary_key=True)
    examination_id = Column("examinationID", Integer, primary_key=True)

    module_code = Column("moduleCode", String)
    mod_name = Column("mod_name", String)
    mod_group = Column("mod_group", String)
    per_name = Column("per_name", String)

    letter_grade = Column("letterGrade", String)
    grade_point = Column("gradePoint", Float)

    exm_exam_term = Column("exm_examTerm", Integer)   # was Integer → must be String (text in PG)
    exm_exam_year = Column("exm_examYear", Integer)
    

    #mark_first_half = Column("markFirstHalf", Numeric)  # changed from Float
    #mark_final = Column("markFinal", Numeric)          # changed from Float
    
    exm_type = Column("exm_type", Integer)            # keep as String

    batch_name = Column("batchName", Integer)
    section_name = Column("sectionName", String)

    tra_term = Column("tra_term", Integer)            # switched to String (likely text)
    tra_year = Column("tra_year", Integer)           # year stays integer

    reg_status = Column("reg_status", String)
    emr_date = Column("emr_date", DateTime)

    check_grade_point = Column("check_grade_point", Float)
    mod_credit_hour = Column("mod_creditHour", Float)
    real_gradepoint = Column("real_gradepoint", Float)

    faculty_id = Column("facultyID", Integer)
    mod_type = Column("mod_type", String)

    """total = Column("total", Float)

    letter_grade = Column("letterGrade", String)
    grade_point = Column("gradePoint", Float)

    

    programme_code = Column("programmeCode", String)
    batch_name = Column("batchName", String)
    section_name = Column("sectionName", String)

    ofm_term = Column("ofm_term", String)            # switched to String (likely text)
    ofm_year = Column("ofm_year", Integer)           # year stays integer
    tra_term = Column("tra_term", String)            # switched to String (likely text)
    tra_year = Column("tra_year", Integer)           # year stays integer

    ex_adm_active = Column("ex_adm_active", Boolean)
    reg_status = Column("reg_status", String)
    emr_date = Column("emr_date", DateTime)
    user_id = Column("userID", Integer)

    check_grade_point = Column("check_grade_point", Float)
    mod_credit_hour = Column("mod_creditHour", Float)
    real_gradepoint = Column("real_gradepoint", Float)

    faculty_id = Column("facultyID", Integer)
    mod_type = Column("mod_type", String)
    term_admission_id = Column("termAdmissionID", Integer)"""
