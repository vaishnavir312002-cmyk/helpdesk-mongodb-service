from dotenv import load_dotenv
import os
from pathlib import Path

# ------------------------------------------------------
# ALWAYS LOAD .env FROM PROJECT ROOT
# HelpDesk-Agent-main/.env
# ------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[3]   # 3 levels up
env_path = ROOT_DIR / ".env"
load_dotenv(env_path)

# ----------------------------
# MongoDB connection settings
# ----------------------------
mongodb_host = os.getenv("MONGODB_HOST_TEST", "127.0.0.1")
mongodb_port = os.getenv("MONGODB_PORT_TEST", "27017")
mongodb_database = os.getenv("MONGODB_DATABASE_NAME_TEST", "helpdesk_db")

mongodb_uri = f"mongodb://{mongodb_host}:{mongodb_port}"

# ----------------------------
# Services
# ----------------------------
url_mongodb_service = os.getenv("MONGODB_SERVICE")
url_chat_service = os.getenv("CHAT_SERVICE")

print("💾 Mongo URI =", mongodb_uri)
print("💾 Mongo DB =", mongodb_database)
print("🌐 MongoDB SERVICE =", url_mongodb_service)
