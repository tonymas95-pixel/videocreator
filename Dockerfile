FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install setuptools==69.5.1 wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY *.py ./

RUN mkdir -p temp results cache logs

CMD ["python", "main.py"]
