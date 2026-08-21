# Especificacion del Protocolo de Comunicacion

## Transporte

- **Capa**: Aplicacion sobre TCP
- **Puerto por defecto**: 5000 (servidor), 9002 (proxies de adversidad)
- **Configuracion**: variable de entorno `PORT` (y `HOST`) en cliente y servidor; los proxies aceptan `--port` y `--server-port`
- **Codificacion de datos**: Texto UTF-8

## Estructura de la Trama

```
| Delimitador (2B) | Tipo (1B) | Secuencia (2B) | Longitud (2B) | Payload (N bytes) | CRC32 (4B) |
```

Todos los campos multi-byte usan **Big-Endian**.

### Campos

| Campo        | Tamano  | Descripcion                                            |
|--------------|---------|--------------------------------------------------------|
| Delimitador  | 2 bytes | `0xAA 0x55` - marca de inicio de trama                 |
| Tipo         | 1 byte  | Codigo de tipo de mensaje                              |
| Secuencia    | 2 bytes | Numero de secuencia (0-65535)                          |
| Longitud     | 2 bytes | Cantidad de bytes del payload (maximo 4096)            |
| Payload      | N bytes | Datos del mensaje en UTF-8                             |
| CRC32        | 4 bytes | Suma de comprobacion (polinomio reflejado `0xEDB88320`) |

**Total cabecera**: 7 bytes (sin payload ni CRC)

El CRC32 se calcula sobre `Tipo + Secuencia + Longitud + Payload`.

## Tipos de Mensaje

| Codigo | Nombre | Descripcion                                    |
|--------|--------|------------------------------------------------|
| 0x01   | DATA   | Datos enviados por el cliente                  |
| 0x02   | ACK    | Confirmacion de recepcion                      |
| 0x03   | NACK   | Negative acknowledgment (retransmision)        |
| 0x04   | PING   | Sonda de conexion (keep-alive)                 |
| 0x05   | CLOSE  | Solicitud de cierre de conexion                |
| 0x06   | ERROR  | Error de protocolo ante trama malformada       |

## Trama ERROR (Fase 3)

Ante cualquier trama malformada o violacion de protocolo, el receptor responde con una trama ERROR estandarizada.

**Payload**: `[Codigo (1B)][Detalle (UTF-8, opcional)]`

**Secuencia**: numero de secuencia de la trama ofensora; `0` si no se puede determinar.

### Codigos de error

| Codigo | Nombre         | Descripcion                                              |
|--------|----------------|----------------------------------------------------------|
| 0x01   | BAD_DELIMITER  | Bytes fuera de trama descartados durante resincronizacion |
| 0x02   | BAD_LENGTH     | Longitud declarada mayor al maximo permitido (4096)       |
| 0x03   | BAD_CRC        | La suma de comprobacion no coincide                       |
| 0x04   | UNKNOWN_TYPE   | Tipo de mensaje no reconocido                             |

## Fase 3 - Robustecimiento

Mecanismos implementados sobre la linea base:

### Verificacion de integridad
- CRC32 sobre `Tipo + Secuencia + Longitud + Payload` en cada trama
- Tramas con CRC invalido se descartan y se notifica al emisor

### Control de flujo y errores
- Numeros de secuencia de 16 bits con deteccion de duplicados y tramas fuera de orden
- ACK para confirmar recepcion en orden; NACK ante DATA fuera de orden
- Stop-and-Wait: el cliente mantiene una sola trama pendiente
- Timeout de 3 segundos y maximo 3 retransmisiones (por timeout, NACK o ERROR)
- Duplicados: el servidor re-ACK sin procesar

### Manejo de excepciones
- Respuestas ERROR estandarizadas con codigo y detalle (ver tabla anterior)
- Resincronizacion del stream: ante bytes fuera de trama, ambos extremos descartan bytes hasta el proximo delimitador `0xAA55` y notifican `ERROR(BAD_DELIMITER)`
- Longitud excesiva: se descarta la cabecera, se resincroniza y se responde `ERROR(BAD_LENGTH)`
- Tipo desconocido: se responde `ERROR(UNKNOWN_TYPE)` con el tipo recibido
- Cliente: si recibe un ERROR mientras tiene una trama pendiente, la retransmite (mismo tratamiento que NACK)

## Historico - Fase 1 (linea base vulnerable, superada)

Estado original del protocolo antes del robustecimiento:

- Sin CRC ni checksum
- Sin validacion de secuencia
- Sin timeouts ni retransmision
- Sin deteccion de duplicados
