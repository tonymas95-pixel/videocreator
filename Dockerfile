FROM python:3.11-slim

# Установка FFmpeg и зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем requirements
COPY requirements.txt .

# Обновляем setuptools перед pip install
RUN pip install --upgrade setuptools

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY *.py ./

# Создаём директории
RUN mkdir -p temp results cache logs

# Запуск
CMD ["python", "main.py"]
