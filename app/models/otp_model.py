from pydantic import BaseModel, ConfigDict, Field


class VerifyOTPRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    student_id: str = Field(
        ...,
        min_length=1,
        description="Student ID requesting OTP verification",
    )

    otp: str = Field(
        ...,
        min_length=1,
        description="One-time password sent to the student",
    )