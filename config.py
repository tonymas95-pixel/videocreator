import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Директории
    TEMP_DIR = "/app/temp"
    RESULTS_DIR = "/app/results"
    CACHE_DIR = "/app/cache"
    
    # База данных
    DB_FILE = "/app/bot.db"
    
    # Настройки видео
    MAX_VIDEO_DURATION = 120
    OUTPUT_DURATION = 45
    FPS = 24
    RESOLUTION = (1080, 1920)
    
    # Настройки субтитров
    FONT_SIZE = 40
    FONT_COLOR = "white"
    HIGHLIGHT_COLOR = "#FF3366"

# Для обратной совместимости
DB_FILE = Config.DB_FILE
DATABASE_SETTINGS = {"db_file": Config.DB_FILE}
