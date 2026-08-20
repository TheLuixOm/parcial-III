import struct
from config import DELIMITER, HEADER_SIZE, MSG_NAMES


def pack_frame(msg_type, seq, payload=b""):
    """Empaqueta una trama con formato: DELIMITER(2) + TYPE(1) + SEQ(2) + LENGTH(2) + PAYLOAD"""
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    length = len(payload)
    header = struct.pack(">2sBHH", DELIMITER, msg_type, seq, length)
    return header + payload


def unpack_frame(data):
    """Desempaqueta una trama. Retorna (msg_type, seq, payload,剩余_bytes) o None si falta datos."""
    if len(data) < HEADER_SIZE:
        return None

    delimiter = data[0:2]
    if delimiter != DELIMITER:
        return None

    msg_type, seq, length = struct.unpack(">BHH", data[2:7])
    total_size = HEADER_SIZE + length

    if len(data) < total_size:
        return None

    payload = data[HEADER_SIZE:total_size]
    remaining = data[total_size:]

    return msg_type, seq, payload, remaining


def type_name(msg_type):
    """Retorna el nombre legible de un tipo de mensaje."""
    return MSG_NAMES.get(msg_type, f"UNKNOWN(0x{msg_type:02X})")


def recv_exact(sock, n):
    """Recibe exactamente n bytes del socket."""
    buffer = b""
    while len(buffer) < n:
        chunk = sock.recv(n - len(buffer))
        if not chunk:
            return None
        buffer += chunk
    return buffer
