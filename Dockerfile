# Используем Python 3.11
FROM python:3.11-slim

# Устанавливаем FFmpeg и другие зависимости
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем requirements
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Скачиваем Whisper модель (base - оптимальный вариант)
RUN python -m whisper download base

# Копируем весь код
COPY main.py .
COPY config.py .
COPY video_processor.py .
COPY transcriber.py .
COPY analyzer.py .
COPY subtitle_generator.py .
COPY effects_engine.py .
COPY database.py .
COPY utils.py .

# Создаём необходимые директории
RUN mkdir -p /app/temp /app/results /app/cache /app/logs

# Запускаем бота
CMD ["python", "main.py"]
