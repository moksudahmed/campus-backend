from sqlalchemy import Column, String, Integer, Date
from app.db.base import Base

class StudentRecord(Base):
    __tablename__ = "vw_student_info"
    #__table_args__ = {"schema": "public"}

    #studentID = Column(String, primary_key=True, index=True)
    student_id = Column("studentID", String, primary_key=True)
    personID = Column(Integer)
    per_name = Column(String)
    per_gender = Column(String(10))
    per_dateOfBirth = Column(Date)
    per_bloodGroup = Column(String(5))
    per_fathersName = Column(String)
    per_mothersName = Column(String)
    per_presentAddress = Column(String)
    per_mobile = Column(String(20))
    stu_academicTerm = Column(Integer)
    stu_academicYear = Column(Integer)
    pro_name = Column(String)
    pro_shortName = Column(String(20))
    batchName = Column(Integer)
    sectionName = Column(String(50))
    adm_date = Column(Date)
    programmeCode = Column(String(20))
    per_permanentAddress = Column(String)
    stu_guardiansMobile = Column(String(20))
    per_nationality = Column(String(50))
    pro_officialName = Column(String)
    per_title = Column(String(20))
    dpt_officalNameforCertificate = Column(String)
