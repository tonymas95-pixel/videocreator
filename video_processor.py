"""
Video processing module - main coordinator for video editing
"""

import logging
from pathlib import Path
from video_processor_logic import process_video_logic

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Главный класс для обработки видео"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process_video_with_preview(
        self, video_path, user_id, style="bright", custom_comment=""
    ):
        """
        Обработка видео и создание превью (первые 10 сек)
        
        Args:
            video_path: путь к видео файлу
            user_id: ID пользователя Telegram
            style: стиль субтитров (bright, minimal, cyberpunk, warm)
            custom_comment: комментарий пользователя
            
        Returns:
            путь к файлу превью или None если ошибка
        """
        try:
            self.logger.info(f"Creating preview for user {user_id}: {video_path}")
            
            # Основная логика обработки
            preview_path = process_video_logic(
                video_path,
                user_id,
                style=style,
                preview_mode=True,
                custom_comment=custom_comment
            )
            
            return preview_path
            
        except Exception as e:
            self.logger.error(f"Preview processing failed: {e}")
            return None

    def process_full_video(
        self, video_path, user_id, style="bright", branding_text="", custom_comment=""
    ):
        """
        Полная обработка видео (создание финального клипа)
        
        Args:
            video_path: путь к видео файлу
            user_id: ID пользователя
            style: стиль субтитров
            branding_text: текст брендинга (имя канала)
            custom_comment: комментарий пользователя
            
        Returns:
            dict с результатами обработки
        """
        try:
            self.logger.info(f"Processing full video for user {user_id}: {video_path}")
            
            # Основная логика обработки
            result = process_video_logic(
                video_path,
                user_id,
                style=style,
                preview_mode=False,
                branding_text=branding_text,
                custom_comment=custom_comment
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Full video processing failed: {e}")
            return {"error": str(e), "output_video": None}
