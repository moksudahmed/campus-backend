from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "tbl_o_student_user"

    student_id = Column("studentID", String, primary_key=True)
    #student_id = Column("studentID", String(15), ForeignKey("tbl_o_student.studentID", onupdate="CASCADE", ondelete="NO ACTION"), primary_key=True)    
    login_id = Column("loginID", String(200), nullable=False, unique=True, index=True)   
    is_active = Column("usr_active", Boolean, nullable=False, default=True)
    usr_otp = Column(String(200))
    usr_otp_expire = Column("usr_otpExpire", Integer)    
    usr_last_login_ip = Column("usr_lastLoginIP", String(20))
    usr_last_login_mac = Column("usr_lastLoingMAC", String(20))
    usr_login_log = Column("usr_loginLog", JSON)
    usr_last_login_at = Column("usr_lastLoginAt", Integer)
    hash_password = Column(String(200))

    # Relationship to Student
    #student = relationship("Student", back_populates="student_user")

    """def __repr__(self):
        return f"<StudentUser(student_id={self.student_id}, login_id='{self.login_id}', active={self.is_active})>"" """
