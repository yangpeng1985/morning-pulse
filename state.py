"""
状态持久化 - SQLite
存储已处理的 item_id，防止重复推送
"""
import sqlite3
import logging
from datetime import datetime, date

class StateStore:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_items (
                item_id TEXT PRIMARY KEY,
                fetch_date TEXT NOT NULL,
                publish_time TEXT
            )
        """)
        self.conn.commit()

    def has_seen(self, item_id: str) -> bool:
        cur = self.conn.execute("SELECT 1 FROM seen_items WHERE item_id = ?", (item_id,))
        return cur.fetchone() is not None

    def mark_seen(self, item_id: str, publish_time: datetime):
        today = date.today().isoformat()
        pub_str = publish_time.isoformat() if publish_time else ''
        self.conn.execute(
            "INSERT OR IGNORE INTO seen_items (item_id, fetch_date, publish_time) VALUES (?, ?, ?)",
            (item_id, today, pub_str)
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
