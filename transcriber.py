class Transcriber:
    def __init__(self, model="base"):
        self.model = model
        # Если используете реальный Whisper - раскомментируйте:
        # import whisper
        # self.whisper = whisper.load_model(model)
    
    def transcribe(self, audio_path):
        # Заглушка для теста (вернёт фейковые субтитры)
        return [
            {"start": 0.0, "end": 1.5, "text": "Привет мир"},
            {"start": 1.5, "end": 3.0, "text": "Это тестовый ролик"},
            {"start": 3.0, "end": 4.5, "text": "Для проверки работы бота"}
        ]
