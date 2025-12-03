from fastapi import APIRouter, HTTPException
from backend.mongodb_service.app.models.users_model import User, RegisterUser, LoginUser
from passlib.context import CryptContext

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -----------------------------
# REGISTER USER
# -----------------------------
@router.post("/users/register")
async def register_user(data: RegisterUser):

    existing = await User.find_one(User.email == data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = pwd_context.hash(data.password)

    user = User(
        name=data.name,
        email=data.email,
        password=hashed_pw,
        role="user"
    )

    await user.insert()

    return {"message": "User registered successfully"}


# -----------------------------
# LOGIN USER
# -----------------------------
@router.post("/users/login")
async def login_user(data: LoginUser):

    user = await User.find_one(User.email == data.email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not pwd_context.verify(data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    return {
        "message": "Login successful",
        "user_id": str(user.id),
        "role": user.role
    }
