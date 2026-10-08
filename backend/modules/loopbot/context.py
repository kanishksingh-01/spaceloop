"""
SpaceLoop LoopBot Context & Session Manager
==========================================
Manages multi-turn conversation memory, slot filling state,
pending action lifecycles, and affirmative/negative confirmation detection.
"""
import re
import time
import uuid
import threading
from typing import Any, Optional
from backend.modules.loopbot.schemas import ConversationSlots


class ConversationContextManager:
    """
    Thread-safe in-memory session manager with TTL expiration.
    Maintains slot tracking, message histories, and pending action confirmation states.
    """
    _lock = threading.Lock()
    _sessions: dict[str, dict[str, Any]] = {}
    SESSION_TTL_SECONDS = 86400  # 24 hours

    @classmethod
    def get_or_create(
        cls,
        conversation_id: Optional[str] = None,
        user_id: Optional[int] = None,
        initial_slots: Optional[dict[str, Any]] = None
    ) -> tuple[str, dict[str, Any]]:
        """
        Retrieves an active session or instantiates a fresh one.
        Returns (conversation_id, session_data).
        """
        with cls._lock:
            cls._prune_expired_sessions()

            cid = conversation_id.strip() if conversation_id and conversation_id.strip() else str(uuid.uuid4())

            if cid not in cls._sessions:
                slots = ConversationSlots()
                if initial_slots:
                    for k, v in initial_slots.items():
                        if hasattr(slots, k) and v is not None:
                            setattr(slots, k, v)

                cls._sessions[cid] = {
                    "conversation_id": cid,
                    "user_id": user_id,
                    "created_at": time.time(),
                    "updated_at": time.time(),
                    "slots": slots,
                    "history": [],
                    "pending_action": None
                }
            else:
                sess = cls._sessions[cid]
                sess["updated_at"] = time.time()
                if user_id and not sess.get("user_id"):
                    sess["user_id"] = user_id
                if initial_slots:
                    slots = sess["slots"]
                    for k, v in initial_slots.items():
                        if hasattr(slots, k) and v is not None:
                            setattr(slots, k, v)

            return cid, cls._sessions[cid]

    @classmethod
    def get_session(cls, conversation_id: str) -> Optional[dict[str, Any]]:
        with cls._lock:
            return cls._sessions.get(conversation_id)

    @classmethod
    def update_slots(cls, conversation_id: str, new_slot_values: dict[str, Any]) -> ConversationSlots:
        """
        Merges new extracted slot values into the existing conversation state.
        Preserves previously extracted fields unless overwritten by valid new data.
        """
        with cls._lock:
            sess = cls._sessions.get(conversation_id)
            if not sess:
                _, sess = cls.get_or_create(conversation_id)

            slots: ConversationSlots = sess["slots"]
            for field_name, value in new_slot_values.items():
                if hasattr(slots, field_name) and value is not None:
                    if field_name == "amenities" and isinstance(value, list):
                        existing = set(slots.amenities)
                        existing.update(value)
                        slots.amenities = list(existing)
                    else:
                        setattr(slots, field_name, value)

            sess["updated_at"] = time.time()
            return slots

    @classmethod
    def add_turn(cls, conversation_id: str, role: str, content: str) -> None:
        with cls._lock:
            sess = cls._sessions.get(conversation_id)
            if sess:
                sess["history"].append({
                    "role": role,
                    "content": content,
                    "timestamp": time.time()
                })
                # Cap conversation history window at 30 turns for memory efficiency
                if len(sess["history"]) > 30:
                    sess["history"] = sess["history"][-30:]
                sess["updated_at"] = time.time()

    @classmethod
    def set_pending_action(cls, conversation_id: str, action_name: str, payload: dict[str, Any]) -> None:
        """Stores a pending action waiting for explicit user confirmation."""
        with cls._lock:
            sess = cls._sessions.get(conversation_id)
            if sess:
                action_data = {
                    "action": action_name,
                    "payload": payload,
                    "created_at": time.time()
                }
                sess["pending_action"] = action_data
                sess["slots"].pending_action = action_data
                sess["updated_at"] = time.time()

    @classmethod
    def get_pending_action(cls, conversation_id: str) -> Optional[dict[str, Any]]:
        with cls._lock:
            sess = cls._sessions.get(conversation_id)
            if sess:
                return sess.get("pending_action")
            return None

    @classmethod
    def clear_pending_action(cls, conversation_id: str) -> Optional[dict[str, Any]]:
        with cls._lock:
            sess = cls._sessions.get(conversation_id)
            if sess:
                prev = sess.get("pending_action")
                sess["pending_action"] = None
                sess["slots"].pending_action = None
                sess["updated_at"] = time.time()
                return prev
            return None

    @classmethod
    def is_confirmation(cls, message: str) -> bool:
        """
        Detects affirmative intent for two-step confirmation gates across English, Hindi, and Marathi.
        """
        clean = (message or "").lower().strip()
        clean_punct = re.sub(r"[^\w\s]", "", clean).strip()

        affirmative_words = {
            "yes", "y", "confirm", "proceed", "sure", "ok", "okay", "yep", "yeah",
            "book it", "book now", "cancel it", "cancel now", "do it", "agree",
            "go ahead", "haan", "ha", "sahi hai", "theek hai", "pucka", "ho", "hoy",
            "chalein", "confirm booking", "confirm cancel"
        }
        if clean_punct in affirmative_words:
            return True

        affirmative_patterns = [
            r"^(yes|yep|sure|proceed|confirm|ok|okay)\b",
            r"\b(please confirm|confirm this|confirm booking|confirm cancellation)\b",
            r"\b(go ahead and book|go ahead with booking|book this space)\b",
            r"\b(haan ji|haan kar do|ha kara|karo confirm)\b"
        ]
        return any(bool(re.search(pat, clean)) for pat in affirmative_patterns)

    @classmethod
    def is_denial(cls, message: str) -> bool:
        """
        Detects negative intent / cancellation of pending actions.
        """
        clean = (message or "").lower().strip()
        clean_punct = re.sub(r"[^\w\s]", "", clean).strip()

        denial_words = {
            "no", "n", "cancel", "abort", "stop", "dont", "don't", "nevermind",
            "nah", "nope", "nahi", "na", "nako", "mat karo", "rahne do", "thamba"
        }
        if clean_punct in denial_words:
            return True

        denial_patterns = [
            r"^(no|stop|abort|don't|dont|nevermind)\b",
            r"\b(do not proceed|don't book|don't cancel|cancel this action)\b",
            r"\b(nahi chahiye|mat karo|nako karu)\b"
        ]
        return any(bool(re.search(pat, clean)) for pat in denial_patterns)

    @classmethod
    def _prune_expired_sessions(cls) -> None:
        now = time.time()
        expired = [
            cid for cid, sess in cls._sessions.items()
            if now - sess.get("updated_at", 0) > cls.SESSION_TTL_SECONDS
        ]
        for cid in expired:
            del cls._sessions[cid]
