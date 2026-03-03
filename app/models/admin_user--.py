from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class AdminUser(Base):
    __tablename__ = "tbl_y_user"

    personID = Column(Integer, ForeignKey("tbl_j_person.personID", onupdate="CASCADE"), primary_key=True)
    loginID = Column(String(200), nullable=False)
    usr_password = Column(String(200), nullable=True)
    hash_password = Column(String(200), nullable=True)
    usr_role = Column(String(50), nullable=False, default="faculty")
    usr_active = Column(Boolean, nullable=False, default=True)
    usr_otp = Column(String(200), nullable=True)
    usr_otpExpire = Column(Integer, nullable=True)
    usr_resetToken = Column(String(200), nullable=True)
    usr_resetTokenExpire = Column(Integer, nullable=True)
    usr_lastLoginIP = Column(String(20), nullable=True)
    usr_lastLoingMAC = Column(String(20), nullable=True)
    usr_loginLog = Column(JSON, nullable=True)
    usr_lastLoginAt = Column(Integer, nullable=True)

    # Relationship to Person table
    person = relationship("Person", back_populates="user")

    __table_args__ = (
        CheckConstraint(
            "usr_role IN ('admin','super-admin','head','faculty','exam','registry','user','admission','coordinator','deo','basic-user')",
            name="ck_usr_role"
        ),
    )
