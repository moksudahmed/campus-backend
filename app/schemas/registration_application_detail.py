from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DetailCreate(BaseModel):
    offered_module_id: int = Field(gt=0)
    credit_hours: Decimal = Field(
        ge=0,
        max_digits=5,
        decimal_places=2,
    )
    remarks: str | None = Field(
        default=None,
        max_length=5000,
    )


class DetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_detail_id: int
    application_id: int
    offeredModuleID: int
    apd_credit_hours: Decimal
    apd_detail_remarks: str | None
    apd_created_at: datetime