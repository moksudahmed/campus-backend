from sqlalchemy import Column, String, Integer, Boolean, Float
from app.db.base import Base


class CourseEnrollment(Base):
    __tablename__ = "vw_course_enrollment"  # view name

    moduleRegistration_ID = Column("moduleRegistrationID", Integer, primary_key=True, index=True)
    student_id = Column("studentID", String)
    batch_name = Column("batchName", Integer)
    section_name = Column("sectionName", String)
    tra_term = Column(Integer)
    tra_year = Column(Integer)
    module_code = Column("moduleCode", String)
    mod_name = Column(String)
    mod_credit_hour = Column("mod_creditHour", Float)
    mod_lab_included = Column("mod_labIncluded", Boolean)
    mod_major = Column("mod_mejor", String)   # fixed typo `mejor` → keeping as-is since in DB
    mod_group = Column(String)
    faculty_name = Column(String)
    fac_designation = Column(String)
    dpt_code = Column(String)
    reg_status = Column(String)
    reg_type = Column(Integer)