FROM python:3.11-slim

# Установка FFmpeg и зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем requirements
COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY *.py ./

# Создаём директории
RUN mkdir -p temp results cache logs

# Скачиваем Whisper модель (опционально, можно закомментировать если долго)
# RUN python -m whisper download base

# Запуск
CMD ["python", "main.py"]
