from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from app.schemas.constants import Status

from typing import Optional
from pydantic import BaseModel, Field


class ApplicationCreate(BaseModel):
    term: int = Field(gt=0, le=32767)
    year: int = Field(gt=0, le=32767)

    student_remarks: Optional[str] = Field(
        default=None,
        max_length=10000,
    )
    application_type: int
    
class ApplicationUpdate(BaseModel):
    student_remarks: Optional[str] = Field(
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
    apl_student_remarks: Optional[str]
    apl_reviewer_remarks: Optional[str]
    apl_submitted_at: Optional[datetime]
    apl_reviewed_by: Optional[str]
    apl_reviewed_at: Optional[datetime]
    apl_registration_completed_at: Optional[datetime]
    apl_created_at: datetime
    apl_updated_at: datetime
    apl_application_type: int = Field(default=1, gt=0)

class RegistrationApplicationOut(BaseModel):
    application_id: int
    application_no: str
    studentID: str
    apl_term: int
    apl_year: int
    apl_application_status: str
    apl_total_credit_hours: Optional[float]
    apl_student_remarks: Optional[str]
    apl_submitted_at: Optional[datetime]
    apl_created_at: Optional[datetime]
    apl_application_type: int = Field(default=1, gt=0)

    model_config = ConfigDict(from_attributes=True)

class ApplicationDetailOut(ApplicationOut):
    details: List["DetailOut"] = Field(
        default_factory=list
    )

class RegistrationApplicationDetailCreate(BaseModel):
    offeredModuleID: Optional[int] = Field(default=None, gt=0)
    moduleRegistrationID: Optional[int] = Field(default=None, gt=0)

    credit_hours: Optional[Decimal] = Field(default=None, ge=0)

    apd_detail_remarks: Optional[str] = None
    apd_reg_status: Optional[str] = None

from app.schemas.registration_application_detail import DetailOut

ApplicationDetailOut.model_rebuild()