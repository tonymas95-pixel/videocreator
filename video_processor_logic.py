"""
Video processing logic - core algorithm
"""

import logging
from pathlib import Path
from datetime import datetime
import os
from transcriber import Transcriber
from analyzer import VideoAnalyzer
from subtitle_generator import SubtitleGenerator
from effects_engine import EffectsEngine
from utils import calculate_reduction_percent, estimate_ctr
from config import RESULTS_DIR, TEMP_DIR, TARGET_FINAL_DURATION

logger = logging.getLogger(__name__)


def process_video_logic(
    video_path,
    user_id,
    style="bright",
    preview_mode=False,
    branding_text="",
    custom_comment=""
):
    """
    Основная логика обработки видео
    
    Процесс:
    1. Транскрибация (распознавание речи)
    2. Анализ видео (пики, паузы)
    3. Нарезка и монтаж
    4. Добавление субтитров и эффектов
    5. Экспорт финального видео
    
    Args:
        video_path: путь к исходному видео
        user_id: ID пользователя
        style: стиль субтитров
        preview_mode: True для превью (10 сек), False для полного видео
        branding_text: текст брендинга
        custom_comment: комментарий пользователя
        
    Returns:
        dict с результатами или путь до файла при preview_mode=True
    """
    
    try:
        logger.info(f"Starting video processing for user {user_id}")
        logger.info(f"Preview mode: {preview_mode}")
        
        # Шаг 1: Транскрибация
        logger.info("Step 1: Transcription...")
        transcriber = Transcriber(model="base")
        transcript_result = transcriber.transcribe(video_path)
        
        if not transcript_result.get("success"):
            logger.error("Transcription failed")
            return None if preview_mode else {"error": "Transcription failed"}
        
        segments = transcript_result.get("segments", [])
        transcript_text = transcript_result.get("text", "")
        logger.info(f"Transcription complete: {len(transcript_text)} characters")
        
        # Шаг 2: Анализ видео
        logger.info("Step 2: Video analysis...")
        analyzer = VideoAnalyzer()
        accents = analyzer.find_accents(segments)
        pauses = analyzer.detect_pauses([])  # В реальности нужно извлечь аудио
        filler_count = analyzer.detect_filler_words(transcript_text)
        
        logger.info(f"Found {len(accents)} accents, {len(pauses)} pauses, {filler_count} fillers")
        
        # Шаг 3: Генерация субтитров
        logger.info("Step 3: Subtitle generation...")
        subtitle_gen = SubtitleGenerator(style=style)
        subtitles = subtitle_gen.generate_subtitles(segments, accents)
        
        # Шаг 4: Эффекты
        logger.info("Step 4: Effects generation...")
        effects = EffectsEngine()
        zoom_effects = effects.generate_zoom_effects(accents, 0)  # video_duration = 0 для заглушки
        text_animations = effects.generate_text_animations(subtitles)
        emoji_effects = effects.generate_emoji_effects(subtitles)
        
        # Шаг 5: Подготовка выходного файла
        logger.info("Step 5: Output file preparation...")
        
        output_dir = Path(RESULTS_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"shorts_{user_id}_{timestamp}.mp4"
        output_path = output_dir / output_filename
        
        # В реальном приложении здесь был бы FFmpeg/OpenCV код для создания видео
        # Сейчас просто копируем исходный файл в качестве заглушки
        import shutil
        shutil.copy(video_path, output_path)
        
        # Подготовка статистики
        stats = {
            "original_duration": 120.0,  # Заглушка
            "final_duration": 38.0 if not preview_mode else 10.0,
            "reduction_percent": calculate_reduction_percent(120, 38 if not preview_mode else 10),
            "accents_count": len(accents),
            "pauses_removed": len(pauses),
            "file_size_mb": os.path.getsize(output_path) / (1024 * 1024),
            "predicted_ctr": estimate_ctr({
                "emoji_count": len(emoji_effects),
                "accents_count": len(accents),
                "reduction_percent": calculate_reduction_percent(120, 38)
            })
        }
        
        logger.info(f"Processing complete. Output: {output_path}")
        logger.info(f"Stats: {stats}")
        
        if preview_mode:
            return str(output_path)
        else:
            return {
                "output_video": str(output_path),
                "stats": stats,
                "subtitle_count": len(subtitles),
                "effects_applied": {
                    "zooms": len(zoom_effects),
                    "animations": len(text_animations),
                    "emojis": len(emoji_effects)
                }
            }
            
    except Exception as e:
        logger.error(f"Video processing error: {e}", exc_info=True)
        return None if preview_mode else {"error": str(e)}
