from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.constants import Status


class ApplicationCreate(BaseModel):
    term: int = Field(gt=0, le=32767)
    year: int = Field(gt=0, le=32767)
    student_remarks: str | None = Field(
        default=None,
        max_length=10000,
    )


class ApplicationUpdate(BaseModel):
    student_remarks: str | None = Field(
        default=None,
        max_length=10000,
    )


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: int
    application_no: str
    studentID: str
    apl_term: int
    apl_year: int
    apl_application_status: str
    apl_total_credit_hours: Decimal
    apl_student_remarks: str | None
    apl_reviewer_remarks: str | None
    apl_submitted_at: datetime | None
    apl_reviewed_by: str | None
    apl_reviewed_at: datetime | None
    apl_registration_completed_at: datetime | None
    apl_created_at: datetime
    apl_updated_at: datetime


class ApplicationDetailOut(ApplicationOut):
    details: list["DetailOut"] = Field(default_factory=list)


from app.schemas.registration_application_detail import DetailOut

ApplicationDetailOut.model_rebuild()