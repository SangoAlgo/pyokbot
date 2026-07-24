from enum import IntEnum


class MessageOpcode(IntEnum):
    ACTIVITY         = 1
    HELLO            = 6
    AUTH             = 19
    TOKEN            = 23
    CHAT_INFO        = 48
    CLEAR_HISTORY    = 54
    CHAT_SETTINGS    = 55
    SEND_MESSAGE     = 64
    REQUEST_UPLOAD   = 65
    DELETE_MESSAGE   = 66
    EDIT_MESSAGE     = 67
    BLOCK_MEMBER     = 77
    PHOTO_UPLOAD     = 80
    MEDIA_UPLOAD     = 82
    FILE_UPLOAD      = 87
    FILE_PUBLISHED   = 136
    INCOMING_MESSAGE = 128
