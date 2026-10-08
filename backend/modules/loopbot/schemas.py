"""
SpaceLoop LoopBot Core Schemas & Types
=====================================
Defines canonical intent types, structured response formats, slot state,
and action confirmation models for the SpaceLoop native AI assistant.
"""
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional


class LoopBotIntent(str, Enum):
    """The 18 canonical intent types supported by LoopBot."""
    GENERAL = "GENERAL"
    SPACE_SEARCH = "SPACE_SEARCH"
    SPACE_DETAILS = "SPACE_DETAILS"
    SPACE_AVAILABILITY = "SPACE_AVAILABILITY"
    BOOKING_STATUS = "BOOKING_STATUS"
    BOOKING_CREATE = "BOOKING_CREATE"
    BOOKING_CANCEL = "BOOKING_CANCEL"
    ACCESS_STATUS = "ACCESS_STATUS"
    ACCESS_HELP = "ACCESS_HELP"
    ESCROW_STATUS = "ESCROW_STATUS"
    REFUND_HELP = "REFUND_HELP"
    HOST_HELP = "HOST_HELP"
    SEEKER_HELP = "SEEKER_HELP"
    LEGAL_INFORMATION = "LEGAL_INFORMATION"
    DISPUTE_HELP = "DISPUTE_HELP"
    TRUST_SAFETY = "TRUST_SAFETY"
    ACCOUNT_HELP = "ACCOUNT_HELP"
    SUPPORT = "SUPPORT"


class LoopBotResponseType(str, Enum):
    """Structured response type rendered by the client."""
    TEXT = "text"
    SPACE_RESULTS = "space_results"
    SPACE_DETAILS = "space_details"
    BOOKING_PREVIEW = "booking_preview"
    BOOKING_STATUS = "booking_status"
    CONFIRMATION_REQUIRED = "confirmation_required"
    ACCESS_STATUS = "access_status"
    ESCROW_STATUS = "escrow_status"
    SUPPORT = "support"
    ERROR = "error"


@dataclass
class ConversationSlots:
    """Accumulated conversational entity slots across multi-turn exchanges."""
    intent: Optional[str] = None
    location: Optional[str] = None
    date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_hours: Optional[float] = None
    budget: Optional[float] = None
    capacity: Optional[int] = None
    amenities: list[str] = field(default_factory=list)
    noise_preference: Optional[str] = None
    selected_space_id: Optional[int] = None
    selected_booking_id: Optional[int] = None
    pending_action: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationSlots":
        if not data:
            return cls()
        return cls(
            intent=data.get("intent"),
            location=data.get("location"),
            date=data.get("date"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            duration_hours=float(data["duration_hours"]) if data.get("duration_hours") is not None else None,
            budget=float(data["budget"]) if data.get("budget") is not None else None,
            capacity=int(data["capacity"]) if data.get("capacity") is not None else None,
            amenities=list(data.get("amenities") or []),
            noise_preference=data.get("noise_preference"),
            selected_space_id=int(data["selected_space_id"]) if data.get("selected_space_id") is not None else None,
            selected_booking_id=int(data["selected_booking_id"]) if data.get("selected_booking_id") is not None else None,
            pending_action=data.get("pending_action")
        )


@dataclass
class LoopBotResponse:
    """Structured response payload returned by the LoopBot endpoint."""
    message: str
    response_type: LoopBotResponseType = LoopBotResponseType.TEXT
    data: dict[str, Any] = field(default_factory=dict)
    conversation_id: str = ""
    slots: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "conversation_id": self.conversation_id,
            "message": self.message,
            "response_type": self.response_type.value if isinstance(self.response_type, LoopBotResponseType) else str(self.response_type),
            "data": self.data,
            "context": self.slots,
            "error": self.error
        }
