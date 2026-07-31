"""
Analyzer module - video and audio analysis
"""

import logging
import numpy as np
from config import ANALYSIS_SETTINGS, FILLER_WORDS, KEYWORD_MARKERS

logger = logging.getLogger(__name__)


class VideoAnalyzer:
    """Класс для анализа видео и аудио"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def detect_pauses(self, audio_data, sr=16000):
        """
        Определение пауз в аудио
        
        Args:
            audio_data: numpy array аудиоданных
            sr: sample rate
            
        Returns:
            список пауз с временными метками
        """
        try:
            # Порог определения паузы
            threshold = np.mean(np.abs(audio_data)) * 0.1
            pauses = []
            pause_start = None
            
            for i, sample in enumerate(audio_data):
                time = i / sr
                is_silent = np.abs(sample) < threshold
                
                if is_silent and pause_start is None:
                    pause_start = time
                elif not is_silent and pause_start is not None:
                    pause_duration = time - pause_start
                    if pause_duration > ANALYSIS_SETTINGS["pause_threshold"]:
                        pauses.append({
                            "start": pause_start,
                            "end": time,
                            "duration": pause_duration
                        })
                    pause_start = None
            
            return pauses
            
        except Exception as e:
            self.logger.error(f"Pause detection failed: {e}")
            return []

    def find_accents(self, transcript_segments, audio_energy=None):
        """
        Поиск акцентов (ключевых моментов) в видео
        
        Args:
            transcript_segments: сегменты транскрибации
            audio_energy: энергия аудио для каждого фрейма
            
        Returns:
            список найденных акцентов
        """
        accents = []
        
        for segment in transcript_segments:
            text = segment.get("text", "").lower()
            start = segment.get("start", 0)
            end = segment.get("end", 0)
            
            # Ищем важные слова
            for category, words in KEYWORD_MARKERS.items():
                for word in words:
                    if word in text:
                        accents.append({
                            "text": text,
                            "start": start,
                            "end": end,
                            "category": category,
                            "keyword": word,
                            "type": "keyword"
                        })
                        break
        
        # Сортируем по времени и берём нужное количество
        accents = sorted(accents, key=lambda x: x["start"])
        target = ANALYSIS_SETTINGS.get("target_accents", 6)
        
        if len(accents) > target:
            # Берём равномерно распределённые акценты
            step = len(accents) // target
            accents = accents[::step][:target]
        
        return accents

    def detect_filler_words(self, transcript_text):
        """
        Определение слов-паразитов для удаления
        
        Args:
            transcript_text: текст транскрибации
            
        Returns:
            количество найденных слов-паразитов
        """
        text = transcript_text.lower()
        count = 0
        
        for filler in FILLER_WORDS:
            count += text.count(filler)
        
        return count

    def analyze_speech_speed(self, text, duration):
        """
        Анализ скорости речи (слова в секунду)
        
        Args:
            text: транскрибированный текст
            duration: длительность в секундах
            
        Returns:
            слова в секунду
        """
        if duration == 0:
            return 0
        
        word_count = len(text.split())
        wps = word_count / duration
        
        return wps
