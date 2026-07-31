"""
Config для SHORTS BOT v2.0
Простые и понятные настройки
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# TELEGRAM
# ============================================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ============================================================================
# DIRECTORIES
# ============================================================================
BASE_DIR = Path(__file__).parent
TEMP_DIR = BASE_DIR / "temp"
RESULTS_DIR = BASE_DIR / "results"
CACHE_DIR = BASE_DIR / "cache"
LOG_FILE = BASE_DIR / "bot.log"

# Создаём директории если не существуют
for dir_path in [TEMP_DIR, RESULTS_DIR, CACHE_DIR]:
    dir_path.mkdir(exist_ok=True)

# ============================================================================
# ЛИМИТЫ
# ============================================================================
MAX_FILE_SIZE = 400 * 1024 * 1024  # 400MB
MAX_VIDEO_DURATION = 600  # 10 минут
MIN_VIDEO_DURATION = 5  # 5 секунд

# ============================================================================
# VIDEO SETTINGS
# ============================================================================
VIDEO_SETTINGS = {
    "output_resolution": (1080, 1920),  # 9:16 vertical
    "fps": 30,
    "bitrate": "8M",
    "audio_bitrate": "128k",
    "codec": "libx264",
    "crf": 18,  # Качество (меньше = лучше, 0-51)
    "preset": "fast",  # ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
}

# ============================================================================
# ВИДЕООБРАБОТКА
# ============================================================================
# Паузы
PAUSE_THRESHOLD = 0.5  # Сек - минимальная длительность паузы для удаления
PAUSE_MIN_LENGTH = 0.1  # Сек - минимальная длительность сжатой паузы

# Зумирование
ZOOM_FACTOR = 1.05  # На 5% увеличение (мягкое, не резкое)
ZOOM_DURATION = 2  # Секунды для плавного зума

# Субтитры
SUBTITLE_STYLES = {
    "bright": {
        "name": "✨ Яркий",
        "primary_color": (255, 51, 102),  # Ярко-розовый
        "text_color": (255, 255, 255),  # Белый
        "outline_color": (0, 0, 0),  # Чёрный
        "font_size": 60,
    },
    "minimal": {
        "name": "⚫ Минимальный",
        "primary_color": (255, 255, 255),  # Белый
        "text_color": (0, 0, 0),  # Чёрный
        "outline_color": (255, 255, 255),  # Белый
        "font_size": 50,
    },
    "cyberpunk": {
        "name": "🌐 Киберпанк",
        "primary_color": (0, 255, 255),  # Неоновый синий
        "text_color": (0, 255, 255),  # Неоновый синий
        "outline_color": (0, 0, 0),  # Чёрный
        "font_size": 60,
    },
    "warm": {
        "name": "🔥 Тёплый",
        "primary_color": (255, 127, 0),  # Оранжевый
        "text_color": (255, 255, 255),  # Белый
        "outline_color": (0, 0, 0),  # Чёрный
        "font_size": 55,
    },
}

DEFAULT_SUBTITLE_STYLE = "bright"

# ============================================================================
# ЭФФЕКТЫ
# ============================================================================
EFFECTS = {
    "pauses": {
        "name": "✂️ Вырезание пауз",
        "enabled": True,
        "description": "Удаляет молчание > 0.5 сек"
    },
    "duplicates": {
        "name": "🗣️ Удаление повторов",
        "enabled": True,
        "description": "Убирает повторяющиеся кадры"
    },
    "zoom": {
        "name": "🎯 Зумирование",
        "enabled": True,
        "description": "Добавляет мягкие зум-эффекты"
    },
    "subtitles": {
        "name": "📝 Субтитры",
        "enabled": True,
        "description": "Красивые синхронизированные субтитры"
    },
    "emoji": {
        "name": "😊 Эмоджи",
        "enabled": True,
        "description": "Релевантные эмоджи на ключевые слова"
    },
    "enhance": {
        "name": "🎨 Улучшение качества",
        "enabled": True,
        "description": "Шумоподавление, контраст, звук"
    },
    "resolution": {
        "name": "📊 Исправление разрешения",
        "enabled": True,
        "description": "Конвертирует в 9:16 без потери качества"
    },
    "music": {
        "name": "🎵 Фоновая музыка",
        "enabled": True,
        "description": "Добавляет музыку в паузы"
    },
}

# ============================================================================
# ОБРАБОТКА
# ============================================================================
# Таймауты (в секундах)
PROCESSING_TIMEOUT = 900  # 15 минут
VIDEO_DOWNLOAD_TIMEOUT = 60

# Параллельная обработка
MAX_CONCURRENT_TASKS = 1  # На облаке обычно 1
QUEUE_CHECK_INTERVAL = 1  # Сек

# ============================================================================
# ЛОГИРОВАНИЕ
# ============================================================================
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"

# ============================================================================
# РАСШИРЕНИЯ ВИДЕО
# ============================================================================
SUPPORTED_VIDEO_FORMATS = {
    "mp4": "MPEG-4 Video",
    "mov": "Apple QuickTime",
    "mkv": "Matroska Video",
    "avi": "AVI Video",
    "webm": "WebM Video",
    "flv": "Flash Video",
    "wmv": "Windows Media Video",
}
