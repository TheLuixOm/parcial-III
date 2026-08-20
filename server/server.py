import socket
import struct
import threading
from config import HOST, PORT, BUFFER_SIZE, MSG_DATA, MSG_ACK, MSG_NACK, MSG_PING, MSG_CLOSE
from protocol import pack_frame, type_name, recv_exact


def log(addr, msg):
    print(f"[{addr[0]}:{addr[1]}] {msg}")


def handle_client(conn, addr):
    log(addr, "Conexion establecida")

    try:
        while True:
            header = recv_exact(conn, 7)
            if not header:
                log(addr, "Conexion cerrada por el cliente")
                break

            _, msg_type, seq, length = struct.unpack(">2sBHH", header)

            if length > 0:
                payload = recv_exact(conn, length)
                if not payload:
                    log(addr, "Conexion cerrada durante payload")
                    break
            else:
                payload = b""

            crc_data = recv_exact(conn, 4)
            if not crc_data:
                log(addr, "Conexion cerrada durante CRC")
                break
            crc_received = struct.unpack(">I", crc_data)[0]

            from protocol import calc_crc32
            crc_computed = calc_crc32(msg_type.to_bytes(1, "big") + struct.pack(">HH", seq, length) + payload)

            if crc_received != crc_computed:
                log(addr, f"CRC INVALIDO en {type_name(msg_type)} seq={seq} (recibido=0x{crc_received:08X}, esperado=0x{crc_computed:08X})")
                conn.sendall(pack_frame(MSG_NACK, seq))
                log(addr, f"Enviado NACK seq={seq}")
                continue

            log(addr, f"Recibido {type_name(msg_type)} seq={seq} len={length} CRC=OK")

            if msg_type == MSG_DATA:
                mensaje = payload.decode("utf-8", errors="replace")
                log(addr, f"Mensaje: {mensaje}")
                conn.sendall(pack_frame(MSG_ACK, seq))
                log(addr, f"Enviado ACK seq={seq}")

            elif msg_type == MSG_PING:
                conn.sendall(pack_frame(MSG_ACK, seq))
                log(addr, f"Enviado ACK (respuesta a PING)")

            elif msg_type == MSG_CLOSE:
                log(addr, "Solicitud de cierre recibida")
                conn.sendall(pack_frame(MSG_CLOSE, seq))
                log(addr, "Enviado CLOSE de respuesta")
                break

            else:
                log(addr, f"Tipo de mensaje desconocido: 0x{msg_type:02X}")

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
