"""
SHORTS BOT v2.0 - Professional Video Editor
Полностью переписанный бот с реальной обработкой видео
"""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from video_editor import VideoEditor

# ============================================================================
# НАСТРОЙКА
# ============================================================================

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Директории
TEMP_DIR = Path("temp")
RESULTS_DIR = Path("results")
for dir_path in [TEMP_DIR, RESULTS_DIR]:
    dir_path.mkdir(exist_ok=True)

# Максимальный размер файла (400MB)
MAX_FILE_SIZE = 400 * 1024 * 1024

# ============================================================================
# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ ХРАНЕНИЯ СОСТОЯНИЯ
# ============================================================================

user_videos = {}  # {user_id: {"path": str, "info": dict}}
user_settings = {}  # {user_id: {"effects": list, ...}}

# ============================================================================
# ОБРАБОТЧИКИ КОМАНД
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start"""
    user = update.effective_user
    welcome_text = f"""
👋 Привет, {user.first_name}!

🎬 Я - профессиональный видеоредактор для вертикальных роликов!

📤 Просто отправь мне видео (MP4, MOV, MKV, AVI)
📝 Я проанализирую и предложу улучшения
🎯 Ты выберешь нужные функции
✨ Получишь готовый ролик!

⚡ Поддерживаю файлы до 400MB

Команды:
/start - помощь
/settings - мои предпочтения
/help - полная справка
"""
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help"""
    help_text = """
🎬 ДОСТУПНЫЕ ФУНКЦИИ:

✂️ **Вырезание пауз**
Удаляет все паузы > 0.5 сек
Сокращает видео без потери смысла

🗣️ **Удаление повторов**
Убирает дубли и повторяющиеся фразы
Анализирует похожесть текста

🎯 **Зумирование кадров**
Добавляет динамичные зумы
На важные моменты (опционально)

📝 **Субтитры**
Накладывает красивые субтитры
4 стиля: ярких, минимальный, киберпанк, теплый

😊 **Эмоджи**
Добавляет релевантные эмоджи
На ключевые слова

🎨 **Улучшение качества**
Убирает шумы
Выравнивает звук

📊 **Исправление разрешения**
Переводит в 9:16 (вертикальное)
БЕЗ потери качества

🎵 **Добавление фоновой музыки**
Добавляет в моменты пауз
С динамической громкостью

⚙️ **Все сразу**
Применяет оптимальный набор функций

Просто отправь видео и выбери нужное!
"""
    await update.message.reply_text(help_text)


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка загруженного видео"""
    user_id = update.effective_user.id
    message = update.message

    # Получаем видеофайл
    if message.video:
        file = message.video
    elif message.document:
        file = message.document
    else:
        await message.reply_text("❌ Неподдерживаемый формат файла")
        return

    # Проверяем размер
    if file.file_size > MAX_FILE_SIZE:
        await message.reply_text(
            f"❌ Файл слишком большой!\n\n"
            f"Максимум: 400MB\n"
            f"Ваш файл: {file.file_size / (1024*1024):.1f}MB"
        )
        return

    # Скачиваем файл
    await message.reply_text("⏳ Загружаю видео...")

    try:
        file_obj = await context.bot.get_file(file.file_id)
        video_path = TEMP_DIR / f"video_{user_id}_{file.file_unique_id}.mp4"
        await file_obj.download_to_drive(video_path)

        logger.info(f"Video downloaded: {video_path} ({file.file_size / (1024*1024):.1f}MB)")

        # Анализируем видео
        await message.reply_text("🔍 Анализирую видео...")
        editor = VideoEditor()
        info = editor.analyze_video(str(video_path))

        if not info:
            await message.reply_text("❌ Не удалось обработать видео")
            return

        # Сохраняем информацию
        user_videos[user_id] = {"path": str(video_path), "info": info}

        # Показываем анализ
        analysis_text = f"""
📊 АНАЛИЗ ВИДЕО:

📏 Разрешение: {info['width']}x{info['height']}
{'✅ Вертикальное (9:16)' if info['width'] < info['height'] else '⚠️ Горизонтальное - переведу в 9:16'}

⏱️ Длительность: {format_duration(info['duration'])}

🎬 Fps: {info['fps']:.0f}

💾 Размер: {info['file_size_mb']:.1f}MB

🔊 Аудио: {'✅ Есть' if info['has_audio'] else '❌ Нет'}

Качество: {'Хорошее' if info['bitrate'] > 5000 else 'Среднее' if info['bitrate'] > 2000 else 'Низкое'}

─────────────────────

🎯 ЧТО ХОЧЕШЬ СДЕЛАТЬ?
"""
        await message.reply_text(analysis_text)

        # Показываем кнопки выбора
        await show_editing_options(update, context, user_id)

    except Exception as e:
        logger.error(f"Error processing video: {e}")
        await message.reply_text(f"❌ Ошибка при обработке видео: {e}")


async def show_editing_options(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """Показываем кнопки для выбора функций"""
    keyboard = [
        [
            InlineKeyboardButton("✂️ Вырезать паузы", callback_data=f"opt_{user_id}_pauses"),
            InlineKeyboardButton("🗣️ Удалить повторы", callback_data=f"opt_{user_id}_duplicates"),
        ],
        [
            InlineKeyboardButton("🎯 Зумирование", callback_data=f"opt_{user_id}_zoom"),
            InlineKeyboardButton("📝 Субтитры", callback_data=f"opt_{user_id}_subtitles"),
        ],
        [
            InlineKeyboardButton("😊 Эмоджи", callback_data=f"opt_{user_id}_emoji"),
            InlineKeyboardButton("🎨 Улучшить качество", callback_data=f"opt_{user_id}_enhance"),
        ],
        [
            InlineKeyboardButton("📊 Исправить разрешение", callback_data=f"opt_{user_id}_resolution"),
            InlineKeyboardButton("🎵 Фоновая музыка", callback_data=f"opt_{user_id}_music"),
        ],
        [
            InlineKeyboardButton("⚙️ ВСЁ СРАЗУ", callback_data=f"opt_{user_id}_all"),
            InlineKeyboardButton("✅ Готово", callback_data=f"opt_{user_id}_done"),
        ],
        [
            InlineKeyboardButton("❌ Отмена", callback_data=f"opt_{user_id}_cancel"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            "Выбери функции обработки (можно несколько):",
            reply_markup=reply_markup
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            "Выбери функции обработки (можно несколько):",
            reply_markup=reply_markup
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатий кнопок"""
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split("_")
    user_id = int(parts[1])
    action = parts[2]

    if user_id not in user_videos:
        await query.edit_message_text("❌ Видео не найдено. Загрузи видео заново.")
        return

    # Инициализируем настройки пользователя если нужно
    if user_id not in user_settings:
        user_settings[user_id] = {"effects": []}

    # Обработка действий
    if action == "pauses":
        user_settings[user_id]["effects"].append("pauses")
        await query.edit_message_text("✂️ Добавлено: вырезание пауз\n\nВыбери ещё или готово?", 
                                     reply_markup=get_editing_keyboard(user_id))

    elif action == "duplicates":
        user_settings[user_id]["effects"].append("duplicates")
        await query.edit_message_text("🗣️ Добавлено: удаление повторов\n\nВыбери ещё или готово?",
                                     reply_markup=get_editing_keyboard(user_id))

    elif action == "zoom":
        user_settings[user_id]["effects"].append("zoom")
        await query.edit_message_text("🎯 Добавлено: зумирование\n\nВыбери ещё или готово?",
                                     reply_markup=get_editing_keyboard(user_id))

    elif action == "subtitles":
        # Показываем выбор стиля субтитров
        keyboard = [
            [InlineKeyboardButton("✨ Яркий", callback_data=f"sub_{user_id}_bright")],
            [InlineKeyboardButton("⚫ Минимальный", callback_data=f"sub_{user_id}_minimal")],
            [InlineKeyboardButton("🌐 Киберпанк", callback_data=f"sub_{user_id}_cyberpunk")],
            [InlineKeyboardButton("🔥 Теплый", callback_data=f"sub_{user_id}_warm")],
            [InlineKeyboardButton("❌ Без субтитров", callback_data=f"opt_{user_id}_back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📝 Выбери стиль субтитров:", reply_markup=reply_markup)

    elif action == "emoji":
        user_settings[user_id]["effects"].append("emoji")
        await query.edit_message_text("😊 Добавлено: эмоджи\n\nВыбери ещё или готово?",
                                     reply_markup=get_editing_keyboard(user_id))

    elif action == "enhance":
        user_settings[user_id]["effects"].append("enhance")
        await query.edit_message_text("🎨 Добавлено: улучшение качества\n\nВыбери ещё или готово?",
                                     reply_markup=get_editing_keyboard(user_id))

    elif action == "resolution":
        user_settings[user_id]["effects"].append("resolution")
        await query.edit_message_text("📊 Добавлено: коррекция разрешения\n\nВыбери ещё или готово?",
                                     reply_markup=get_editing_keyboard(user_id))

    elif action == "music":
        user_settings[user_id]["effects"].append("music")
        await query.edit_message_text("🎵 Добавлено: фоновая музыка\n\nВыбери ещё или готово?",
                                     reply_markup=get_editing_keyboard(user_id))

    elif action == "all":
        user_settings[user_id]["effects"] = ["pauses", "duplicates", "zoom", "subtitles", "emoji", "enhance"]
        user_settings[user_id]["subtitle_style"] = "bright"
        await query.edit_message_text(
            "⚙️ Выбраны все функции!\n\n"
            "Функции:\n"
            "✂️ Вырезание пауз\n"
            "🗣️ Удаление повторов\n"
            "🎯 Зумирование\n"
            "📝 Субтитры (яркий стиль)\n"
            "😊 Эмоджи\n"
            "🎨 Улучшение качества\n\n"
            "Нажми 'Обработать', когда готов!"
        )
        await show_process_button(query, user_id)

    elif action == "done":
        effects = user_settings[user_id].get("effects", [])
        if not effects:
            await query.edit_message_text("❌ Выбери хотя бы одну функцию!")
            return

        # Показываем финальное подтверждение
        effects_text = "\n".join([get_effect_name(e) for e in effects])
        keyboard = [
            [InlineKeyboardButton("✅ Обработать!", callback_data=f"process_{user_id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data=f"opt_{user_id}_back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📋 Выбранные функции:\n{effects_text}\n\n"
            "Нажми 'Обработать!' чтобы начать!",
            reply_markup=reply_markup
        )

    elif action == "back":
        await show_editing_options(query, context, user_id)

    elif action == "cancel":
        if user_id in user_videos:
            try:
                Path(user_videos[user_id]["path"]).unlink()
            except:
                pass
            del user_videos[user_id]
        if user_id in user_settings:
            del user_settings[user_id]
        await query.edit_message_text("❌ Отменено")

    # Обработка выбора стиля субтитров
    elif action.startswith("sub_"):
        style = "_".join(action.split("_")[2:])
        user_settings[user_id]["effects"].append("subtitles")
        user_settings[user_id]["subtitle_style"] = style
        await query.edit_message_text(
            f"📝 Субтитры ({style})добавлены\n\nВыбери ещё или готово?",
            reply_markup=get_editing_keyboard(user_id)
        )


async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка видео с выбранными функциями"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = int(data.split("_")[1])

    if user_id not in user_videos or user_id not in user_settings:
        await query.edit_message_text("❌ Ошибка: данные не найдены")
        return

    video_path = user_videos[user_id]["path"]
    effects = user_settings[user_id].get("effects", [])

    await query.edit_message_text(
        "⏳ Обрабатываю видео...\n\n"
        "Это может занять время в зависимости от размера файла"
    )

    try:
        editor = VideoEditor()
        output_path = editor.process_video(
            video_path,
            effects=effects,
            subtitle_style=user_settings[user_id].get("subtitle_style", "bright"),
            user_id=user_id
        )

        if not output_path or not Path(output_path).exists():
            await query.edit_message_text("❌ Ошибка при обработке видео")
            return

        file_size_mb = Path(output_path).stat().st_size / (1024 * 1024)

        # Отправляем видео
        await query.edit_message_text(
            f"✅ Видео готово! ({file_size_mb:.1f}MB)\n\n"
            "📤 Загружаю..."
        )

        with open(output_path, "rb") as video_file:
            await context.bot.send_video(
                chat_id=query.from_user.id,
                video=video_file,
                caption="✨ Готовое видео!\n\n"
                        "Ещё одно видео обработать? /start"
            )

        # Очищаем временные файлы
        try:
            Path(video_path).unlink()
            Path(output_path).unlink()
        except:
            pass

        await query.edit_message_text(
            "✅ Видео отправлено!\n\n"
            "Хочешь обработать ещё одно? /start"
        )

        # Очищаем данные
        if user_id in user_videos:
            del user_videos[user_id]
        if user_id in user_settings:
            del user_settings[user_id]

    except Exception as e:
        logger.error(f"Error processing video: {e}")
        await query.edit_message_text(f"❌ Ошибка: {e}")


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def get_effect_name(effect: str) -> str:
    """Получить имя эффекта по коду"""
    names = {
        "pauses": "✂️ Вырезание пауз",
        "duplicates": "🗣️ Удаление повторов",
        "zoom": "🎯 Зумирование",
        "subtitles": "📝 Субтитры",
        "emoji": "😊 Эмоджи",
        "enhance": "🎨 Улучшение качества",
        "resolution": "📊 Исправление разрешения",
        "music": "🎵 Фоновая музыка",
    }
    return names.get(effect, effect)


def get_editing_keyboard(user_id: int):
    """Получить клавиатуру для продолжения выбора"""
    keyboard = [
        [
            InlineKeyboardButton("✂️ Паузы", callback_data=f"opt_{user_id}_pauses"),
            InlineKeyboardButton("🗣️ Повторы", callback_data=f"opt_{user_id}_duplicates"),
        ],
        [
            InlineKeyboardButton("🎯 Зум", callback_data=f"opt_{user_id}_zoom"),
            InlineKeyboardButton("📝 Субтитры", callback_data=f"opt_{user_id}_subtitles"),
        ],
        [
            InlineKeyboardButton("😊 Эмоджи", callback_data=f"opt_{user_id}_emoji"),
            InlineKeyboardButton("🎨 Качество", callback_data=f"opt_{user_id}_enhance"),
        ],
        [
            InlineKeyboardButton("✅ Готово!", callback_data=f"opt_{user_id}_done"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"opt_{user_id}_cancel"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def show_process_button(query, user_id: int):
    """Показать кнопку обработки"""
    keyboard = [[InlineKeyboardButton("✅ Обработать!", callback_data=f"process_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Всё готово!\n\nНажми кнопку ниже для обработки",
        reply_markup=reply_markup
    )


def format_duration(seconds: float) -> str:
    """Форматировать длительность"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Запуск бота"""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN not found in .env")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # Обработчики сообщений
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, handle_video))

    # Обработчики кнопок
    app.add_handler(CallbackQueryHandler(button_callback, pattern=r"^opt_"))
    app.add_handler(CallbackQueryHandler(button_callback, pattern=r"^sub_"))
    app.add_handler(CallbackQueryHandler(process_video, pattern=r"^process_"))

    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
