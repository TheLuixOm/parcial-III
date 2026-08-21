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

## Fase 3 - Robustecimiento del Protocolo

Mecanismos de tolerancia a fallos implementados (detalle completo en `protocolo/spec.md`):

- **Verificacion de integridad**: CRC32 sobre cada trama; las tramas corruptas se descartan y se notifican
- **Control de flujo y errores**: ACK/NACK, numeros de secuencia, deteccion de duplicados, Stop-and-Wait con timeout de 3s y maximo 3 retransmisiones
- **Manejo de excepciones**: tramas ERROR estandarizadas (`BAD_DELIMITER`, `BAD_LENGTH`, `BAD_CRC`, `UNKNOWN_TYPE`) ante tramas malformadas, con resincronizacion del stream

### Variables de entorno

Los puertos por defecto no cambian: el cliente usa 9002 (proxy de adversidad) y el servidor 5000. Para conexion directa sin proxy:

```bash
# Terminal 1
cd server && python server.py            # escucha en 5000

# Terminal 2
cd client && PORT=5000 node client.js    # conecta directo al servidor
```

En Windows (PowerShell): `$env:PORT=5000; node client.js`

Tambien esta disponible `HOST` en ambos extremos. Los proxies de `attack/` aceptan `--port` y `--server-port`.