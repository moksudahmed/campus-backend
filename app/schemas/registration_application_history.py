from typing import Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel


class HistoryOut(BaseModel):

    history_id: int
    application_id: int

    aph_previous_status: Optional[str] = None
    aph_new_status: str
    aph_action_type: str
    aph_action_by: str

    aph_action_by_role: Optional[str] = None
    aph_action_remarks: Optional[str] = None

    aph_action_metadata: Dict[str, Any]

    aph_action_at: datetime

    class Config:
        orm_mode = True