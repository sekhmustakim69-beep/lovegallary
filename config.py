import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
UPLOAD_DIR = BASE_DIR / "uploads" / "photos"

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
	raise RuntimeError("Set SECRET_KEY in your local .env file before starting the app.")
DATABASE_URL = os.getenv("DATABASE_URL", str(INSTANCE_DIR / "love.db"))
DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

UPLOAD_FOLDER = str(UPLOAD_DIR)
DATABASE = DATABASE_URL
