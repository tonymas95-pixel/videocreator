#!/usr/bin/env python3
"""
🎬 SHORTS BOT - Автоматический видеомонтаж вертикальных роликов
для Telegram. Превращает сырой видеоисходник в динамичный клип.

Автор: Anton
"""

import logging
import os
import asyncio
from datetime import datetime
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

from config import (
    TELEGRAM_TOKEN,
    TEMP_DIR,
    RESULTS_DIR,
    SUBTITLE_STYLES,
    DEFAULT_STYLE,
    LOG_FILE,
)
from video_processor import VideoProcessor
from utils import setup_logging, get_user_settings, save_user_settings
from database import Database

# Setup logging
logger = setup_logging(LOG_FILE)

# Initialize database
db = Database()

# States for ConversationHandler
WAITING_FOR_VIDEO = 1
WAITING_FOR_COMMENT = 2
WAITING_FOR_PREVIEW_APPROVAL = 3
WAITING_FOR_STYLE_SELECTION = 4


class ShortsBot:
    """Основной класс бота для обработки видео"""

    def __init__(self):
        self.video_processor = VideoProcessor()
        self.user_queues = {}  # Очереди задач на пользователя
        self.processing_tasks = {}  # Текущие задачи

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start - приветствие и инструкция"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "Друже"

        welcome_text = f"""
🎬 Привет, {user_name}! Добро пожаловать в SHORTS BOT! 🚀

Я превращу твой видеоисходник в профессиональный вертикальный клип:
✨ Динамичные субтитры
🎯 Умные зум-акценты на ключевые моменты
🎵 Фоновая музыка
🎨 Визуальные эффекты

📝 КАК ПОЛЬЗОВАТЬСЯ:
1. Отправь мне вертикальное видео (до 3 минут)
2. (Опционально) напиши комментарий с пожеланиями
3. Я сделаю превью для утверждения
4. После твоего "ОК" — вот и готовый клип!

⚙️ Команды:
/help - подробная справка
/settings - мои настройки (стиль, брендинг)
/history - история обработок
/examples - примеры результатов

Готов? Просто отправь видео! 📹
        """

        await update.message.reply_text(welcome_text)
        logger.info(f"User {user_id} started bot")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """
📖 ПОЛНАЯ СПРАВКА

🎬 ОСНОВНОЕ:
Отправь вертикальное видео (9:16, MP4/MOV, до 3 минут).
Я обработаю его за 2-3 минуты и пришлю готовый клип (30-45 сек).

📋 ОПЦИИ:
• Текстовый комментарий: напиши, что улучшить
  ("подчеркни слово 'скидка'", "вырежь паузы", "добавь больше эмодзи")
• Своя музыка: загрузи аудиофайл (MP3, WAV)
• Свой брендинг: настрой плашку через /settings

⚙️ КОМАНДЫ:
/start - начало
/help - эта справка
/settings - настройки (стиль субтитров, цвет, брендинг)
/history - последние 10 обработок
/preview - посмотреть шаблон превью
/clear_cache - очистить кэш

🎨 СТИЛИ СУБТИТРОВ:
• bright - яркие цвета, много эмодзи (по умолчанию)
• minimal - чёрный текст, классика
• cyberpunk - неоновые цвета, выглядит круто

💡 СОВЕТЫ:
1. Снимай вертикально с самого начала
2. Говори чётко, речь должна быть разборчива
3. Лучше короче, чем растягивать
4. Монолог работает лучше, чем разговор с кем-то

❓ ВОПРОСЫ? Напиши @admin

Поехали! 🚀
        """
        await update.message.reply_text(help_text)

    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик загрузки видео"""
        user_id = update.effective_user.id
        message_id = update.message.message_id

        # Сохраняем видео в контекст
        video_file = update.message.video or update.message.document
        if not video_file:
            await update.message.reply_text("❌ Видео не найдено. Попробуй ещё раз.")
            return

        context.user_data["video_file"] = video_file
        context.user_data["user_id"] = user_id
        context.user_data["message_id"] = message_id

        # Проверка размера
        if video_file.file_size > 100 * 1024 * 1024:  # 100 MB
            await update.message.reply_text(
                "❌ Видео слишком большое (макс 100 МБ). Пожалуйста, сожми его."
            )
            return

        # Спрашиваем комментарий
        keyboard = [
            [InlineKeyboardButton("Нет комментариев", callback_data="no_comment")],
            [InlineKeyboardButton("Напишу комментарий", callback_data="add_comment")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "✅ Видео получено! Есть ли пожелания? (опционально)",
            reply_markup=reply_markup,
        )

    async def button_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Обработчик кнопок"""
        query = update.callback_query
        user_id = update.effective_user.id

        if query.data == "no_comment":
            await query.answer()
            context.user_data["comment"] = ""
            await self.process_video_async(update, context)

        elif query.data == "add_comment":
            await query.answer()
            await query.edit_message_text(
                "Напиши свои пожелания (например, 'больше эмодзи', 'выдели слово скидка'):"
            )
            return WAITING_FOR_COMMENT

        elif query.data.startswith("style_"):
            style = query.data.replace("style_", "")
            await query.answer()
            await query.edit_message_text(f"✅ Стиль '{style}' выбран!")
            save_user_settings(user_id, {"style": style})
            await self.process_video_async(update, context)

        elif query.data == "preview_ok":
            await query.answer("✅ Начинаю полную обработку...")
            await self.process_full_video(update, context)

        elif query.data == "preview_retry":
            await query.answer()
            await query.edit_message_text("Какие изменения хочешь?")
            return WAITING_FOR_COMMENT

    async def process_video_async(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Асинхронная обработка видео - создание превью"""
        user_id = update.effective_user.id

        try:
            await update.effective_message.edit_text(
                "🧠 Анализирую видео... Это займёт ~1-2 минуты"
            )

            # Скачиваем видео
            video_file = context.user_data["video_file"]
            file = await context.bot.get_file(video_file.file_id)

            video_path = f"{TEMP_DIR}/input_{user_id}_{datetime.now().timestamp()}.mp4"
            await file.download_to_drive(video_path)

            # Обрабатываем видео
            context.user_data["video_path"] = video_path
            comment = context.user_data.get("comment", "")
            user_settings = get_user_settings(user_id)

            # Создаём превью (первые 10 сек)
            preview_path = await asyncio.to_thread(
                self.video_processor.process_video_with_preview,
                video_path,
                user_id,
                style=user_settings.get("style", DEFAULT_STYLE),
                custom_comment=comment,
            )

            if preview_path and os.path.exists(preview_path):
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "✅ Готово, делай полную!", callback_data="preview_ok"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔄 Переделай что-то", callback_data="preview_retry"
                        )
                    ],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                with open(preview_path, "rb") as video:
                    await context.bot.send_video(
                        user_id,
                        video,
                        caption="📺 Вот превью первых 10 сек. Устраивает стиль?",
                        reply_markup=reply_markup,
                    )

                logger.info(f"Preview generated for user {user_id}")
            else:
                await update.effective_message.reply_text(
                    "❌ Ошибка обработки. Попробуй другое видео."
                )

        except Exception as e:
            logger.error(f"Error processing video for user {user_id}: {e}")
            await update.effective_message.reply_text(
                f"❌ Ошибка: {str(e)[:100]}"
            )

    async def process_full_video(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Полная обработка видео"""
        user_id = update.effective_user.id

        try:
            video_path = context.user_data.get("video_path")
            if not video_path:
                await update.effective_message.reply_text("❌ Видео не найдено.")
                return

            processing_msg = await update.effective_message.reply_text(
                "⚙️ Обрабатываю полное видео... Подожди 2-3 минуты"
            )

            user_settings = get_user_settings(user_id)
            comment = context.user_data.get("comment", "")

            # Полная обработка
            result = await asyncio.to_thread(
                self.video_processor.process_full_video,
                video_path,
                user_id,
                style=user_settings.get("style", DEFAULT_STYLE),
                branding_text=user_settings.get("branding_name", "My Channel"),
                custom_comment=comment,
            )

            if result and result.get("output_video"):
                output_path = result["output_video"]

                # Готовим отчёт
                stats = result.get("stats", {})
                report = f"""
🎉 ГОТОВО! Твой клип готов к публикации!

📊 СТАТИСТИКА:
• Исходная длина: {stats.get('original_duration', 0):.1f} сек
• Итоговая длина: {stats.get('final_duration', 0):.1f} сек
• Сокращено: {stats.get('reduction_percent', 0):.0f}%
• Акцентов: {stats.get('accents_count', 0)}
• Удалено пауз: {stats.get('pauses_removed', 0)}
• Прогнозируемый CTR: {stats.get('predicted_ctr', 0):.0f}%

✨ ЭФФЕКТЫ:
• Динамичные субтитры ✓
• Зум-акценты ✓
• Фоновая музыка ✓
• Брендинг плашка ✓
• Эмодзи и визуальные вставки ✓

📤 Качество: 1080x1920, 30 fps, {stats.get('file_size_mb', 0):.1f} МБ

🚀 Поделись в TikTok, Reels, Shorts!
        """

                # Отправляем видео
                with open(output_path, "rb") as video:
                    await context.bot.send_video(
                        user_id,
                        video,
                        caption=report,
                        width=1080,
                        height=1920,
                    )

                # Сохраняем в историю
                db.save_to_history(
                    user_id,
                    {
                        "input_path": video_path,
                        "output_path": output_path,
                        "stats": stats,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                logger.info(f"Full video processed for user {user_id}")

            else:
                await processing_msg.edit_text(
                    "❌ Ошибка при обработке. Попробуй другое видео."
                )

        except Exception as e:
            logger.error(f"Error in full video processing: {e}")
            await update.effective_message.reply_text(f"❌ Ошибка: {str(e)[:100]}")

    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /settings - настройки пользователя"""
        user_id = update.effective_user.id
        user_settings = get_user_settings(user_id)

        settings_text = f"""
⚙️ ТВОИ НАСТРОЙКИ

🎨 Стиль субтитров: {user_settings.get("style", DEFAULT_STYLE)}
👤 Имя в плашке: {user_settings.get("branding_name", "My Channel")}

Хочешь изменить?
        """

        # Кнопки для выбора стиля
        keyboard = [
            [InlineKeyboardButton(f"🎨 {style}", callback_data=f"style_{style}")]
            for style in SUBTITLE_STYLES.keys()
        ]
        keyboard.append(
            [InlineKeyboardButton("✏️ Изменить имя в плашке", callback_data="edit_branding")]
        )

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(settings_text, reply_markup=reply_markup)

    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /history - история обработок"""
        user_id = update.effective_user.id
        history = db.get_user_history(user_id, limit=5)

        if not history:
            await update.message.reply_text("📭 История пуста. Обработай первое видео!")
            return

        history_text = "📚 ПОСЛЕДНИЕ ОБРАБОТКИ:\n\n"
        for i, record in enumerate(history, 1):
            stats = record.get("stats", {})
            history_text += f"""
{i}. {record.get('timestamp', 'N/A')}
   Original: {stats.get('original_duration', 0):.0f}s → Final: {stats.get('final_duration', 0):.0f}s
   CTR: {stats.get('predicted_ctr', 0):.0f}%
"""

        await update.message.reply_text(history_text)

    async def unknown_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Обработчик неизвестных команд"""
        await update.message.reply_text(
            "❓ Не понимаю эту команду. Используй /help для справки."
        )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений (комментарии)"""
    if context.user_data.get("video_file"):
        context.user_data["comment"] = update.message.text
        await update.message.reply_text(
            "✅ Комментарий сохранён! Начинаю обработку..."
        )
        # Продолжаем обработку
        bot = ShortsBot()
        await bot.process_video_async(update, context)


def main():
    """Запуск бота"""
    logger.info("🚀 Starting SHORTS BOT...")

    # Создаём приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Инициализируем бот
    shorts_bot = ShortsBot()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", shorts_bot.start))
    application.add_handler(CommandHandler("help", shorts_bot.help_command))
    application.add_handler(CommandHandler("settings", shorts_bot.settings_command))
    application.add_handler(CommandHandler("history", shorts_bot.history_command))

    # Обработчик видео
    application.add_handler(
        MessageHandler(filters.VIDEO | filters.Document.ALL, shorts_bot.handle_video)
    )

    # Обработчик кнопок
    application.add_handler(CallbackQueryHandler(shorts_bot.button_callback))

    # Обработчик текста
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # Неизвестные команды
    application.add_handler(
        MessageHandler(filters.COMMAND, shorts_bot.unknown_command)
    )

    # Создаём директории если их нет
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Запускаем бота
    logger.info(f"Bot token configured. Starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
