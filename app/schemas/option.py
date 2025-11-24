# app/schemas/option.py

from pydantic import BaseModel
from typing import Optional

class OptionBase(BaseModel):
    option_name: str
    option_value: Optional[str] = None
    auto_load: Optional[bool] = False
    option_group: Optional[str] = None


class OptionResponse(OptionBase):
    option_id: int

    class Config:
        from_attributes = True
