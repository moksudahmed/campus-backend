
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RegistrationApplicationDetail(Base):
    __tablename__ = "tbl_osd_registration_application_detail"

    __table_args__ = (
        # ---------------------------------------------
        # UNIQUE CONSTRAINT
        # ---------------------------------------------
        UniqueConstraint(
            "application_id",
            "offeredModuleID",
            name="uq_osd_registration_application_module",
        ),

        # ---------------------------------------------
        # CHECK CONSTRAINTS
        # ---------------------------------------------
        CheckConstraint(
            "apd_credit_hours >= 0",
            name="chk_osd_registration_application_detail_credits",
        ),

        CheckConstraint(
            """
            apd_reg_status IN (
                'Regular',
                'Retake',
                'Retaken',
                'Exempted',
                'Expelled',
                'Improve',
                'Supple',
                'Special-Supple'
            )
            """,
            name="chk_osd_registration_application_detail_reg_status",
        ),

        # ---------------------------------------------
        # INDEXES
        # ---------------------------------------------
        Index(
            "idx_osd_registration_application_detail_application",
            "application_id",
        ),

        Index(
            "idx_osd_registration_application_detail_offeredmodule",
            "offeredModuleID",
        ),

        Index(
            "idx_osd_registration_application_detail_moduleregistration",
            "moduleRegistrationID",
        ),

        {"schema": "public"},

        
    )

    # =================================================
    # PRIMARY KEY
    # =================================================

    application_detail_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # =================================================
    # APPLICATION FOREIGN KEY
    # =================================================

    application_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "public.tbl_os_registration_application.application_id",
            name="fk_osd_registration_application_detail_application",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # =================================================
    # OFFERED MODULE FOREIGN KEY
    # =================================================

    # No ORM ForeignKey: validated through CourseOfferList
    offeredModuleID: Mapped[Optional[int]] = mapped_column(
            "offeredModuleID",
            Integer,
            nullable=True,
        )
    
        # No ORM ForeignKey: database maintains the actual constraint
    moduleRegistrationID: Mapped[Optional[int]] = mapped_column(
            "moduleRegistrationID",
            Integer,
            nullable=True,
        )
    

    # =================================================
    # REGISTRATION STATUS
    # =================================================

    apd_reg_status: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        server_default=text("'Regular'"),
    )

    # =================================================
    # CREDIT HOURS
    # =================================================

    apd_credit_hours: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        server_default=text("0"),
    )

    # =================================================
    # REMARKS
    # =================================================

    apd_detail_remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # =================================================
    # CREATED DATE
    # =================================================

    apd_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
