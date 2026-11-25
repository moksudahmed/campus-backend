from typing import Optional
from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    remarks: Optional[str] = Field(
        default=None,
        max_length=10000,
    )