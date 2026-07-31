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
    
    # Настройки видео
    MAX_VIDEO_DURATION = 120  # секунд
    OUTPUT_DURATION = 45  # секунд
    FPS = 24
    RESOLUTION = (1080, 1920)  # 9:16
    
    # Настройки субтитров
    FONT_SIZE = 40
    FONT_COLOR = "white"
    HIGHLIGHT_COLOR = "#FF3366"
