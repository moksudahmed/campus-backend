from sqlalchemy import Column, String, Boolean, DateTime
from app.db.base import Base
from datetime import datetime
from sqlalchemy import BigInteger, Text


class PersonalAccessToken(Base):
    __tablename__ = "personal_access_tokens"

    id = Column(BigInteger, primary_key=True, index=True)
    tokenable_type = Column(String(255), nullable=False)
    tokenable_id = Column(String(255), nullable=False)
    name = Column(Text, nullable=False)
    token = Column(String(64), unique=True, nullable=False)
    abilities = Column(Text)
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
