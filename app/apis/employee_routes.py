from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.mongodb_service.app.mongodb.db_connections import employees_col
from backend.mongodb_service.app.models.db_schemas import Complaint
import bcrypt

employee_router = APIRouter()

# ============================================================
# 1) EMPLOYEE LOGIN
# ============================================================
class EmployeeLogin(BaseModel):
    email: str
    password: str


@employee_router.post("/employee/login")
async def employee_login(data: EmployeeLogin):
    user = await employees_col.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email")

    # Password validation (stored as bcrypt hash string)
    if not bcrypt.checkpw(data.password.encode(), user["password"].encode()):
        raise HTTPException(status_code=401, detail="Invalid password")

    return {
        "status": "ok",
        "email": user["email"],
        "name": user.get("name"),
        "role": "employee",
    }


# ============================================================
# 2) EMPLOYEE – VIEW ASSIGNED TASKS
# ============================================================
class EmployeeTasksRequest(BaseModel):
    email: str


@employee_router.post("/employee/tasks")
async def employee_tasks(data: EmployeeTasksRequest):
    """
    Return all complaints where assigned_to == employee email.
    Used by the Streamlit 'My Tasks' page.
    """
    docs = await Complaint.find_all().to_list()

    tasks = []
    for doc in docs:
        for cid, comp in doc.complaints.items():
            # normalize to dict
            if not isinstance(comp, dict):
                comp = {
                    "complaint_details": getattr(comp, "complaint_details", None),
                    "status": getattr(comp, "status", "Pending"),
                    "created_at": getattr(comp, "created_at", None),
                    "assigned_to": getattr(comp, "assigned_to", None),
                }

            if comp.get("assigned_to") == data.email:
                tasks.append(
                    {
                        "complaint_id": cid,
                        "customer": doc.name,
                        "mobile": doc.mobile_number,
                        "issue": comp.get("complaint_details"),
                        "status": comp.get("status", "Pending"),
                        "created_at": comp.get("created_at"),
                    }
                )

    return tasks


# ============================================================
# 3) EMPLOYEE – UPDATE TASK STATUS
# ============================================================
class EmployeeUpdate(BaseModel):
    complaint_id: str
    status: str


@employee_router.post("/employee/tasks/update")
async def employee_update(payload: EmployeeUpdate):
    """
    Employee changes the status of an assigned complaint.
    This updates the same Complaint document used by admin + customer.
    """
    docs = await Complaint.find_all().to_list()

    for doc in docs:
        if payload.complaint_id in doc.complaints:
            comp = doc.complaints[payload.complaint_id]

            # normalize to dict
            if not isinstance(comp, dict):
                comp = {
                    "complaint_details": getattr(comp, "complaint_details", None),
                    "status": getattr(comp, "status", "Pending"),
                    "created_at": getattr(comp, "created_at", None),
                    "assigned_to": getattr(comp, "assigned_to", None),
                }

            comp["status"] = payload.status

            doc.complaints[payload.complaint_id] = comp
            await doc.save()

            return {"status": "ok"}

    raise HTTPException(status_code=404, detail="Complaint not found")


# ============================================================
# 4) ADMIN – CREATE EMPLOYEE
# ============================================================
class EmployeeCreate(BaseModel):
    name: str
    email: str
    password: str


@employee_router.post("/employee/create")
async def create_employee(data: EmployeeCreate):
    """
    Create employee with bcrypt-hashed password.
    Can be called from Swagger.
    """
    exists = await employees_col.find_one({"email": data.email})
    if exists:
        raise HTTPException(status_code=400, detail="Employee already exists")

    hashed_pw = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()

    new_emp = {
        "name": data.name,
        "email": data.email,
        "password": hashed_pw,
        "assigned_tasks": [],
    }

    await employees_col.insert_one(new_emp)

    return {"message": "Employee Created", "email": data.email}


# ============================================================
# 5) LIST ALL EMPLOYEES – for admin dropdown
# ============================================================
@employee_router.get("/employees/list")
async def list_employees():
    employees = await employees_col.find({}).to_list(None)

    result = []
    for emp in employees:
        result.append(
            {
                "id": str(emp["_id"]),
                "name": emp.get("name"),
                "email": emp.get("email"),
            }
        )

    return result
