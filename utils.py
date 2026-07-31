"""
Utilities module - helper functions
"""

import json
import logging
from pathlib import Path
from config import LOG_FILE, LOG_FORMAT, LOG_LEVEL


def setup_logging(log_file=LOG_FILE):
    """Инициализация логирования"""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    formatter = logging.Formatter(LOG_FORMAT)
    
    # File handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger


def get_user_settings(user_id):
    """Получение настроек пользователя"""
    settings_file = Path("cache") / f"user_{user_id}_settings.json"
    
    if settings_file.exists():
        try:
            with open(settings_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Failed to load settings for user {user_id}: {e}")
    
    # Настройки по умолчанию
    return {
        "style": "bright",
        "branding_name": "My Channel",
        "language": "ru"
    }


def save_user_settings(user_id, settings):
    """Сохранение настроек пользователя"""
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    
    settings_file = cache_dir / f"user_{user_id}_settings.json"
    
    try:
        with open(settings_file, "w") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        logging.info(f"Settings saved for user {user_id}")
    except Exception as e:
        logging.error(f"Failed to save settings for user {user_id}: {e}")


def format_duration(seconds):
    """Форматирование длительности в MM:SS"""
    if seconds < 0:
        return "0:00"
    
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    
    return f"{mins}:{secs:02d}"


def calculate_reduction_percent(original_duration, final_duration):
    """Расчёт процента сокращения видео"""
    if original_duration == 0:
        return 0
    
    reduction = (original_duration - final_duration) / original_duration * 100
    return max(0, min(100, reduction))


def estimate_ctr(stats):
    """
    Прогноз CTR на основе статистики видео
    
    Args:
        stats: dict со статистикой видео
        
    Returns:
        прогнозируемый CTR (0-100%)
    """
    from config import CTR_FACTORS, BASE_CTR
    
    ctr = BASE_CTR
    
    # Факторы влияния
    factors = {
        "emoji_count": stats.get("emoji_count", 0),
        "accent_count": stats.get("accents_count", 0),
        "duration_ratio": stats.get("reduction_percent", 0),
    }
    
    # Добавляем бонусы за эффекты
    if factors["emoji_count"] > 0:
        ctr += min(20, factors["emoji_count"] * 2)
    
    if factors["accent_count"] >= 6:
        ctr += 15
    
    if factors["duration_ratio"] > 60:
        ctr += 10
    
    return min(100, max(0, ctr))


def validate_video_file(file_path):
    """Проверка валидности видеофайла"""
    from pathlib import Path
    
    path = Path(file_path)
    
    if not path.exists():
        return False, "File does not exist"
    
    valid_extensions = {".mp4", ".mov", ".avi", ".mkv"}
    if path.suffix.lower() not in valid_extensions:
        return False, f"Invalid extension. Allowed: {valid_extensions}"
    
    # Проверка размера (макс 100 МБ)
    max_size = 100 * 1024 * 1024
    if path.stat().st_size > max_size:
        return False, "File is too large (max 100 MB)"
    
    return True, "OK"


def get_aspect_ratio(width, height):
    """Определение соотношения сторон видео"""
    from math import gcd
    
    divisor = gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def log_processing_stats(user_id, stats):
    """Логирование статистики обработки"""
    logger = logging.getLogger(__name__)
    
    log_message = f"""
    ========== PROCESSING STATS FOR USER {user_id} ==========
    Original duration: {stats.get('original_duration', 0):.1f}s
    Final duration: {stats.get('final_duration', 0):.1f}s
    Reduction: {stats.get('reduction_percent', 0):.1f}%
    Accents: {stats.get('accents_count', 0)}
    Pauses removed: {stats.get('pauses_removed', 0)}
    Predicted CTR: {stats.get('predicted_ctr', 0):.1f}%
    File size: {stats.get('file_size_mb', 0):.1f} MB
    =====================================================
    """
    
    logger.info(log_message)
