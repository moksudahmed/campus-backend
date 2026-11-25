from decimal import Decimal
from typing import Optional

from sqlalchemy import Integer, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CourseOfferList(Base):
    __tablename__ = "vw_course_offer_list"
    __table_args__ = {"schema": "public"}

    # The view does not declare a primary key.
    # offeredModuleID is used as the ORM identity.
    offeredModuleID: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    dpt_code: Mapped[Optional[str]] = mapped_column(String)

    pro_shortName: Mapped[Optional[str]] = mapped_column(String)

    syllabusCode: Mapped[Optional[str]] = mapped_column(String)

    moduleCode: Mapped[Optional[str]] = mapped_column(String)

    mod_name: Mapped[Optional[str]] = mapped_column(String)

    mod_creditHour: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(7, 2)
    )

    mod_group: Mapped[Optional[str]] = mapped_column(String)

    mod_type: Mapped[Optional[str]] = mapped_column(String)

    sectionName: Mapped[Optional[str]] = mapped_column(String)

    batchName: Mapped[Optional[str]] = mapped_column(String)

    ofm_term: Mapped[Optional[int]] = mapped_column(SmallInteger)

    ofm_year: Mapped[Optional[int]] = mapped_column(SmallInteger)

    per_title: Mapped[Optional[str]] = mapped_column(String)

    per_name: Mapped[Optional[str]] = mapped_column(String)

    per_mobile: Mapped[Optional[str]] = mapped_column(String)

    fac_designation: Mapped[Optional[str]] = mapped_column(String)

    programmeCode: Mapped[Optional[str]] = mapped_column(String)