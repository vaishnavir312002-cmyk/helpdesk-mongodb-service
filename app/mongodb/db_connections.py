from datetime import datetime
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from backend.mongodb_service.app.core.config import (
    mongodb_uri,
    mongodb_database
)

from backend.mongodb_service.app.models.db_schemas import Complaint
from backend.mongodb_service.app.models.users_model import UserInDB

import uuid
from bson import ObjectId
from fastapi import HTTPException


# -----------------------------------
# MongoDB Client Setup
# -----------------------------------
client = AsyncIOMotorClient(mongodb_uri)
db = client[mongodb_database]

# Employees collection (for employee login)
employees_col = db["employees"]


# -----------------------------------
# Initialize Beanie ODM
# -----------------------------------
async def init_db():
    await init_beanie(
        database=db,
        document_models=[Complaint, UserInDB]
    )


# -----------------------------------
# Close DB
# -----------------------------------
async def close_db():
    client.close()


# -----------------------------------
# Insert Complaint (New User)
# -----------------------------------
async def insert_in_db(data):
    complaint_id = str(uuid.uuid4())

    # 💡 FIX 1: Always generate datetime
    created_time = datetime.utcnow()

    complaint = Complaint(
        name=data.name,
        mobile_number=data.mobile_number,
        complaints={
            complaint_id: {
                "complaint_details": data.complaints.complaint_details,
                "status": "Pending",
                "assigned_to": None,
                "created_at": created_time,     # FIXED (never None)
            }
        }
    )

    await complaint.insert()

    return {
        "message": "Success",
        "complaint_id": complaint_id
    }


# -----------------------------------
# Check if user exists
# -----------------------------------
async def check_user_exists(mobile_number: str):
    if not mobile_number:
        raise HTTPException(status_code=400, detail="Mobile number missing")

    user = await Complaint.find_one({"mobile_number": mobile_number})
    return str(user.id) if user else False


# -----------------------------------
# Add Complaint (Existing User)
# -----------------------------------
async def add_complaint_to_user(mongo_id: str, new_complaint):
    obj_id = ObjectId(mongo_id)
    complaint_doc = await Complaint.get(obj_id)

    if not complaint_doc:
        raise HTTPException(status_code=404, detail="User complaint document not found")

    complaint_id = str(uuid.uuid4())

    # 💡 FIX 2: Always generate datetime
    created_time = datetime.utcnow()

    complaint_doc.complaints[complaint_id] = {
        "complaint_details": new_complaint.complaints.complaint_details,
        "status": "Pending",
        "assigned_to": None,
        "created_at": created_time,     # FIXED (never None)
    }

    await complaint_doc.save()

    return {
        "message": "New complaint added",
        "complaint_id": complaint_id
    }


# -----------------------------------
# Get Complaint Status
# -----------------------------------
async def get_complaint_status(obj_id: str, complaint_id: str):
    mongo_obj_id = ObjectId(obj_id)
    user = await Complaint.get(mongo_obj_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    complaint = user.complaints.get(complaint_id)

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return {
        "complaint_id": complaint_id,
        "status": complaint.get("status", "Pending"),
        "details": complaint.get("complaint_details"),
        "assigned_to": complaint.get("assigned_to"),
        "created_at": complaint.get("created_at"),
    }
