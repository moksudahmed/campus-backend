from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.constants import STATUSES_SQL


class RegistrationApplicationHistory(Base):
    __tablename__ = "tbl_osh_registration_application_history"

    __table_args__ = (
        CheckConstraint(
            f"aph_new_status IN ({STATUSES_SQL})",
            name="chk_osh_registration_application_history_new_status",
        ),
        CheckConstraint(
            "aph_previous_status IS NULL "
            f"OR aph_previous_status IN ({STATUSES_SQL})",
            name="chk_osh_registration_application_history_previous_status",
        ),
        CheckConstraint(
            "BTRIM(aph_action_type) <> ''",
            name="chk_osh_registration_application_history_action_type",
        ),
        CheckConstraint(
            "BTRIM(aph_action_by) <> ''",
            name="chk_osh_registration_application_history_action_by",
        ),
        Index(
            "idx_osh_registration_application_history_application",
            "application_id",
            text("aph_action_at DESC"),
        ),
        {"schema": "public"},
    )

    history_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True
    )
    application_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "public.tbl_os_registration_application.application_id",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    aph_previous_status: Mapped[str | None] = mapped_column(String(25))
    aph_new_status: Mapped[str] = mapped_column(String(25), nullable=False)
    aph_action_type: Mapped[str] = mapped_column(String(40), nullable=False)
    aph_action_by: Mapped[str] = mapped_column(String(100), nullable=False)
    aph_action_by_role: Mapped[str | None] = mapped_column(String(40))
    aph_action_remarks: Mapped[str | None] = mapped_column(Text)
    aph_action_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    aph_action_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
