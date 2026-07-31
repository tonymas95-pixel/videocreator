"""
Subtitle generator - creating dynamic animated subtitles
"""

import logging
from config import SUBTITLE_STYLES, EFFECTS_SETTINGS

logger = logging.getLogger(__name__)


class SubtitleGenerator:
    """Класс для генерации субтитров"""

    def __init__(self, style="bright"):
        self.style = style
        self.style_config = SUBTITLE_STYLES.get(style, SUBTITLE_STYLES["bright"])
        self.logger = logging.getLogger(__name__)

    def generate_subtitles(self, segments, accents=None):
        """
        Генерация субтитров для каждого сегмента
        
        Args:
            segments: список сегментов с текстом и временем
            accents: акценты для выделения
            
        Returns:
            список субтитров с эффектами
        """
        subtitles = []
        accents = accents or []
        accent_keywords = {a.get("keyword") for a in accents}
        
        for segment in segments:
            text = segment.get("text", "").strip()
            start = segment.get("start", 0)
            end = segment.get("end", 0)
            
            if not text:
                continue
            
            # Определяем стиль для этого сегмента
            is_accent = any(keyword in text.lower() for keyword in accent_keywords)
            
            subtitle = {
                "text": text,
                "start": start,
                "end": end,
                "duration": end - start,
                "style": self.style,
                "colors": self.style_config,
                "font_size": self._get_font_size(text, is_accent),
                "animation": self.style_config.get("animation", "fade"),
                "is_accent": is_accent,
                "emoji": self._select_emoji(text) if is_accent else None
            }
            
            subtitles.append(subtitle)
        
        return subtitles

    def _get_font_size(self, text, is_accent=False):
        """Определение размера шрифта"""
        base_size = EFFECTS_SETTINGS.get("base_font_size", 70)
        
        if is_accent:
            return int(base_size * EFFECTS_SETTINGS.get("keyword_font_size_multiplier", 1.3))
        
        return base_size

    def _select_emoji(self, text):
        """Выбор подходящего эмодзи для текста"""
        text_lower = text.lower()
        
        # Простой выбор эмодзи на основе ключевых слов
        if any(word in text_lower for word in ["деньги", "скидка", "цена"]):
            return "💰"
        elif any(word in text_lower for word in ["новое", "первый", "начин"]):
            return "✨"
        elif any(word in text_lower for word in ["спасибо", "хорошо", "отлично"]):
            return "👍"
        elif any(word in text_lower for word in ["быстро", "срочно", "сейчас"]):
            return "⚡"
        
        return None

    def get_style_info(self):
        """Информация о текущем стиле"""
        return {
            "name": self.style_config.get("name", self.style),
            "description": self.style_config.get("description", ""),
            "colors": {
                "primary": self.style_config.get("primary_color"),
                "secondary": self.style_config.get("secondary_color"),
                "text": self.style_config.get("text_color"),
                "outline": self.style_config.get("outline_color")
            }
        }
