# app/models/option.py

from sqlalchemy import Column, Integer, String, Text, Boolean
from app.db.base import Base


class Option(Base):
    __tablename__ = "tbl_ad_options"

    option_id = Column("optionID", Integer, primary_key=True, index=True)
    option_name = Column(String(200), unique=True, nullable=False, index=True)
    option_value = Column(Text, nullable=True)
    auto_load = Column(Boolean, default=False)
    option_group = Column(String(200), nullable=True)

