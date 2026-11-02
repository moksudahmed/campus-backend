from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.constants import STATUSES_SQL


class RegistrationApplication(Base):
    __tablename__ = "tbl_os_registration_application"

    __table_args__ = (
        CheckConstraint(
            f"apl_application_status IN ({STATUSES_SQL})",
            name="chk_os_registration_application_status",
        ),
        CheckConstraint(
            "apl_total_credit_hours >= 0",
            name="chk_os_registration_application_credits",
        ),
        CheckConstraint(
            "apl_term > 0",
            name="chk_os_registration_application_term",
        ),
        CheckConstraint(
            "apl_year > 0",
            name="chk_os_registration_application_year",
        ),
        CheckConstraint(
            "BTRIM(application_no) <> ''",
            name="chk_os_registration_application_no",
        ),
        Index(
            "uq_os_registration_application_active",
            "studentID",
            "apl_term",
            "apl_year",
            unique=True,
            postgresql_where=text(
                "apl_application_status IN "
                "('DRAFT','SUBMITTED','UNDER_REVIEW','CHANGES_REQUESTED')"
            ),
        ),
        {"schema": "public"},
    )

    application_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True
    )
    application_no: Mapped[str] = mapped_column(
        String(30), nullable=False, unique=True
    )
    studentID: Mapped[str] = mapped_column(
        "studentID",
        String(15),
        ForeignKey(
            "public.tbl_o_student.studentID",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    apl_term: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    apl_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    apl_application_status: Mapped[str] = mapped_column(
        String(25),
        nullable=False,
        server_default=text("'DRAFT'"),
    )
    apl_total_credit_hours: Mapped[Decimal] = mapped_column(
        Numeric(7, 2),
        nullable=False,
        server_default=text("0"),
    )
    apl_student_remarks: Mapped[str | None] = mapped_column(Text)
    apl_reviewer_remarks: Mapped[str | None] = mapped_column(Text)
    apl_submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    apl_reviewed_by: Mapped[str | None] = mapped_column(String(100))
    apl_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    apl_registration_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    apl_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    apl_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
