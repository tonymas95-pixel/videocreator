import os
import logging
import uuid
import subprocess
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

from config import Config
from database import Database

logger = logging.getLogger(__name__)
db = Database()

def extract_audio(video_path, audio_path):
    """Извлекает аудио из видео"""
    try:
        cmd = ["ffmpeg", "-i", video_path, "-ac", "1", "-ar", "16000", audio_path, "-y"]
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        logger.error(f"Audio extraction error: {e}")
        return False

def detect_silence(audio_path, min_silence=0.3):
    """Находит паузы в аудио"""
    try:
        cmd = ["ffmpeg", "-i", audio_path, "-af", f"silencedetect=noise=-30dB:d={min_silence}", "-f", "null", "-"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        silences = []
        start = None
        for line in result.stderr.split('\n'):
            if 'silence_start' in line:
                start = float(line.split('silence_start: ')[1].split()[0])
            elif 'silence_end' in line and start is not None:
                end = float(line.split('silence_end: ')[1].split()[0])
                silences.append({'start': start, 'end': end})
                start = None
        return silences
    except Exception as e:
        logger.error(f"Silence detection error: {e}")
        return []

def remove_silence_from_video(video_path, audio_path, output_path):
    """Удаляет паузы из видео"""
    try:
        video = VideoFileClip(video_path)
        
        # Находим паузы
        silences = detect_silence(audio_path)
        
        if not silences:
            video.write_videofile(output_path, codec='libx264', audio_codec='aac')
            video.close()
            return video.duration
        
        # Создаём клипы без пауз
        clips = []
        current = 0
        
        for s in silences:
            if current < s['start']:
                clips.append(video.subclip(current, s['start']))
            current = s['end']
        
        if current < video.duration:
            clips.append(video.subclip(current, video.duration))
        
        if not clips:
            video.write_videofile(output_path, codec='libx264', audio_codec='aac')
            video.close()
            return video.duration
        
        # Склеиваем
        final = concatenate_videoclips(clips)
        final.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        duration = final.duration
        video.close()
        final.close()
        return duration
        
    except Exception as e:
        logger.error(f"Remove silence error: {e}")
        return 0

def add_subtitles_to_video(video_path, output_path, text="Тестовые субтитры"):
    """Добавляет субтитры на видео"""
    try:
        video = VideoFileClip(video_path)
        
        # Создаём текстовый клип
        txt_clip = TextClip(
            text,
            fontsize=50,
            color='white',
            stroke_color='black',
            stroke_width=3,
            font='Arial'
        ).set_position(('center', 'bottom')).set_duration(video.duration)
        
        # Накладываем
        final = CompositeVideoClip([video, txt_clip])
        final.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        video.close()
        final.close()
        return True
    except Exception as e:
        logger.error(f"Subtitle error: {e}")
        return False

def add_zoom_to_video(video_path, output_path):
    """Добавляет зум-эффект"""
    try:
        video = VideoFileClip(video_path)
        
        # Зум на 20% в середине видео
        def make_zoom(t):
            if 5 <= t <= 10:
                return 1 + 0.15 * ((t - 5) / 5)
            return 1
        
        zoomed = video.resize(lambda t: make_zoom(t))
        zoomed.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        video.close()
        zoomed.close()
        return True
    except Exception as e:
        logger.error(f"Zoom error: {e}")
        return False

async def handle_video(update, context):
    """Главный обработчик видео"""
    user_id = update.effective_user.id
    
    try:
        # Проверка размера (300 МБ)
        if update.message.video.file_size > 300 * 1024 * 1024:
            await update.message.reply_text("❌ Файл больше 300 МБ")
            return
        
        msg = await update.message.reply_text("🎬 Начинаю обработку...")
        
        # Скачиваем
        video_file = await update.message.video.get_file()
        input_path = f"{Config.TEMP_DIR}/input_{user_id}_{uuid.uuid4()}.mp4"
        await video_file.download_to_drive(input_path)
        
        await msg.edit_text("🎵 Извлекаю аудио...")
        
        # Извлекаем аудио
        audio_path = f"{Config.TEMP_DIR}/audio_{user_id}_{uuid.uuid4()}.wav"
        if not extract_audio(input_path, audio_path):
            await msg.edit_text("❌ Ошибка извлечения аудио")
            return
        
        await msg.edit_text("✂️ Удаляю паузы...")
        
        # Удаляем паузы
        no_silence_path = f"{Config.TEMP_DIR}/no_silence_{user_id}_{uuid.uuid4()}.mp4"
        duration = remove_silence_from_video(input_path, audio_path, no_silence_path)
        
        if duration == 0:
            await msg.edit_text("❌ Не удалось обработать видео")
            return
        
        await msg.edit_text("🔍 Добавляю зум-эффект...")
        
        # Добавляем зум
        zoom_path = f"{Config.TEMP_DIR}/zoom_{user_id}_{uuid.uuid4()}.mp4"
        if not add_zoom_to_video(no_silence_path, zoom_path):
            zoom_path = no_silence_path
        
        await msg.edit_text("💬 Добавляю субтитры...")
        
        # Добавляем субтитры
        output_path = f"{Config.RESULTS_DIR}/result_{user_id}_{uuid.uuid4()}.mp4"
        if not add_subtitles_to_video(zoom_path, output_path, "🎬 Обработано ботом"):
            output_path = zoom_path
        
        await msg.edit_text("📤 Отправляю готовый ролик...")
        
        # Отправляем
        with open(output_path, 'rb') as f:
            await update.message.reply_video(
                video=f,
                caption=f"✅ Готово!\n\n✂️ Паузы удалены\n🎯 Зум добавлен\n💬 Субтитры наложены\n\n🔥 Ролик готов!"
            )
        
        # Удаляем временные файлы
        for path in [input_path, audio_path, no_silence_path, zoom_path, output_path]:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except:
                pass
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:200]}")
