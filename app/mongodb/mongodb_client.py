from backend.mongodb_service.app.mongodb.db_connections import db

# Motor-style collection handles used by chat_service.auth.routes
complaints_collection = db["complaints"]
users_collection = db["users"]
