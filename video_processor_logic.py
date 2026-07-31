import os
import logging
import uuid
from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)

async def process_video_logic(update, context, is_preview=False):
    """Простая обработка видео - обрезка до 30 секунд"""
    user_id = update.effective_user.id
    
    try:
        # Скачиваем видео
        video_file = await update.message.video.get_file()
        input_path = f"/app/temp/input_{user_id}_{uuid.uuid4()}.mp4"
        await video_file.download_to_drive(input_path)
        
        await update.message.reply_text("🎬 Обрабатываю видео...")
        
        # Загружаем видео
        clip = VideoFileClip(input_path)
        
        # Обрезаем до 30 секунд
        if clip.duration > 30:
            clip = clip.subclip(0, 30)
        
        # Уменьшаем размер (делаем вертикальным)
        clip = clip.resize(height=720)
        
        # Сохраняем результат
        output_path = f"/app/results/result_{user_id}_{uuid.uuid4()}.mp4"
        clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=24
        )
        
        clip.close()
        
        # Отправляем результат
        with open(output_path, 'rb') as f:
            await update.message.reply_video(
                video=f,
                caption="✅ Готово! Видео обрезано до 30 секунд."
            )
        
        # Удаляем временные файлы
        os.remove(input_path)
        os.remove(output_path)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:200]}")

async def handle_video(update, context):
    """Обработчик видео"""
    await process_video_logic(update, context, is_preview=False)
