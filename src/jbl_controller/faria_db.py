import sqlite3
import os
import logging

class FariaDB:
    def __init__(self, db_path="faria_fx.db"):
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
                
                # Migração: adicionar coluna beat_pos
                cursor.execute("PRAGMA table_info(events)")
                columns = [c[1] for c in cursor.fetchall()]
                if "beat_pos" not in columns:
                    cursor.execute("ALTER TABLE events ADD COLUMN beat_pos REAL DEFAULT 0.0")
                    
                conn.commit()
        except Exception as e:
            logging.error(f"FARIA DB Init Error: {e}")

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
            logging.error(f"FARIA DB Error (get_or_create_track): {e}")
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
            logging.error(f"FARIA DB Error (rename_track): {e}")

    def get_events(self, track_id: int):
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, time_ms, beat_pos, preset, enabled FROM events WHERE track_id = ? ORDER BY time_ms ASC', (track_id,))
                events = []
                for row in cursor.fetchall():
                    events.append({
                        "id": row[0],
                        "time_ms": row[1],
                        "beat_pos": row[2] if row[2] is not None else 0.0,
                        "preset": row[3],
                        "enabled": bool(row[4])
                    })
                return events
        except Exception as e:
            logging.error(f"FARIA DB Error (get_events): {e}")
            return []

    def add_event(self, track_id: int, time_ms: int, beat_pos: float = 0.0, preset: str = "", enabled: bool = True) -> int:
        if isinstance(beat_pos, str):
            preset = beat_pos
            beat_pos = 0.0
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO events (track_id, time_ms, beat_pos, preset, enabled) VALUES (?, ?, ?, ?, ?)', 
                               (track_id, time_ms, beat_pos, preset, int(enabled)))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logging.error(f"FARIA DB Error (add_event): {e}")
            return -1

    def update_event(self, event_id: int, time_ms: int, beat_pos: float = 0.0, preset: str = "", enabled: bool = None):
        if isinstance(beat_pos, str):
            if isinstance(preset, bool):
                enabled = preset
            preset = beat_pos
            beat_pos = 0.0
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                if enabled is not None:
                    cursor.execute('UPDATE events SET time_ms = ?, beat_pos = ?, preset = ?, enabled = ? WHERE id = ?',
                                   (time_ms, beat_pos, preset, int(enabled), event_id))
                else:
                    cursor.execute('UPDATE events SET time_ms = ?, beat_pos = ?, preset = ? WHERE id = ?',
                                   (time_ms, beat_pos, preset, event_id))
                conn.commit()
        except Exception as e:
            logging.error(f"FARIA DB Error (update_event): {e}")

    def delete_event(self, event_id: int):
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
                conn.commit()
        except Exception as e:
            logging.error(f"FARIA DB Error (delete_event): {e}")

