import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    TEMP_DIR = "/app/temp"
    RESULTS_DIR = "/app/results"
    CACHE_DIR = "/app/cache"
    DB_FILE = "/app/bot.db"
    
    MAX_FILE_SIZE = 300 * 1024 * 1024  # 300 МБ

DB_FILE = Config.DB_FILE
DATABASE_SETTINGS = {"db_file": Config.DB_FILE}
