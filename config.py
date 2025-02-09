import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
print(f"BOT_TOKEN: {BOT_TOKEN}")  # ADDED: DEBUG
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///manicure.db")
MASTER_TELEGRAM_ID = int(os.getenv("MASTER_TELEGRAM_ID", "0")) # Читаем MASTER_TELEGRAM_ID из .env
