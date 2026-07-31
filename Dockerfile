FROM python:3.11-slim

# Установка FFmpeg и системных зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем requirements и устанавливаем
COPY requirements.txt .

# Устанавливаем все зависимости
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY *.py ./

# Создаём директории
RUN mkdir -p temp results cache logs

# Запуск
CMD ["python", "main.py"]
