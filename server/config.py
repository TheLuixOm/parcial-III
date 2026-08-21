HOST = "127.0.0.1"
PORT = 5000
BUFFER_SIZE = 4096

DELIMITER = b"\xAA\x55"
HEADER_SIZE = 7  # 2(delimiter) + 1(type) + 2(seq) + 2(length)
CRC_SIZE = 4

MSG_DATA = 0x01
MSG_ACK = 0x02
MSG_NACK = 0x03
MSG_PING = 0x04
MSG_CLOSE = 0x05

MSG_NAMES = {
    MSG_DATA: "DATA",
    MSG_ACK: "ACK",
    MSG_NACK: "NACK",
    MSG_PING: "PING",
    MSG_CLOSE: "CLOSE",
}

TIMEOUT_S = 3  # timeout Stop-and-Wait en segundos
MAX_RETRIES = 3  # maximo reintentos ante timeout/NACK
