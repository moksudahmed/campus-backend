from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    CheckConstraint,
    JSON
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class AdminUser(Base):
    __tablename__ = "tbl_o_admin_user"

    personID = Column(
        Integer,
        ForeignKey("tbl_j_person.personID", onupdate="CASCADE"),
        primary_key=True
    )

    loginID = Column(String(200), unique=True, nullable=False)
    usr_role = Column(
        String(50),
        nullable=False,
        default="basic-user"
    )

    admin_usr_active = Column(Boolean, nullable=False, default=True)
    admin_usr_otp = Column(String(200), nullable=True)
    admin_usr_otpExpire = Column(Integer, nullable=True)

    admin_usr_lastLoginIP = Column(String(20), nullable=True)
    admin_usr_lastLoingMAC = Column(String(20), nullable=True)
    admin_usr_loginLog = Column(JSON, nullable=True)
    admin_usr_lastLoginAt = Column(Integer, nullable=True)

    hash_password = Column(String(200), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "usr_role IN ("
            "'admin','super-admin','head','faculty','exam','registry',"
            "'user','admission','coordinator','deo','basic-user'"
            ")",
            name="ck_admin_usr_role"
        ),
    )

    person = relationship("Person", backref="admin_account")
