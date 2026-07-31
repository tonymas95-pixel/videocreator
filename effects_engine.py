"""
Effects engine - video effects, zooms, animations
"""

import logging
from config import EFFECTS_SETTINGS

logger = logging.getLogger(__name__)


class EffectsEngine:
    """Класс для применения видеоэффектов"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.zoom_factor = EFFECTS_SETTINGS.get("zoom_factor", 1.3)
        self.emoji_size = EFFECTS_SETTINGS.get("emoji_size", 80)

    def generate_zoom_effects(self, accents, video_duration):
        """
        Генерация зум-эффектов для акцентов
        
        Args:
            accents: список акцентов
            video_duration: длительность видео
            
        Returns:
            список зум-эффектов с временем применения
        """
        zoom_effects = []
        
        for accent in accents:
            start = accent.get("start", 0)
            end = accent.get("end", 0)
            
            # Добавляем зум-эффект
            zoom_effect = {
                "type": "zoom",
                "start": start,
                "end": end,
                "zoom_factor": self.zoom_factor,
                "duration": end - start,
                "easing": "ease-in-out"
            }
            
            zoom_effects.append(zoom_effect)
        
        return zoom_effects

    def generate_text_animations(self, subtitles):
        """
        Генерация текстовых анимаций
        
        Args:
            subtitles: список субтитров
            
        Returns:
            список анимаций для текста
        """
        animations = []
        
        for subtitle in subtitles:
            text = subtitle.get("text", "")
            start = subtitle.get("start", 0)
            animation_type = subtitle.get("animation", "fade")
            
            # Разбиваем текст на слова для покадровой анимации
            words = text.split()
            word_appear_duration = EFFECTS_SETTINGS.get("word_appear_duration", 0.15)
            
            for idx, word in enumerate(words):
                word_start = start + (idx * word_appear_duration)
                word_end = word_start + word_appear_duration
                
                animation = {
                    "type": animation_type,
                    "text": word,
                    "start": word_start,
                    "end": word_end,
                    "index": idx
                }
                
                animations.append(animation)
        
        return animations

    def generate_emoji_effects(self, subtitles):
        """
        Генерация эффектов с эмодзи
        
        Args:
            subtitles: список субтитров
            
        Returns:
            список эмодзи эффектов
        """
        emoji_effects = []
        
        for subtitle in subtitles:
            emoji = subtitle.get("emoji")
            if not emoji:
                continue
            
            start = subtitle.get("start", 0)
            end = subtitle.get("end", 0)
            
            emoji_effect = {
                "type": "emoji",
                "emoji": emoji,
                "start": start,
                "end": end,
                "size": self.emoji_size,
                "appear_duration": EFFECTS_SETTINGS.get("emoji_appear_duration", 0.3),
                "stay_duration": EFFECTS_SETTINGS.get("emoji_stay_duration", 1.5)
            }
            
            emoji_effects.append(emoji_effect)
        
        return emoji_effects

    def apply_transitions(self, scenes):
        """
        Применение переходов между сценами
        
        Args:
            scenes: список сцен
            
        Returns:
            список сцен с переходами
        """
        for i in range(len(scenes) - 1):
            scenes[i]["transition"] = {
                "type": "fade",
                "duration": 0.3
            }
        
        return scenes

    def get_effects_summary(self, effects_list):
        """Краткая информация об применённых эффектах"""
        return {
            "zoom_count": len([e for e in effects_list if e.get("type") == "zoom"]),
            "animation_count": len([e for e in effects_list if e.get("type") in ["fade", "bounce", "pulse"]]),
            "emoji_count": len([e for e in effects_list if e.get("type") == "emoji"])
        }
