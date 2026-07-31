import requests
import json
import os

class Transcriber:
    def __init__(self):
        # Бесплатный ключ от Google (можно получить в Google Cloud)
        self.api_key = os.getenv("GOOGLE_API_KEY", "")
    
    def transcribe(self, audio_path):
        """Транскрибирует аудио через Google Speech API"""
        if not self.api_key:
            # Если нет ключа - возвращаем заглушку
            return self._mock_transcription()
        
        url = f"https://speech.googleapis.com/v1/speech:recognize?key={self.api_key}"
        
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        
        payload = {
            "config": {
                "encoding": "LINEAR16",
                "sampleRateHertz": 16000,
                "languageCode": "ru-RU",
                "enableWordTimeOffsets": True
            },
            "audio": {
                "content": audio_data.decode('latin1')
            }
        }
        
        response = requests.post(url, json=payload)
        return self._parse_response(response.json())
    
    def _parse_response(self, data):
        """Парсит ответ от Google"""
        segments = []
        if 'results' in data:
            for result in data['results']:
                for alt in result['alternatives']:
                    for word in alt.get('words', []):
                        segments.append({
                            'start': float(word['startTime'].replace('s', '')),
                            'end': float(word['endTime'].replace('s', '')),
                            'text': word['word']
                        })
        return segments
    
    def _mock_transcription(self):
        """Заглушка для тестирования"""
        return [
            {'start': 0.0, 'end': 1.0, 'text': 'Привет'},
            {'start': 1.0, 'end': 2.0, 'text': 'мир'}
        ]
