"""
Proxy de Corrupcion de Datos
Altera bits aleatorios en el payload de las tramas antes de reenviarlas.
Uso: python corruption_proxy.py [--corrupt 30] [--port 9002]
"""
import socket
import threading
import random
import struct
import argparse
import sys

DELIMITER = b"\xAA\x55"
HEADER_SIZE = 7

MSG_NAMES = {0x01: "DATA", 0x02: "ACK", 0x03: "NACK", 0x04: "PING", 0x05: "CLOSE"}


def parse_frame(data):
    if len(data) < HEADER_SIZE:
        return None
    if data[0:2] != DELIMITER:
        return None
    msg_type, seq, length = struct.unpack(">BHH", data[2:7])
    total = HEADER_SIZE + length
    if len(data) < total:
        return None
    return data[:total], data[total:], msg_type, seq, data[HEADER_SIZE:total]


def corrupt_payload(payload):
    if len(payload) == 0:
        return payload
    data = bytearray(payload)
    idx = random.randint(0, len(data) - 1)
    bit = 1 << random.randint(0, 7)
    data[idx] ^= bit
    return bytes(data)


def type_name(t):
    return MSG_NAMES.get(t, f"0x{t:02X}")


def forward(src, dst, label, corrupt_pct):
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break

            remaining = data
            while remaining:
                result = parse_frame(remaining)
                if result is None:
                    dst.sendall(remaining)
                    break

                frame, rest, msg_type, seq, payload = result
                remaining = rest

                if msg_type in (0x02, 0x03):
                    dst.sendall(frame)
                else:
                    if random.randint(1, 100) <= corrupt_pct:
                        corrupted_payload = corrupt_payload(payload)
                        header = struct.pack(">2sBHH", DELIMITER, msg_type, seq, len(corrupted_payload))
                        new_frame = header + corrupted_payload
                        dst.sendall(new_frame)
                        print(f"  [CORRUPT] {label} {type_name(msg_type)} seq={seq} "
                              f"original={payload.hex()} corrupto={corrupted_payload.hex()}")
                    else:
                        dst.sendall(frame)

    except (ConnectionResetError, BrokenPipeError, OSError):
        pass
    finally:
        print(f"  [{label}] Conexion cerrada")


def main():
    parser = argparse.ArgumentParser(description="Proxy de corrupcion de datos")
    parser.add_argument("--corrupt", type=int, default=50, help="Porcentaje de corrupcion (0-100)")
    parser.add_argument("--port", type=int, default=9002, help="Puerto local del proxy")
    parser.add_argument("--server-port", type=int, default=5000, help="Puerto del servidor real")
    args = parser.parse_args()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", args.port))
    server.listen(1)

    print(f"[CORRUPTION PROXY] Puerto local: {args.port}")
    print(f"[CORRUPTION PROXY] Corrupcion configurada: {args.corrupt}%")
    print(f"[CORRUPTION PROXY] Servidor destino: 127.0.0.1:{args.server_port}")
    print(f"[CORRUPTION PROXY] Esperando conexion del cliente...\n")

    try:
        while True:
            client_sock, client_addr = server.accept()
            print(f"[+] Cliente conectado desde {client_addr}")

            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                server_sock.connect(("127.0.0.1", args.server_port))
                print(f"[+] Conectado al servidor en {args.server_port}")
            except ConnectionRefusedError:
                print(f"[-] No se pudo conectar al servidor en {args.server_port}")
                client_sock.close()
                continue

            t1 = threading.Thread(target=forward, args=(client_sock, server_sock, "C->S", args.corrupt), daemon=True)
            t2 = threading.Thread(target=forward, args=(server_sock, client_sock, "S->C", 0), daemon=True)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            client_sock.close()
            server_sock.close()
            print(f"[-] Sesion finalizada\n")

    except KeyboardInterrupt:
        print("\n[STOP] Proxy detenido.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
