#!/usr/bin/env python3
"""
SHORTS BOT — Telegram бот для автоматического монтажа вертикальных видео
"""

import os
import logging
import asyncio
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from config import Config
from database import Database
from video_processor_logic import handle_video

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, Config.LOG_LEVEL)
)
logger = logging.getLogger(__name__)

# Создаём папки
for folder in [Config.TEMP_DIR, Config.RESULTS_DIR, Config.CACHE_DIR]:
    Path(folder).mkdir(parents=True, exist_ok=True)

# Инициализация БД
db = Database()

# Хранилище состояний пользователей
user_states = {}

# Команда /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"User {user.id} started bot")
    
    welcome_text = (
        f"🎬 Привет, {user.first_name}!\n\n"
        "Я бот для автоматического монтажа вертикальных видео (Reels/TikTok/Shorts).\n\n"
        "📹 Как я работаю:\n"
        "1. Отправь мне любое видео (30-120 секунд)\n"
        "2. Я обрежу его до 30 секунд\n"
        "3. Получишь готовый ролик!\n\n"
        "🔥 В будущем добавлю: субтитры, зум-эффекты, музыку и акценты!"
    )
    
    keyboard = [
        [InlineKeyboardButton("📖 Инструкция", callback_data="help")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 Инструкция:\n\n"
        "1. Отправь мне видео (MP4/MOV)\n"
        "2. Видео должно быть вертикальным (9:16)\n"
        "3. Длительность: 30-120 секунд\n"
        "4. Я обрежу его до 30 секунд и отправлю обратно\n\n"
        "⚠️ Если видео слишком большое — я уменьшу качество.\n\n"
        "🚀 Скоро будут доступны:\n"
        "• Субтитры\n"
        "• Зум-эффекты\n"
        "• Фоновая музыка\n"
        "• Акценты на ключевых словах"
    )
    await update.message.reply_text(help_text)

# Команда /stats
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stats = db.get_user_stats(user_id)
    
    if stats:
        text = (
            "📊 Ваша статистика:\n\n"
            f"📹 Обработано видео: {stats['total']}\n"
            f"⏱ Всего времени: {stats['total_time']} сек\n"
            f"📅 Последний раз: {stats['last_used']}"
        )
    else:
        text = "📊 Вы ещё не обрабатывали видео. Отправьте мне видео!"
    
    await update.message.reply_text(text)

# Обработчик нажатий на кнопки
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        await help_command(update, context)
    elif query.data == "stats":
        await stats_command(update, context)

# Обработчик текстовых сообщений
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    
    if text in ["привет", "hi", "hello", "здарова"]:
        await update.message.reply_text("👋 Привет! Отправь мне видео для обработки.")
    else:
        await update.message.reply_text(
            "📹 Отправь мне видео, и я обработаю его!\n"
            "Или напиши /help для инструкции."
        )

# Обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Произошла ошибка. Попробуй позже или отправь другое видео."
        )

# Главная функция
def main():
    """Запуск бота"""
    logger.info("🚀 Starting SHORTS BOT...")
    
    # Проверка токена
    if not Config.TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN not set in environment variables!")
        return
    
    # Создаём приложение
    application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Обработчик ВИДЕО (главный!)
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
    # Обработчик текста
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запуск
    logger.info("✅ Bot started! Waiting for messages...")
    application.run_polling(
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
