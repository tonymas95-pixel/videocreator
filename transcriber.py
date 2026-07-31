"""
Transcriber module - speech recognition using OpenAI Whisper
"""

import logging
import whisper
from config import AUDIO_SETTINGS

logger = logging.getLogger(__name__)


class Transcriber:
    """Класс для распознавания речи"""

    def __init__(self, model="base"):
        self.model_name = model
        try:
            self.model = whisper.load_model(model)
            logger.info(f"Whisper model '{model}' loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    def transcribe(self, audio_path):
        """
        Распознавание речи в аудиофайле
        
        Args:
            audio_path: путь к аудиофайлу
            
        Returns:
            dict с результатами распознавания
        """
        try:
            logger.info(f"Transcribing audio: {audio_path}")
            
            result = self.model.transcribe(audio_path, language="ru")
            
            logger.info(f"Transcription completed: {len(result.get('segments', []))} segments")
            
            return {
                "text": result.get("text", ""),
                "segments": result.get("segments", []),
                "language": result.get("language", "ru"),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {"text": "", "segments": [], "success": False, "error": str(e)}

    def extract_timestamps(self, segments):
        """
        Извлечение временных меток для каждого слова
        
        Args:
            segments: список сегментов из Whisper
            
        Returns:
            список с временными метками
        """
        timestamps = []
        
        for segment in segments:
            start = segment.get("start", 0)
            end = segment.get("end", 0)
            text = segment.get("text", "").strip()
            
            if text:
                timestamps.append({
                    "text": text,
                    "start": start,
                    "end": end,
                    "duration": end - start
                })
        
        return timestamps
