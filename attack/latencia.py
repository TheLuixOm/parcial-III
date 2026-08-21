
## Proxy de Latencia y Reordenamiento
## de delay artificial y reordena tramas aleatoriamente.
## para usar: python latency_proxy.py [--delay 200] [--reorder 30] [--port 9002]

import socket
import threading
import random
import struct
import time
import argparse
import sys
from collections import deque

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
    return data[:total], data[total:], msg_type, seq


def type_name(t):
    return MSG_NAMES.get(t, f"0x{t:02X}")


def extract_frames(data):
    frames = []
    remaining = data
    while remaining:
        result = parse_frame(remaining)
        if result is None:
            break
        frame, rest, msg_type, seq = result
        frames.append((frame, msg_type, seq))
        remaining = rest
    return frames, remaining


def forward_with_latency(src, dst, label, delay_ms, reorder_pct):
    pending = deque()
    last_send = 0

    try:
        while True:
            data = src.recv(4096)
            if not data:
                break

            frames, leftover = extract_frames(data)

            for frame, msg_type, seq in frames:
                delay = delay_ms / 1000.0
                if random.randint(1, 100) <= reorder_pct and msg_type not in (0x02, 0x03):
                    delay += random.uniform(0.1, 0.5)
                    print(f"  [REORDER] {label} {type_name(msg_type)} seq={seq} (+{delay:.2f}s extra)")

                pending.append((frame, time.time() + delay))

            now = time.time()
            while pending and pending[0][1] <= now:
                frame, _ = pending.popleft()
                dst.sendall(frame)

            if pending:
                wait = min(t - time.time() for _, t in pending)
                if wait > 0:
                    time.sleep(min(wait, 0.05))

    except (ConnectionResetError, BrokenPipeError, OSError):
        pass
    finally:
        now = time.time()
        while pending:
            frame, t = pending.popleft()
            try:
                dst.sendall(frame)
            except OSError:
                break
        print(f"  [{label}] Conexion cerrada")


def main():
    parser = argparse.ArgumentParser(description="Proxy de latencia y reordenamiento")
    parser.add_argument("--delay", type=int, default=1000, help="Delay base en milisegundos")
    parser.add_argument("--reorder", type=int, default=80, help="Porcentaje de reordenamiento (0-100)")
    parser.add_argument("--port", type=int, default=9002, help="Puerto local del proxy")
    parser.add_argument("--server-port", type=int, default=5000, help="Puerto del servidor real")
    args = parser.parse_args()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", args.port))
    server.listen(1)

    print(f"[LATENCY PROXY] Puerto local: {args.port}")
    print(f"[LATENCY PROXY] Delay base: {args.delay}ms")
    print(f"[LATENCY PROXY] Reordenamiento: {args.reorder}%")
    print(f"[LATENCY PROXY] Servidor destino: 127.0.0.1:{args.server_port}")
    print(f"[LATENCY PROXY] Esperando conexion del cliente...\n")

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
                target=forward_with_latency,
                args=(client_sock, server_sock, "C->S", args.delay, args.reorder),
                daemon=True,
            )
            t2 = threading.Thread(
                target=forward_with_latency,
                args=(server_sock, client_sock, "S->C", args.delay, 0),
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
