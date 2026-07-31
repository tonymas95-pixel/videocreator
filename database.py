"""
Database module - SQLite database for user data and history
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from config import DB_FILE, DATABASE_SETTINGS

logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с базой данных"""

    def __init__(self):
        self.db_path = Path(DB_FILE)
        self.logger = logging.getLogger(__name__)
        self._init_database()

    def _init_database(self):
        """Инициализация базы данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Таблица пользователей
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        created_at TIMESTAMP,
                        style TEXT DEFAULT 'bright',
                        branding_name TEXT
                    )
                """)
                
                # Таблица истории обработок
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS processing_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        input_path TEXT,
                        output_path TEXT,
                        stats TEXT,
                        timestamp TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES users(user_id)
                    )
                """)
                
                # Таблица кэша
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cache (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        expires_at TIMESTAMP
                    )
                """)
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")

    def save_user(self, user_id, username, first_name):
        """Сохранение данных пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO users (user_id, username, first_name, created_at)
                    VALUES (?, ?, ?, ?)
                """, (user_id, username, first_name, datetime.now()))
                conn.commit()
                self.logger.info(f"User {user_id} saved")
        except Exception as e:
            self.logger.error(f"Failed to save user: {e}")

    def save_to_history(self, user_id, data):
        """Сохранение записи в историю"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO processing_history (user_id, input_path, output_path, stats, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    user_id,
                    data.get("input_path", ""),
                    data.get("output_path", ""),
                    str(data.get("stats", {})),
                    data.get("timestamp", datetime.now())
                ))
                conn.commit()
                self.logger.info(f"History saved for user {user_id}")
        except Exception as e:
            self.logger.error(f"Failed to save history: {e}")

    def get_user_history(self, user_id, limit=10):
        """Получение истории пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT input_path, output_path, stats, timestamp
                    FROM processing_history
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (user_id, limit))
                
                rows = cursor.fetchall()
                history = []
                
                for row in rows:
                    history.append({
                        "input_path": row[0],
                        "output_path": row[1],
                        "stats": eval(row[2]) if row[2] else {},
                        "timestamp": row[3]
                    })
                
                return history
        except Exception as e:
            self.logger.error(f"Failed to get history: {e}")
            return []

    def get_statistics(self):
        """Получение общей статистики"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM users")
                total_users = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM processing_history")
                total_videos = cursor.fetchone()[0]
                
                return {
                    "total_users": total_users,
                    "total_videos": total_videos
                }
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {"total_users": 0, "total_videos": 0}

    def cleanup_cache(self):
        """Очистка истёкшего кэша"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cache WHERE expires_at < ?", (datetime.now(),))
                conn.commit()
                self.logger.info("Cache cleaned")
        except Exception as e:
            self.logger.error(f"Failed to clean cache: {e}")

    def cleanup_old_history(self, days=30):
        """Удаление старых записей из истории"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM processing_history WHERE timestamp < ?", (cutoff_date,))
                conn.commit()
                self.logger.info(f"Old history cleaned (older than {days} days)")
        except Exception as e:
            self.logger.error(f"Failed to cleanup history: {e}")
