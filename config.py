import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
API_ID: int = int(os.getenv("API_ID", "0"))
API_HASH: str = os.getenv("API_HASH", "")
DB_PATH: str = "database.db"

_owner_str = os.getenv("OWNER_IDS", os.getenv("OWNER_ID", ""))
OWNER_IDS: list[int] = [int(x.strip()) for x in _owner_str.split(",") if x.strip().isdigit()]
