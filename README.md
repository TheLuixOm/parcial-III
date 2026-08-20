# Parcial III: Diseno, Adversidad y Robustecimiento de Protocolos de Comunicacion

Protocolo de comunicacion cliente-servidor TCP con fase de adversidad y robustecimiento.

## Requisitos

- Python 3.8+
- Node.js 14+

No se necesitan dependencias externas. Solo stdlib.

## Uso - Comunicacion Directa (Fase 1)

### Terminal 1 - Servidor

```bash
cd server
python server.py
```

### Terminal 2 - Cliente

```bash
cd client
node client.js
```

El cliente es interactivo. Escribe mensajes y presiona Enter. Comandos:

- `/ping` - Enviar PING
- `/close` - Cerrar conexion
- `/quit` - Cerrar y salir