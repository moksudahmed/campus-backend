from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    remarks: str | None = Field(
        default=None,
        max_length=10000,
    )