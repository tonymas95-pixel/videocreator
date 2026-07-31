import os
import subprocess
import json
import logging

logger = logging.getLogger(__name__)

class Transcriber:
    def __init__(self, model="base"):
        self.model = model
    
    def extract_audio(self, video_path, audio_path):
        """Извлекает аудио из видео"""
        try:
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-ac", "1",
                "-ar", "16000",
                audio_path,
                "-y"
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except Exception as e:
            logger.error(f"Audio extraction error: {e}")
            return False
    
    def transcribe(self, audio_path):
        """Транскрибирует аудио (заглушка для теста)"""
        # В будущем подключите реальный Whisper
        return [
            {"start": 0.0, "end": 1.5, "text": "Привет мир"},
            {"start": 1.5, "end": 3.0, "text": "Это тестовый ролик"},
            {"start": 3.0, "end": 4.5, "text": "Для проверки работы бота"},
            {"start": 4.5, "end": 6.0, "text": "Скоро здесь будет реальная транскрипция"}
        ]
