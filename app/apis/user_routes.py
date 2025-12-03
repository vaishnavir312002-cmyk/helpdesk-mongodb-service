from fastapi import APIRouter, HTTPException
from backend.mongodb_service.app.models.users_model import UserCreate, UserLogin, UserInDB
from backend.mongodb_service.app.mongodb.db_connections import db
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/register")
async def register_user(user: UserCreate):
    # Check if user exists
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = pwd_context.hash(user.password)

    user_dict = {
        "name": user.name,
        "email": user.email,
        "password": hashed_pw,
        "role": "user"
    }

    result = await db.users.insert_one(user_dict)
    return {"msg": "User created", "id": str(result.inserted_id)}


@router.post("/login")
async def login_user(data: UserLogin):
    user = await db.users.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not pwd_context.verify(data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect password")

    return {
        "msg": "Login successful",
        "user": {
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    }
