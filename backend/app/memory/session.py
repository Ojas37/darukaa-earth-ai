import sqlite3
import json
import uuid
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.schemas.profile import EnvironmentalProfile

class ConversationSession:
    def __init__(self, conversation_id: str, profile: Optional[EnvironmentalProfile] = None):
        self.conversation_id = conversation_id
        self.profile = profile or EnvironmentalProfile()
        self.messages: List[Dict[str, str]] = []
        self.latest_report_json: Optional[str] = None
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()

    def add_message(self, role: str, content: str):
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.updated_at = datetime.utcnow().isoformat()

class SessionManager:
    """
    Manages multi-turn conversation sessions with persistent SQLite backing and fast in-memory cache.
    """

    def __init__(self, db_path: str = "daruka.db"):
        self.db_path = db_path
        self._cache: Dict[str, ConversationSession] = {}
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                conversation_id TEXT PRIMARY KEY,
                profile_json TEXT NOT NULL,
                messages_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def get_or_create_session(self, conversation_id: Optional[str] = None) -> ConversationSession:
        if not conversation_id:
            conversation_id = f"conv_{uuid.uuid4().hex[:10]}"

        # Check in-memory cache
        if conversation_id in self._cache:
            return self._cache[conversation_id]

        # Check SQLite database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT profile_json, messages_json, created_at, updated_at FROM sessions WHERE conversation_id = ?", (conversation_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            profile_dict = json.loads(row[0])
            profile = EnvironmentalProfile.model_validate(profile_dict)
            session = ConversationSession(conversation_id=conversation_id, profile=profile)
            session.messages = json.loads(row[1])
            session.created_at = row[2]
            session.updated_at = row[3]
        else:
            session = ConversationSession(conversation_id=conversation_id)

        self._cache[conversation_id] = session
        return session

    def save_session(self, session: ConversationSession):
        session.updated_at = datetime.utcnow().isoformat()
        self._cache[session.conversation_id] = session

        profile_json = session.profile.model_dump_json()
        messages_json = json.dumps(session.messages)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (conversation_id, profile_json, messages_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(conversation_id) DO UPDATE SET
                profile_json = excluded.profile_json,
                messages_json = excluded.messages_json,
                updated_at = excluded.updated_at
        """, (session.conversation_id, profile_json, messages_json, session.created_at, session.updated_at))
        conn.commit()
        conn.close()

    def delete_session(self, conversation_id: str) -> bool:
        if conversation_id in self._cache:
            del self._cache[conversation_id]

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE conversation_id = ?", (conversation_id,))
        rows_deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_deleted > 0

session_manager = SessionManager()
