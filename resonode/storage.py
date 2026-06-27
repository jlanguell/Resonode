"""SQLite-backed persistence: sessions, utterances, per-guild settings.

Local-first and dependency-free (stdlib sqlite3). The API is intentionally small
and storage-agnostic so the hosted tier can swap in Postgres + pgvector later
without touching the cogs.
"""
from __future__ import annotations

import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    guild_name TEXT,
    channel_id INTEGER,
    channel_name TEXT,
    model TEXT,
    started_at REAL NOT NULL,
    ended_at REAL
);
CREATE TABLE IF NOT EXISTS utterances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    guild_id INTEGER NOT NULL,
    speaker_id INTEGER,
    speaker_name TEXT,
    start_s REAL,
    end_s REAL,
    text TEXT NOT NULL,
    lang TEXT,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    PRIMARY KEY (guild_id, key)
);
CREATE INDEX IF NOT EXISTS idx_utt_guild ON utterances(guild_id);
CREATE INDEX IF NOT EXISTS idx_utt_session ON utterances(session_id);
"""


@dataclass
class Utterance:
    speaker_name: str
    start_s: float
    end_s: float
    text: str
    speaker_id: Optional[int] = None
    lang: Optional[str] = None


class Storage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self):
        with self._lock:
            self._conn.close()

    # --- sessions ---
    def start_session(self, guild_id, guild_name, channel_id, channel_name, model) -> int:
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO sessions(guild_id,guild_name,channel_id,channel_name,model,started_at)"
                " VALUES (?,?,?,?,?,?)",
                (guild_id, guild_name, channel_id, channel_name, model, time.time()),
            )
            self._conn.commit()
            return cur.lastrowid

    def end_session(self, session_id):
        with self._lock:
            self._conn.execute("UPDATE sessions SET ended_at=? WHERE id=?", (time.time(), session_id))
            self._conn.commit()

    def latest_session(self, guild_id):
        cur = self._conn.execute(
            "SELECT * FROM sessions WHERE guild_id=? ORDER BY id DESC LIMIT 1", (guild_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None

    # --- utterances ---
    def add_utterance(self, session_id, guild_id, u: Utterance):
        with self._lock:
            self._conn.execute(
                "INSERT INTO utterances(session_id,guild_id,speaker_id,speaker_name,start_s,end_s,text,lang,created_at)"
                " VALUES (?,?,?,?,?,?,?,?,?)",
                (session_id, guild_id, u.speaker_id, u.speaker_name, u.start_s, u.end_s, u.text, u.lang, time.time()),
            )
            self._conn.commit()

    def session_utterances(self, session_id):
        cur = self._conn.execute(
            "SELECT * FROM utterances WHERE session_id=? ORDER BY start_s", (session_id,)
        )
        return [dict(r) for r in cur.fetchall()]

    def recent_utterances(self, guild_id, limit=50):
        cur = self._conn.execute(
            "SELECT * FROM utterances WHERE guild_id=? ORDER BY id DESC LIMIT ?", (guild_id, limit)
        )
        return list(reversed([dict(r) for r in cur.fetchall()]))

    def search(self, guild_id, query, limit=20):
        cur = self._conn.execute(
            "SELECT * FROM utterances WHERE guild_id=? AND text LIKE ? ORDER BY id DESC LIMIT ?",
            (guild_id, f"%{query}%", limit),
        )
        return [dict(r) for r in cur.fetchall()]

    # --- settings ---
    def set_setting(self, guild_id, key, value):
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO guild_settings(guild_id,key,value) VALUES (?,?,?)",
                (guild_id, key, str(value)),
            )
            self._conn.commit()

    def get_setting(self, guild_id, key, default=None):
        cur = self._conn.execute(
            "SELECT value FROM guild_settings WHERE guild_id=? AND key=?", (guild_id, key)
        )
        row = cur.fetchone()
        return row["value"] if row else default
