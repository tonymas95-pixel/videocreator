#!/usr/bin/env python3
import os
import logging
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import Config
from database import Database
from video_processor_logic import handle_video

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

for folder in [Config.TEMP_DIR, Config.RESULTS_DIR, Config.CACHE_DIR]:
    Path(folder).mkdir(parents=True, exist_ok=True)

db = Database()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Привет! Отправь мне видео (до 300 МБ).\n\n"
        "Я сделаю:\n"
        "✅ Удалю паузы\n"
        "✅ Добавлю зум-эффект\n"
        "✅ Наложу субтитры\n"
        "✅ Сохраню качество"
    )

def main():
    logger.info("🚀 Starting SHORTS BOT...")
    
    if not Config.TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN not set!")
        return
    
    app = Application.builder().token(Config.TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
    logger.info("✅ Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
