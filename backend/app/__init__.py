from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from backend/.env BEFORE anything reads os.environ
# (db.py and config.get_jwt_secret rely on these being present).
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")
