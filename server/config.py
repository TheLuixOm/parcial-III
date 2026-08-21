import os

HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "5000"))
BUFFER_SIZE = 4096

DELIMITER = b"\xAA\x55"
HEADER_SIZE = 7  # 2(delimiter) + 1(type) + 2(seq) + 2(length)
CRC_SIZE = 4

MAX_PAYLOAD_SIZE = 4096

MSG_DATA = 0x01
MSG_ACK = 0x02
MSG_NACK = 0x03
MSG_PING = 0x04
MSG_CLOSE = 0x05
MSG_ERROR = 0x06

ERR_BAD_DELIMITER = 0x01
ERR_BAD_LENGTH = 0x02
ERR_BAD_CRC = 0x03
ERR_UNKNOWN_TYPE = 0x04

MSG_NAMES = {
    MSG_DATA: "DATA",
    MSG_ACK: "ACK",
    MSG_NACK: "NACK",
    MSG_PING: "PING",
    MSG_CLOSE: "CLOSE",
    MSG_ERROR: "ERROR",
}

ERROR_NAMES = {
    ERR_BAD_DELIMITER: "BAD_DELIMITER",
    ERR_BAD_LENGTH: "BAD_LENGTH",
    ERR_BAD_CRC: "BAD_CRC",
    ERR_UNKNOWN_TYPE: "UNKNOWN_TYPE",
}

TIMEOUT_S = 4  # timeout en segundos
MAX_RETRIES = 3  # maximo reintentos ante timeout/NACK
