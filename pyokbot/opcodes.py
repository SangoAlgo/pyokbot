"""
WebSocket message opcode definitions for OK.ru messaging API.

These opcodes are used in the WebSocket protocol communication with OK.ru servers.
Each opcode represents a specific type of message or action.
"""
from enum import IntEnum


class MessageOpcode(IntEnum):
    """WebSocket message opcodes for OK.ru API communication."""

    # Connection lifecycle
    HELLO = 6
    """Server hello message during connection setup."""

    OKWEB_TOKEN_RESPONSE = 23
    """Response containing OKWEB authentication token."""

    AUTH_RESPONSE = 19
    """Authentication/authorization response from server."""

    ACTIVITY = 1
    """Keep-alive / activity heartbeat."""

    # Message operations
    SEND_MESSAGE = 64
    """Send a text message to a chat."""

    DELETE_MESSAGE = 66
    """Delete one or more messages."""

    EDIT_MESSAGE = 67
    """Edit message text."""

    REQUEST_UPLOAD = 65
    """Request upload URL for media files."""

    PHOTO_UPLOAD_URL = 80
    """Response with photo/avatar upload URL."""

    VIDEO_UPLOAD_URL = 82
    """Response with video upload URL."""

    FILE_UPLOAD_URL = 87
    """Response with file upload URL."""

    FILE_PUBLISHED = 136
    """Notification that file was published after upload."""

    # Chat management
    GET_CHAT_INFO = 48
    """Request chat information (members, title, etc.)."""

    CLEAR_CHAT_HISTORY = 54
    """Clear chat message history."""

    PIN_MESSAGE = 55
    """Pin a message in a chat."""

    BLOCK_MEMBER = 77
    """Block or remove a member from chat."""

    # Incoming messages
    INCOMING_MESSAGE = 128
    """Incoming message from chat (opcode for received messages)."""
