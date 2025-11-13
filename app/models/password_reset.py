from sqlalchemy import Column, String, Boolean, DateTime
from app.db.base import Base
from datetime import datetime

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    token = Column(String, primary_key=True, index=True)
    email = Column(String, nullable=False, index=True)
    expiry = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
