import sqlite3
import logging
from datetime import datetime
from config import DB_FILE

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_file = DB_FILE
        self.init_db()
    
    def init_db(self):
        """Создаёт таблицы если их нет"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TEXT,
                    last_activity TEXT
                )
            ''')
            
            # Таблица обработок
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    video_duration INTEGER,
                    output_duration INTEGER,
                    processing_time INTEGER,
                    is_preview INTEGER,
                    created_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица настроек
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    user_id INTEGER PRIMARY KEY,
                    font_size INTEGER DEFAULT 40,
                    font_color TEXT DEFAULT 'white',
                    highlight_color TEXT DEFAULT '#FF3366',
                    music_volume INTEGER DEFAULT 30,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database init error: {e}")
    
    def get_user(self, user_id):
        """Получает пользователя"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None
    
    def save_user(self, user_id, username=None, first_name=None, last_name=None):
        """Сохраняет пользователя"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_name, created_at, last_activity)
                VALUES (?, ?, ?, ?, COALESCE((SELECT created_at FROM users WHERE user_id = ?), ?), ?)
            ''', (user_id, username, first_name, last_name, user_id, now, now))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Save user error: {e}")
            return False
    
    def add_process(self, user_id, video_duration, output_duration, processing_time, is_preview=False):
        """Добавляет запись об обработке"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO processes 
                (user_id, video_duration, output_duration, processing_time, is_preview, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, video_duration, output_duration, processing_time, int(is_preview), now))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Add process error: {e}")
            return False
    
    def get_user_stats(self, user_id):
        """Получает статистику пользователя"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(output_duration) as total_time,
                    MAX(created_at) as last_used
                FROM processes 
                WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] > 0:
                return {
                    "total": result[0],
                    "total_time": result[1] or 0,
                    "last_used": result[2] or "Никогда"
                }
            return None
        except Exception as e:
            logger.error(f"Get stats error: {e}")
            return None
    
    def get_user_settings(self, user_id):
        """Получает настройки пользователя"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM settings WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "font_size": result[1],
                    "font_color": result[2],
                    "highlight_color": result[3],
                    "music_volume": result[4]
                }
            return None
        except Exception as e:
            logger.error(f"Get settings error: {e}")
            return None
    
    def save_settings(self, user_id, **kwargs):
        """Сохраняет настройки пользователя"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Получаем текущие настройки
            current = self.get_user_settings(user_id)
            if not current:
                current = {
                    "font_size": 40,
                    "font_color": "white",
                    "highlight_color": "#FF3366",
                    "music_volume": 30
                }
            
            # Обновляем
            for key, value in kwargs.items():
                if key in current:
                    current[key] = value
            
            cursor.execute('''
                INSERT OR REPLACE INTO settings 
                (user_id, font_size, font_color, highlight_color, music_volume)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, current["font_size"], current["font_color"], 
                  current["highlight_color"], current["music_volume"]))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Save settings error: {e}")
            return False
