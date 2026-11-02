from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RegistrationApplicationDetail(Base):
    __tablename__ = "tbl_osd_registration_application_detail"

    __table_args__ = (
        UniqueConstraint(
            "application_id",
            "offeredModuleID",
            name="uq_osd_registration_application_module",
        ),
        CheckConstraint(
            "apd_credit_hours >= 0",
            name="chk_osd_registration_application_detail_credits",
        ),
        {"schema": "public"},
    )

    application_detail_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True
    )
    application_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "public.tbl_os_registration_application.application_id",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    offeredModuleID: Mapped[int] = mapped_column(
        "offeredModuleID",
        Integer,
        ForeignKey(
            "public.tbl_h_offeredmodule.offeredModuleID",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    apd_credit_hours: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        server_default=text("0"),
    )
    apd_detail_remarks: Mapped[str | None] = mapped_column(Text)
    apd_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
