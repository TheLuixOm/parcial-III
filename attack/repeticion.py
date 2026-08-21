
## Proxy de Replay / Inyeccion de Tramas
## Duplica tramas DATA aleatoriamente (ataque de replay) o inyecta tramas basura.
## para usar: python replay_proxy.py [--replay 30] [--inject 10] [--port 9002]

import socket
import threading
import random
import struct
import argparse
import sys
import time

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


def type_name(t):
    return MSG_NAMES.get(t, f"0x{t:02X}")


def make_junk_frame():
    msg_type = random.choice([0x01, 0x04])
    seq = random.randint(0, 65535)
    junk = bytes(random.getrandbits(8) for _ in range(random.randint(5, 30)))
    header = struct.pack(">2sBHH", DELIMITER, msg_type, seq, len(junk))
    return header + junk


def forward(src, dst, label, replay_pct, inject_pct):
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
                    dst.sendall(frame)

                    if msg_type == 0x01 and random.randint(1, 100) <= replay_pct:
                        time.sleep(random.uniform(0.01, 0.1))
                        dst.sendall(frame)
                        print(f"  [REPLAY] {label} DATA seq={seq} DUPLICADO")

                    if random.randint(1, 100) <= inject_pct:
                        junk = make_junk_frame()
                        dst.sendall(junk)
                        junk_type, junk_seq, _, _ = parse_frame(junk)
                        print(f"  [INJECT] {label} Basura {type_name(junk_type)} seq={junk_seq}")

    except (ConnectionResetError, BrokenPipeError, OSError):
        pass
    finally:
        print(f"  [{label}] Conexion cerrada")


def main():
    parser = argparse.ArgumentParser(description="Proxy de replay e inyeccion")
    parser.add_argument("--replay", type=int, default=30, help="Porcentaje de replay (0-100)")
    parser.add_argument("--inject", type=int, default=10, help="Porcentaje de inyeccion de basura (0-100)")
    parser.add_argument("--port", type=int, default=9002, help="Puerto local del proxy")
    parser.add_argument("--server-port", type=int, default=5000, help="Puerto del servidor real")
    args = parser.parse_args()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", args.port))
    server.listen(1)

    print(f"[REPLAY PROXY] Puerto local: {args.port}")
    print(f"[REPLAY PROXY] Replay: {args.replay}%")
    print(f"[REPLAY PROXY] Inyeccion: {args.inject}%")
    print(f"[REPLAY PROXY] Servidor destino: 127.0.0.1:{args.server_port}")
    print(f"[REPLAY PROXY] Esperando conexion del cliente...\n")

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

            t1 = threading.Thread(
                target=forward,
                args=(client_sock, server_sock, "C->S", args.replay, args.inject),
                daemon=True,
            )
            t2 = threading.Thread(
                target=forward,
                args=(server_sock, client_sock, "S->C", 0, 0),
                daemon=True,
            )
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
