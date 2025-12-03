from fastapi import APIRouter, HTTPException
from datetime import datetime

from backend.mongodb_service.app.models.data_models import (
    RegisterComplaint,
    ComplaintStatus,
)
from backend.mongodb_service.app.mongodb.db_connections import (
    insert_in_db,
    check_user_exists,
    add_complaint_to_user,
    get_complaint_status,
)
from backend.mongodb_service.app.models.db_schemas import Complaint

from pydantic import BaseModel
from typing import List, Any, Dict

mongo_router = APIRouter()

# -----------------------------------------------------------
# Status Mapper
# -----------------------------------------------------------
STATUS_MAP = {
    "open": "Pending",
    "pending": "Pending",
    "in progress": "In Progress",
    "inprogress": "In Progress",
    "resolved": "Resolved",
    "closed": "Closed",
}

def map_status(input_status: str | None):
    if not input_status:
        return "Pending"
    return STATUS_MAP.get(input_status.lower(), "Pending")


# -----------------------------------------------------------
# Register or Add Complaint
# -----------------------------------------------------------
@mongo_router.post("/register-complaint-mongodb/")
async def create_complaint(data: RegisterComplaint):
    if not data.mobile_number:
        raise HTTPException(status_code=400, detail="Missing mobile_number")

    # Check if user exists
    obj_id = await check_user_exists(data.mobile_number)

    # New user → insert fresh document
    if not obj_id:
        return await insert_in_db(data)

    # Existing user → add complaint
    return await add_complaint_to_user(mongo_id=obj_id, new_complaint=data)


# -----------------------------------------------------------
# Check status of a specific complaint
# -----------------------------------------------------------
@mongo_router.post("/check-complaint-status-mongodb/")
async def check_complaint_status(data: ComplaintStatus):
    if not data.mobile_number:
        raise HTTPException(status_code=400, detail="Missing mobile_number")

    obj_id = await check_user_exists(data.mobile_number)
    if not obj_id:
        raise HTTPException(status_code=404, detail="User not found")

    return await get_complaint_status(
        obj_id=obj_id,
        complaint_id=data.complaint_id
    )


# -----------------------------------------------------------
# User – List My Complaints
# -----------------------------------------------------------
class UserComplaintsRequest(BaseModel):
    mobile: str


@mongo_router.post("/user/complaints")
async def list_user_complaints(req: UserComplaintsRequest) -> List[Dict[str, Any]]:
    if not req.mobile:
        raise HTTPException(status_code=400, detail="Missing mobile")

    complaint_doc = await Complaint.find_one({"mobile_number": req.mobile})
    if not complaint_doc:
        return []

    results = []

    for complaint_id, comp in complaint_doc.complaints.items():

        # Normalize document → dict
        if isinstance(comp, dict):
            details = comp
        else:
            details = {
                "complaint_details": getattr(comp, "complaint_details", None),
                "status": map_status(getattr(comp, "status", None)),
                "created_at": getattr(comp, "created_at", None),
            }

        results.append({
            "complaint_id": complaint_id,
            "name": complaint_doc.name,
            "mobile": complaint_doc.mobile_number,
            "issue": details.get("complaint_details"),
            "status": map_status(details.get("status")),
            "created_at": details.get("created_at"),
        })

    return results


# -----------------------------------------------------------
# Admin – List All Complaints (AI-ready)
# -----------------------------------------------------------
@mongo_router.get("/admin/complaints")
async def admin_list_complaints() -> List[Dict[str, Any]]:
    docs = await Complaint.find_all().to_list()
    rows = []

    for doc in docs:
        for complaint_id, comp in doc.complaints.items():

            if isinstance(comp, dict):
                details = comp
            else:
                details = {
                    "complaint_details": getattr(comp, "complaint_details", None),
                    "status": map_status(getattr(comp, "status", None)),
                    "created_at": getattr(comp, "created_at", None),
                }

            status_val = map_status(details.get("status"))

            priority_label = "High" if status_val in ["Pending", "In Progress"] else "Normal"

            rows.append({
                "complaint_id": complaint_id,
                "name": doc.name,
                "mobile": doc.mobile_number,
                "issue": details.get("complaint_details"),
                "status": status_val,
                "created_at": details.get("created_at"),
                "priority_label": priority_label,
            })

    rows.sort(
        key=lambda r: (r.get("created_at") is None, r.get("created_at")),
        reverse=True
    )
    return rows


# -----------------------------------------------------------
# Admin – Update / Assign Complaint
# -----------------------------------------------------------
class AdminUpdateComplaint(BaseModel):
    complaint_id: str
    status: str | None = None
    assigned_to: str | None = None


@mongo_router.post("/admin/complaints/update")
async def admin_update_complaint(payload: AdminUpdateComplaint):

    if not payload.complaint_id:
        raise HTTPException(status_code=400, detail="complaint_id is required")

    docs = await Complaint.find_all().to_list()

    for doc in docs:
        if payload.complaint_id in doc.complaints:

            comp = doc.complaints[payload.complaint_id]

            if not isinstance(comp, dict):
                comp = {
                    "complaint_details": getattr(comp, "complaint_details", None),
                    "status": map_status(getattr(comp, "status", None)),
                    "created_at": getattr(comp, "created_at", None),
                }

            # Update status
            if payload.status:
                comp["status"] = map_status(payload.status)

            # Update assignee
            if payload.assigned_to:
                comp["assigned_to"] = payload.assigned_to

            # Save back
            doc.complaints[payload.complaint_id] = comp
            await doc.save()

            return {"status": "ok", "complaint_id": payload.complaint_id}

    raise HTTPException(status_code=404, detail="Complaint not found")
