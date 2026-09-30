import sqlite3
import os
import logging

class ViskoDB:
    def __init__(self, db_path="visko_fx.db"):
        self.db_path = db_path
        self._init_db()
        
    def _get_conn(self):
        return sqlite3.connect(self.db_path)
        
    def _init_db(self):
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tracks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        current_filename TEXT UNIQUE NOT NULL
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS track_aliases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        track_id INTEGER NOT NULL,
                        filename TEXT UNIQUE NOT NULL,
                        FOREIGN KEY(track_id) REFERENCES tracks(id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        track_id INTEGER NOT NULL,
                        time_ms INTEGER NOT NULL,
                        preset TEXT NOT NULL,
                        enabled INTEGER NOT NULL DEFAULT 1,
                        FOREIGN KEY(track_id) REFERENCES tracks(id)
                    )
                ''')
                conn.commit()
        except Exception as e:
            logging.error(f"VISKO DB Init Error: {e}")

    def get_or_create_track(self, filename: str) -> int:
        """Finds track by filename or alias, or creates a new one."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                # Check current_filename
                cursor.execute('SELECT id FROM tracks WHERE current_filename = ?', (filename,))
                row = cursor.fetchone()
                if row: return row[0]
                
                # Check aliases
                cursor.execute('SELECT track_id FROM track_aliases WHERE filename = ?', (filename,))
                row = cursor.fetchone()
                if row:
                    track_id = row[0]
                    # Update current_filename to the new alias? 
                    # The spec says: when renaming, update current_filename, add old to aliases.
                    # For now just return the track_id, renaming is a separate explicit action.
                    return track_id
                
                # Create new
                cursor.execute('INSERT INTO tracks (current_filename) VALUES (?)', (filename,))
                track_id = cursor.lastrowid
                conn.commit()
                return track_id
        except Exception as e:
            logging.error(f"VISKO DB Error (get_or_create_track): {e}")
            return -1

    def rename_track(self, track_id: int, new_filename: str):
        """Changes current_filename and saves the old one as an alias."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT current_filename FROM tracks WHERE id = ?', (track_id,))
                row = cursor.fetchone()
                if not row: return
                old_filename = row[0]
                
                if old_filename == new_filename: return
                
                cursor.execute('INSERT OR IGNORE INTO track_aliases (track_id, filename) VALUES (?, ?)', (track_id, old_filename))
                cursor.execute('UPDATE tracks SET current_filename = ? WHERE id = ?', (new_filename, track_id))
                conn.commit()
        except Exception as e:
            logging.error(f"VISKO DB Error (rename_track): {e}")

    def get_events(self, track_id: int):
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, time_ms, preset, enabled FROM events WHERE track_id = ? ORDER BY time_ms ASC', (track_id,))
                return [{"id": r[0], "time_ms": r[1], "preset": r[2], "enabled": bool(r[3])} for r in cursor.fetchall()]
        except Exception as e:
            logging.error(f"VISKO DB Error (get_events): {e}")
            return []

    def add_event(self, track_id: int, time_ms: int, preset: str, enabled: bool = True) -> int:
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO events (track_id, time_ms, preset, enabled) VALUES (?, ?, ?, ?)', 
                               (track_id, time_ms, preset, int(enabled)))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logging.error(f"VISKO DB Error (add_event): {e}")
            return -1

    def update_event(self, event_id: int, time_ms: int, preset: str, enabled: bool):
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE events SET time_ms = ?, preset = ?, enabled = ? WHERE id = ?',
                               (time_ms, preset, int(enabled), event_id))
                conn.commit()
        except Exception as e:
            logging.error(f"VISKO DB Error (update_event): {e}")

    def delete_event(self, event_id: int):
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
                conn.commit()
        except Exception as e:
            logging.error(f"VISKO DB Error (delete_event): {e}")

