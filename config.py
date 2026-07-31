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
    MAX_FILE_SIZE = 300 * 1024 * 1024  # 300 МБ
    MAX_VIDEO_DURATION = 180  # 3 минуты
    OUTPUT_DURATION = 45  # 45 секунд
    FPS = 24
    RESOLUTION = (1080, 1920)
    
    # Настройки субтитров
    FONT_SIZE = 50
    FONT_COLOR = "white"
    HIGHLIGHT_COLOR = "#FF3366"
    FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

DB_FILE = Config.DB_FILE
DATABASE_SETTINGS = {"db_file": Config.DB_FILE}
