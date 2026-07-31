FROM python:3.11-slim

# Установка FFmpeg и зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем requirements
COPY requirements.txt .

# Обновляем pip и устанавливаем зависимости
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY main.py .
COPY video_editor.py .
COPY config.py .
COPY database.py .
COPY utils.py .

# Создаём необходимые директории
RUN mkdir -p temp results cache logs

# Экспортируем порт (если нужен webhook)
EXPOSE 8080

# Запуск бота
CMD ["python", "main.py"]
