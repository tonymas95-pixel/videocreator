import os
import logging
import uuid
from moviepy.editor import VideoFileClip
from config import Config
from database import Database

logger = logging.getLogger(__name__)
db = Database()

async def handle_video(update, context):
    """Обработчик видео - обрезка до 30 секунд"""
    user_id = update.effective_user.id
    
    # Сохраняем пользователя
    user = update.effective_user
    db.save_user(user_id, user.username, user.first_name, user.last_name)
    
    try:
        # Отправляем сообщение о начале
        msg = await update.message.reply_text("🎬 Обрабатываю видео...")
        
        # Скачиваем видео
        video_file = await update.message.video.get_file()
        input_path = f"{Config.TEMP_DIR}/input_{user_id}_{uuid.uuid4()}.mp4"
        await video_file.download_to_drive(input_path)
        
        # Загружаем видео
        clip = VideoFileClip(input_path)
        original_duration = clip.duration
        
        # Обрезаем до 30 секунд
        if clip.duration > 30:
            clip = clip.subclip(0, 30)
        
        # Уменьшаем размер (делаем вертикальным)
        clip = clip.resize(height=720)
        
        # Сохраняем результат
        output_path = f"{Config.RESULTS_DIR}/result_{user_id}_{uuid.uuid4()}.mp4"
        clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=24,
            verbose=False,
            logger=None
        )
        
        clip.close()
        
        # Записываем в БД
        db.add_process(user_id, int(original_duration), 30, 0, False)
        
        # Отправляем результат
        with open(output_path, 'rb') as f:
            await update.message.reply_video(
                video=f,
                caption=f"✅ Готово!\n\n📹 Исходная длина: {int(original_duration)} сек\n✂️ Обрезано до: 30 сек\n\n🔥 Отправь следующее видео!"
            )
        
        # Удаляем временные файлы
        os.remove(input_path)
        os.remove(output_path)
        
    except Exception as e:
        logger.error(f"Video processing error: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:200]}")
