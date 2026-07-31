import os
import logging
import uuid
import subprocess
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips
from moviepy.video.fx.all import resize
import numpy as np

from config import Config
from database import Database
from transcriber import Transcriber

logger = logging.getLogger(__name__)
db = Database()

def detect_silence(audio_path, silence_thresh=-40, min_silence_duration=0.3):
    """Обнаруживает паузы в аудио с помощью ffmpeg"""
    try:
        cmd = [
            "ffmpeg",
            "-i", audio_path,
            "-af", f"silencedetect=noise={silence_thresh}dB:d={min_silence_duration}",
            "-f", "null",
            "-"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        silence_segments = []
        for line in result.stderr.split('\n'):
            if 'silence_start' in line:
                start = float(line.split('silence_start: ')[1].split()[0])
                silence_segments.append({'start': start})
            elif 'silence_end' in line:
                end = float(line.split('silence_end: ')[1].split()[0])
                if silence_segments:
                    silence_segments[-1]['end'] = end
        
        return silence_segments
    except Exception as e:
        logger.error(f"Silence detection error: {e}")
        return []

def remove_silence(video_path, audio_path, output_path, silence_thresh=-40, min_silence_duration=0.3):
    """Удаляет паузы из видео"""
    try:
        video = VideoFileClip(video_path)
        audio = video.audio
        
        if audio is None:
            video.write_videofile(output_path, codec='libx264', audio_codec='aac')
            return video.duration
        
        # Обнаружение пауз
        silence_segments = detect_silence(audio_path, silence_thresh, min_silence_duration)
        
        if not silence_segments:
            video.write_videofile(output_path, codec='libx264', audio_codec='aac')
            return video.duration
        
        # Создаём фрагменты без пауз
        clips = []
        current_time = 0
        
        for seg in silence_segments:
            start = seg['start']
            end = seg.get('end', start + min_silence_duration)
            
            if current_time < start:
                clips.append(video.subclip(current_time, start))
            current_time = end
        
        if current_time < video.duration:
            clips.append(video.subclip(current_time, video.duration))
        
        if not clips:
            video.write_videofile(output_path, codec='libx264', audio_codec='aac')
            return video.duration
        
        # Склеиваем
        final_clip = concatenate_videoclips(clips)
        final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        final_duration = final_clip.duration
        video.close()
        final_clip.close()
        
        return final_duration
        
    except Exception as e:
        logger.error(f"Remove silence error: {e}")
        return 0

def add_zoom_effects(video_path, output_path, key_moments):
    """Добавляет зум-эффекты в ключевые моменты"""
    try:
        clip = VideoFileClip(video_path)
        
        if not key_moments:
            clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            return
        
        # Применяем зум к ключевым моментам
        clips = []
        current_time = 0
        
        for moment in key_moments:
            start = moment['start']
            end = moment['end']
            
            # Обычная часть
            if current_time < start:
                clips.append(clip.subclip(current_time, start).resize(height=720))
            
            # Часть с зумом
            zoom_clip = clip.subclip(start, end)
            zoom_clip = zoom_clip.resize(lambda t: 1 + 0.15 * (t / zoom_clip.duration))
            zoom_clip = zoom_clip.resize(height=720)
            clips.append(zoom_clip)
            
            current_time = end
        
        if current_time < clip.duration:
            clips.append(clip.subclip(current_time, clip.duration).resize(height=720))
        
        final_clip = concatenate_videoclips(clips)
        final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        clip.close()
        final_clip.close()
        
    except Exception as e:
        logger.error(f"Zoom effects error: {e}")
        # Если ошибка - просто копируем видео
        clip = VideoFileClip(video_path)
        clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        clip.close()

def add_subtitles(video_path, output_path, segments):
    """Добавляет субтитры с выделением ключевых слов"""
    try:
        clip = VideoFileClip(video_path)
        
        if not segments:
            clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            return
        
        # Создаём субтитры
        subtitles = []
        for seg in segments:
            text = seg['text']
            start = seg['start']
            end = seg['end']
            
            # Разбиваем на слова
            words = text.split()
            if len(words) > 1:
                # Выделяем первое слово (ключевое)
                first_word = words[0]
                rest = ' '.join(words[1:])
                
                # Создаём текст с выделением
                subtitle = TextClip(
                    f"{first_word} {rest}",
                    fontsize=Config.FONT_SIZE,
                    color=Config.FONT_COLOR,
                    stroke_color='black',
                    stroke_width=2,
                    font=Config.FONT_PATH
                )
                
                # Увеличиваем первое слово
                subtitle = subtitle.set_position(('center', 'bottom')).set_start(start).set_duration(end - start)
                subtitles.append(subtitle)
        
        # Накладываем субтитры
        if subtitles:
            final_clip = CompositeVideoClip([clip] + subtitles)
            final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            final_clip.close()
        else:
            clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        clip.close()
        
    except Exception as e:
        logger.error(f"Subtitle error: {e}")
        clip = VideoFileClip(video_path)
        clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        clip.close()

def find_key_moments(segments, num_moments=5):
    """Находит ключевые моменты для акцентов"""
    if not segments:
        return []
    
    # Сортируем по длительности
    sorted_segments = sorted(segments, key=lambda x: x['end'] - x['start'], reverse=True)
    
    # Берём топ N моментов
    key_moments = sorted_segments[:num_moments]
    return [{'start': m['start'], 'end': m['end']} for m in key_moments]

async def handle_video(update, context):
    """Обработка видео с полным функционалом"""
    user_id = update.effective_user.id
    
    user = update.effective_user
    db.save_user(user_id, user.username, user.first_name, user.last_name)
    
    try:
        # Проверка размера
        file_size = update.message.video.file_size
        if file_size > Config.MAX_FILE_SIZE:
            await update.message.reply_text(
                f"❌ Файл слишком большой ({file_size // 1024 // 1024} МБ).\n"
                f"Максимум: {Config.MAX_FILE_SIZE // 1024 // 1024} МБ"
            )
            return
        
        msg = await update.message.reply_text("🎬 Начинаю обработку...")
        
        # Скачиваем видео
        video_file = await update.message.video.get_file()
        input_path = f"{Config.TEMP_DIR}/input_{user_id}_{uuid.uuid4()}.mp4"
        await video_file.download_to_drive(input_path)
        
        await msg.edit_text("🎵 Извлекаю аудио...")
        
        # Извлекаем аудио
        audio_path = f"{Config.TEMP_DIR}/audio_{user_id}_{uuid.uuid4()}.wav"
        transcriber = Transcriber()
        if not transcriber.extract_audio(input_path, audio_path):
            await update.message.reply_text("❌ Не удалось извлечь аудио")
            return
        
        await msg.edit_text("📝 Распознаю речь...")
        
        # Транскрипция
        segments = transcriber.transcribe(audio_path)
        
        await msg.edit_text("✂️ Удаляю паузы...")
        
        # Удаление пауз
        no_silence_path = f"{Config.TEMP_DIR}/no_silence_{user_id}_{uuid.uuid4()}.mp4"
        final_duration = remove_silence(input_path, audio_path, no_silence_path)
        
        await msg.edit_text(f"🎯 Нашёл ключевые моменты...")
        
        # Находим ключевые моменты
        key_moments = find_key_moments(segments)
        
        await msg.edit_text("🔍 Добавляю зум-эффекты...")
        
        # Добавляем зум
        zoom_path = f"{Config.TEMP_DIR}/zoom_{user_id}_{uuid.uuid4()}.mp4"
        add_zoom_effects(no_silence_path, zoom_path, key_moments)
        
        await msg.edit_text("💬 Добавляю субтитры...")
        
        # Добавляем субтитры
        output_path = f"{Config.RESULTS_DIR}/result_{user_id}_{uuid.uuid4()}.mp4"
        add_subtitles(zoom_path, output_path, segments)
        
        # Отправляем результат
        await msg.edit_text("📤 Отправляю готовый ролик...")
        
        with open(output_path, 'rb') as f:
            await update.message.reply_video(
                video=f,
                caption=(
                    f"✅ Готово!\n\n"
                    f"📹 Исходная длина: {int(final_duration)} сек\n"
                    f"✂️ Удалено пауз: {len(segments) - len(key_moments)}\n"
                    f"🎯 Акцентов: {len(key_moments)}\n"
                    f"🔥 Ролик готов к публикации!"
                )
            )
        
        # Записываем в БД
        db.add_process(user_id, int(final_duration), min(45, int(final_duration)), 0, False)
        
        # Удаляем временные файлы
        for path in [input_path, audio_path, no_silence_path, zoom_path, output_path]:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except:
                pass
        
    except Exception as e:
        logger.error(f"Video processing error: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:200]}")
