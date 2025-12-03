from beanie import Document
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class User(Document):
    name: str = Field(..., description="Full Name")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Hashed password")
    role: str = Field(default="user", description="Role: user/admin")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"   # MongoDB collection name


# For registration input
class RegisterUser(BaseModel):
    name: str
    email: EmailStr
    password: str


# For login input
class LoginUser(BaseModel):
    email: EmailStr
    password: str

# ===============================
#  USER INPUT MODELS
# ===============================

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ===============================
#  USER DATABASE MODEL (Beane)
# ===============================

class UserInDB(Document):
    name: str
    email: EmailStr
    hashed_password: str
    role: str = "user"   # default role
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "users"