from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ALLOWED_REG_STATUSES = {
    "Regular",
    "Retake",
    "Retaken",
    "Exempted",
    "Expelled",
    "Improve",
    "Supple",
    "Special-Supple"
}


class DetailCreate(BaseModel):
    offeredModuleID: int | None = Field(default=None, gt=0)

    moduleRegistrationID: int | None = Field(default=None, gt=0)    

    apd_reg_status: str = Field(
        default="Regular",
        max_length=10,
    )

    apd_credit_hours: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        max_digits=5,
        decimal_places=2,
    )

    apd_detail_remarks: str | None = Field(
        default=None,
        max_length=5000,
    )

    @model_validator(mode="after")
    def validate_detail(self):
        if (
            self.offeredModuleID is None
            and self.moduleRegistrationID is None
        ):
            raise ValueError(
                "Either offeredModuleID or moduleRegistrationID is required."
            )

        if self.apd_reg_status not in ALLOWED_REG_STATUSES:
            raise ValueError(
                f"Invalid registration status. Allowed values: "
                f"{', '.join(sorted(ALLOWED_REG_STATUSES))}"
            )

        return self


class DetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_detail_id: int
    application_id: int

    offeredModuleID: int | None
    moduleRegistrationID: int | None
    
    apd_reg_status: str

    apd_credit_hours: Decimal
    apd_detail_remarks: str | None

    apd_created_at: datetime