from fastapi import FastAPI
from contextlib import asynccontextmanager

# DB setup
from backend.mongodb_service.app.mongodb.db_connections import init_db, close_db

# Routers
from backend.mongodb_service.app.apis.mongodb_routes import mongo_router
from backend.mongodb_service.app.apis.user_routes import router as user_router
from backend.mongodb_service.app.apis.users_routes import router as users_router
from backend.mongodb_service.app.apis.employee_routes import employee_router


# ---------------------------------------------------------
# Lifespan – connect DB on startup and close on shutdown
# ---------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


# ---------------------------------------------------------
# Create FastAPI app AFTER defining lifespan
# ---------------------------------------------------------
app = FastAPI(lifespan=lifespan)


# ---------------------------------------------------------
# Register routers NOW (after app creation)
# ---------------------------------------------------------
app.include_router(mongo_router)
app.include_router(user_router)
app.include_router(users_router)
app.include_router(employee_router,prefix="")


# ---------------------------------------------------------
# Health check route
# ---------------------------------------------------------
@app.get("/")
def root():
    return {"msg": "MongoDB Service Running"}


# Run using:
# uvicorn backend.mongodb_service.main:app --reload --port 8001
