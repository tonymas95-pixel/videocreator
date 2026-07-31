#!/usr/bin/env python3
import os
import logging
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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, Config.LOG_LEVEL)
)
logger = logging.getLogger(__name__)

for folder in [Config.TEMP_DIR, Config.RESULTS_DIR, Config.CACHE_DIR]:
    Path(folder).mkdir(parents=True, exist_ok=True)

db = Database()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"User {user.id} started bot")
    
    db.save_user(user.id, user.username, user.first_name, user.last_name)
    
    text = (
        f"🎬 Привет, {user.first_name}!\n\n"
        "Я бот для обрезки вертикальных видео.\n\n"
        "📹 Отправь мне видео, и я обрежу его до 30 секунд!"
    )
    
    keyboard = [
        [InlineKeyboardButton("📖 Инструкция", callback_data="help")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        await query.message.reply_text(
            "📖 Инструкция:\n\n"
            "1. Отправь видео (MP4/MOV)\n"
            "2. Вертикальное (9:16)\n"
            "3. До 45 МБ\n"
            "4. Я обрежу до 30 секунд"
        )
    elif query.data == "stats":
        user_id = update.effective_user.id
        stats = db.get_user_stats(user_id)
        if stats:
            await query.message.reply_text(
                f"📊 Статистика:\n"
                f"📹 Обработано: {stats['total']} видео\n"
                f"⏱ Всего: {stats['total_time']} сек"
            )
        else:
            await query.message.reply_text("📊 Пока нет обработанных видео.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    logger.info("🚀 Starting SHORTS BOT...")
    
    if not Config.TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN not set!")
        return
    
    application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_error_handler(error_handler)
    
    logger.info("✅ Bot started!")
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
