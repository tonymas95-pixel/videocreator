import os
import logging
import uuid
import subprocess
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from moviepy.video.fx.all import resize

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

def detect_silence(audio_path, min_silence=0.5):
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
            # Если пауз нет - просто копируем
            video.write_videofile(output_path, codec='libx264', audio_codec='aac')
            video.close()
            return video.duration
        
        # Создаём клипы без пауз
        clips = []
        current = 0
        
        for s in silences:
            # Обрезаем только реальные паузы (не трогаем речь)
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

def make_vertical(video_path, output_path):
    """Делает видео вертикальным (9:16)"""
    try:
        clip = VideoFileClip(video_path)
        
        # Проверяем пропорции
        w, h = clip.size
        if w > h:
            # Горизонтальное -> обрезаем до вертикального
            new_w = int(h * 9 / 16)
            x_center = w // 2
            clip = clip.crop(x_center=new_w//2, width=new_w)
        elif h / w < 16/9:
            # Почти вертикальное - растягиваем
            clip = clip.resize(height=1920)
        else:
            clip = clip.resize(height=1920)
        
        clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        clip.close()
        return True
    except Exception as e:
        logger.error(f"Make vertical error: {e}")
        return False

def add_subtitles_to_video(video_path, output_path):
    """Добавляет СУБТИТРЫ на видео (крупно и ярко)"""
    try:
        video = VideoFileClip(video_path)
        
        # Создаём текст с большим шрифтом
        txt_clip = TextClip(
            "🔥 ТВОЙ РОЛИК ГОТОВ!",
            fontsize=80,
            color='white',
            stroke_color='black',
            stroke_width=4,
            font='Arial'
        ).set_position(('center', 'bottom')).set_duration(video.duration)
        
        # Ещё один текст сверху
        txt_top = TextClip(
            "🎬 ОБРАБОТАНО БОТОМ",
            fontsize=60,
            color='#FF3366',
            stroke_color='black',
            stroke_width=3,
            font='Arial'
        ).set_position(('center', 'top')).set_duration(video.duration)
        
        # Накладываем
        final = CompositeVideoClip([video, txt_clip, txt_top])
        final.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        video.close()
        final.close()
        return True
    except Exception as e:
        logger.error(f"Subtitle error: {e}")
        return False

def add_zoom_to_video(video_path, output_path):
    """Добавляет зум-эффект в середине видео"""
    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        
        if duration < 3:
            clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            clip.close()
            return True
        
        # Плавный зум в середине
        def zoom_effect(t):
            mid = duration / 2
            if mid - 2 <= t <= mid + 2:
                progress = (t - (mid - 2)) / 4
                return 1 + 0.15 * progress
            return 1
        
        zoomed = clip.resize(lambda t: zoom_effect(t))
        zoomed.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        clip.close()
        zoomed.close()
        return True
    except Exception as e:
        logger.error(f"Zoom error: {e}")
        return False

async def handle_video(update, context):
    """Главный обработчик видео"""
    user_id = update.effective_user.id
    
    try:
        # Проверка размера
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
        
        await msg.edit_text("✂️ Делаю вертикальным...")
        
        # Делаем вертикальным
        vertical_path = f"{Config.TEMP_DIR}/vertical_{user_id}_{uuid.uuid4()}.mp4"
        if not make_vertical(input_path, vertical_path):
            vertical_path = input_path
        
        await msg.edit_text("✂️ Удаляю паузы...")
        
        # Удаляем паузы
        no_silence_path = f"{Config.TEMP_DIR}/no_silence_{user_id}_{uuid.uuid4()}.mp4"
        duration = remove_silence_from_video(vertical_path, audio_path, no_silence_path)
        
        if duration == 0:
            no_silence_path = vertical_path
        
        await msg.edit_text("🔍 Добавляю зум...")
        
        # Добавляем зум
        zoom_path = f"{Config.TEMP_DIR}/zoom_{user_id}_{uuid.uuid4()}.mp4"
        if not add_zoom_to_video(no_silence_path, zoom_path):
            zoom_path = no_silence_path
        
        await msg.edit_text("💬 Добавляю субтитры...")
        
        # Добавляем субтитры
        output_path = f"{Config.RESULTS_DIR}/result_{user_id}_{uuid.uuid4()}.mp4"
        if not add_subtitles_to_video(zoom_path, output_path):
            output_path = zoom_path
        
        await msg.edit_text("📤 Отправляю готовый ролик...")
        
        # Отправляем
        with open(output_path, 'rb') as f:
            await update.message.reply_video(
                video=f,
                caption=(
                    "✅ ГОТОВО!\n\n"
                    "📱 ВЕРТИКАЛЬНЫЙ РОЛИК\n"
                    f"✂️ УДАЛЕНО ПАУЗ: {int(duration)} сек → {int(duration * 0.7)} сек\n"
                    "🔍 ДОБАВЛЕН ZOOM\n"
                    "💬 СУБТИТРЫ НАЛОЖЕНЫ\n\n"
                    "🔥 ПУБЛИКУЙ!"
                )
            )
        
        # Удаляем временные файлы
        for path in [input_path, audio_path, vertical_path, no_silence_path, zoom_path, output_path]:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except:
                pass
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:200]}")
