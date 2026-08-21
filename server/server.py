import socket
import struct
import threading
from config import (
    HOST,
    PORT,
    BUFFER_SIZE,
    HEADER_SIZE,
    CRC_SIZE,
    DELIMITER,
    MAX_PAYLOAD_SIZE,
    TIMEOUT_S,
    MSG_DATA,
    MSG_ACK,
    MSG_NACK,
    MSG_PING,
    MSG_CLOSE,
    MSG_ERROR,
    ERR_BAD_DELIMITER,
    ERR_BAD_LENGTH,
    ERR_BAD_CRC,
    ERR_UNKNOWN_TYPE,
)
from protocol import pack_frame, type_name, error_name, calc_crc32, find_delimiter


def log(addr, msg):
    print(f"[{addr[0]}:{addr[1]}] {msg}")


def send_error(conn, addr, code, seq=0, detail=""):
    payload = bytes([code])
    if detail:
        payload += detail.encode("utf-8")
    conn.sendall(pack_frame(MSG_ERROR, seq, payload))
    log(addr, f"Enviado ERROR({error_name(code)}) seq={seq}")


def resync(buffer, addr, start=1):
    idx = find_delimiter(buffer, start)
    if idx == -1:
        dropped = buffer[:len(buffer) - 1]
        buffer = buffer[len(buffer) - 1:]
    else:
        dropped = buffer[:idx]
        buffer = buffer[idx:]
    if dropped:
        log(addr, f"RESYNC: {len(dropped)} bytes fuera de trama descartados ({dropped[:8].hex()}...)")
    return buffer, bool(dropped)


def recv_chunk(conn, addr, waiting_msg=None):
    try:
        return conn.recv(BUFFER_SIZE)
    except socket.timeout:
        if waiting_msg:
            log(addr, waiting_msg)
        return None
    except OSError:
        return b""


def handle_client(conn, addr):
    log(addr, "Conexion establecida")
    expected_seq = 1
    buffer = b""

    try:
        while True:
            conn.settimeout(TIMEOUT_S)

            while len(buffer) < HEADER_SIZE:
                chunk = recv_chunk(conn, addr, "Timeout esperando datos del cliente")
                if chunk is None:
                    continue
                if not chunk:
                    log(addr, "Conexion cerrada por el cliente")
                    return
                buffer += chunk

            if buffer[:2] != DELIMITER:
                buffer, dropped = resync(buffer, addr)
                if dropped:
                    send_error(conn, addr, ERR_BAD_DELIMITER)
                continue

            msg_type, seq, length = struct.unpack(">BHH", buffer[2:HEADER_SIZE])

            if length > MAX_PAYLOAD_SIZE:
                log(addr, f"LONGITUD INVALIDA {length} (max={MAX_PAYLOAD_SIZE}) en trama seq={seq}")
                send_error(conn, addr, ERR_BAD_LENGTH, seq)
                buffer, _ = resync(buffer[2:], addr, start=0)
                continue

            total_size = HEADER_SIZE + length + CRC_SIZE
            while len(buffer) < total_size:
                chunk = recv_chunk(
                    conn,
                    addr,
                    f"Timeout esperando trama incompleta seq={seq} ({total_size - len(buffer)} bytes faltantes)",
                )
                if chunk is None:
                    continue
                if not chunk:
                    log(addr, "Conexion cerrada durante recepcion de trama")
                    return
                buffer += chunk

            payload = buffer[HEADER_SIZE:HEADER_SIZE + length]
            crc_received = struct.unpack(">I", buffer[HEADER_SIZE + length:total_size])[0]
            crc_computed = calc_crc32(msg_type.to_bytes(1, "big") + struct.pack(">HH", seq, length) + payload)
            buffer = buffer[total_size:]

            if crc_received != crc_computed:
                log(
                    addr,
                    f"CRC INVALIDO en {type_name(msg_type)} seq={seq} "
                    f"(recibido=0x{crc_received:08X}, esperado=0x{crc_computed:08X})",
                )
                send_error(conn, addr, ERR_BAD_CRC, seq)
                continue

            if msg_type == MSG_DATA:
                if seq == expected_seq:
                    log(addr, f"Recibido DATA seq={seq} len={length} CRC=OK [expected={expected_seq}]")
                    mensaje = payload.decode("utf-8", errors="replace")
                    log(addr, f"Mensaje: {mensaje}")
                    conn.sendall(pack_frame(MSG_ACK, seq))
                    log(addr, f"Enviado ACK seq={seq}")
                    expected_seq = (expected_seq + 1) & 0xFFFF
                elif seq < expected_seq:
                    log(addr, f"DUPLICADO DATA seq={seq} (expected={expected_seq}) - reenviando ACK")
                    conn.sendall(pack_frame(MSG_ACK, seq))
                else:
                    log(addr, f"FUERA DE ORDEN DATA seq={seq} (expected={expected_seq})")
                    conn.sendall(pack_frame(MSG_NACK, seq))
                    log(addr, f"Enviado NACK seq={seq}")

            elif msg_type == MSG_PING:
                log(addr, f"Recibido PING seq={seq} CRC=OK")
                conn.sendall(pack_frame(MSG_ACK, seq))
                log(addr, "Enviado ACK (respuesta a PING)")

            elif msg_type == MSG_CLOSE:
                log(addr, f"Solicitud de cierre recibida seq={seq}")
                conn.sendall(pack_frame(MSG_CLOSE, seq))
                log(addr, "Enviado CLOSE de respuesta")
                return

            else:
                log(addr, f"Tipo de mensaje desconocido: 0x{msg_type:02X}")
                send_error(conn, addr, ERR_UNKNOWN_TYPE, seq, f"tipo=0x{msg_type:02X}")

    except ConnectionResetError:
        log(addr, "Conexion reseteada por el cliente")
    except Exception as e:
        log(addr, f"Error: {e}")
    finally:
        conn.close()
        log(addr, "Conexion cerrada")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"Servidor escuchando en {HOST}:{PORT}")
    print(f"Stop-and-Wait activo (timeout={TIMEOUT_S}s)")
    print("Esperando conexiones...\n")

    try:
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
