import sqlite3
import json
from datetime import datetime
import os

class OfflineManager:
    """
    Manages local SQLite caching of passenger count logs
    when the remote API endpoint is unreachable.
    """
    def __init__(self, db_path="offline_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = None
        try:
            conn = self._get_connection()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    attempts INTEGER DEFAULT 0
                )
            """)
            conn.commit()
        except Exception as e:
            print(f"Error initializing offline database: {e}")
        finally:
            if conn:
                conn.close()

    def save_pending_payload(self, payload):
        """Saves a JSON payload array to the offline queue."""
        if not payload:
            return
        conn = None
        try:
            conn = self._get_connection()
            conn.execute(
                "INSERT INTO pending_logs (payload, created_at, attempts) VALUES (?, ?, 0)",
                (json.dumps(payload), datetime.now().isoformat())
            )
            conn.commit()
        except Exception as e:
            print(f"Error saving to offline database: {e}")
        finally:
            if conn:
                conn.close()

    def get_pending_payloads(self):
        """Retrieves all pending payloads."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, payload FROM pending_logs ORDER BY id ASC")
            rows = cursor.fetchall()
            results = []
            for row_id, payload_str in rows:
                results.append((row_id, json.loads(payload_str)))
            return results
        except Exception as e:
            print(f"Error reading offline database: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def remove_payload(self, record_id):
        """Deletes a successfully sent payload from the queue."""
        conn = None
        try:
            conn = self._get_connection()
            conn.execute("DELETE FROM pending_logs WHERE id = ?", (record_id,))
            conn.commit()
        except Exception as e:
            print(f"Error removing record {record_id} from offline database: {e}")
        finally:
            if conn:
                conn.close()

    def get_pending_count(self):
        """Returns the number of queued batches."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM pending_logs")
            count = cursor.fetchone()[0]
            return count
        except Exception:
            return 0
        finally:
            if conn:
                conn.close()
