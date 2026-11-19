
from decimal import Decimal

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

    dpt_code: Mapped[str | None] = mapped_column(String)

    pro_shortName: Mapped[str | None] = mapped_column(String)

    syllabusCode: Mapped[str | None] = mapped_column(String)

    moduleCode: Mapped[str | None] = mapped_column(String)

    mod_name: Mapped[str | None] = mapped_column(String)

    mod_creditHour: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))

    mod_group: Mapped[str | None] = mapped_column(String)

    mod_type: Mapped[str | None] = mapped_column(String)

    sectionName: Mapped[str | None] = mapped_column(String)

    batchName: Mapped[str | None] = mapped_column(String)

    ofm_term: Mapped[int | None] = mapped_column(SmallInteger)

    ofm_year: Mapped[int | None] = mapped_column(SmallInteger)

    per_title: Mapped[str | None] = mapped_column(String)

    per_name: Mapped[str | None] = mapped_column(String)

    per_mobile: Mapped[str | None] = mapped_column(String)

    fac_designation: Mapped[str | None] = mapped_column(String)

    programmeCode: Mapped[str | None] = mapped_column(String)
