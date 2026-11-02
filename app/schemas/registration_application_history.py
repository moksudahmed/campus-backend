from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    history_id: int
    application_id: int
    aph_previous_status: str | None
    aph_new_status: str
    aph_action_type: str
    aph_action_by: str
    aph_action_by_role: str | None
    aph_action_remarks: str | None
    aph_action_metadata: dict[str, Any]
    aph_action_at: datetime