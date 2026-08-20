import struct
import binascii
from config import DELIMITER, HEADER_SIZE, CRC_SIZE, MSG_NAMES


def calc_crc32(data):
    return binascii.crc32(data) & 0xFFFFFFFF


def pack_frame(msg_type, seq, payload=b""):
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    length = len(payload)
    header = struct.pack(">2sBHH", DELIMITER, msg_type, seq, length)
    crc = calc_crc32(msg_type.to_bytes(1, "big") + struct.pack(">HH", seq, length) + payload)
    return header + payload + struct.pack(">I", crc)


def unpack_frame(data):
    if len(data) < HEADER_SIZE + CRC_SIZE:
        return None

    delimiter = data[0:2]
    if delimiter != DELIMITER:
        return None

    msg_type, seq, length = struct.unpack(">BHH", data[2:7])
    total_size = HEADER_SIZE + length + CRC_SIZE

    if len(data) < total_size:
        return None

    payload = data[7:7 + length]
    crc_received = struct.unpack(">I", data[7 + length:7 + length + 4])[0]
    crc_data = msg_type.to_bytes(1, "big") + struct.pack(">HH", seq, length) + payload
    crc_computed = calc_crc32(crc_data)

    remaining = data[total_size:]

    return msg_type, seq, payload, crc_received == crc_computed, remaining


def type_name(msg_type):
    return MSG_NAMES.get(msg_type, f"UNKNOWN(0x{msg_type:02X})")


def recv_exact(sock, n):
    buffer = b""
    while len(buffer) < n:
        chunk = sock.recv(n - len(buffer))
        if not chunk:
            return None
        buffer += chunk
    return buffer
