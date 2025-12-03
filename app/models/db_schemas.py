from beanie import Document
from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from enum import Enum


# -------------------------------------------------------
# Allow "Open" status because UI sends it
# -------------------------------------------------------
class ComplaintStatus(str, Enum):
    OPEN = "open"                     # <-- ADDED
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    PENDING = "Pending"
    CLOSED = "Closed"


class ComplaintDetails(BaseModel):
    complaint_details: str
    status: str = "Pending"       # Allow any value, no ENUM limit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_to: Optional[str] = None



class Complaint(Document):
    name: str = Field(...)
    mobile_number: str = Field(..., min_length=10, max_length=10)

    # complaint_id → ComplaintDetails
    complaints: Dict[str, ComplaintDetails] = Field(...)

    class Settings:
        name = "complaints"
