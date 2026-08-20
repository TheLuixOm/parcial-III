# Especificacion del Protocolo de Comunicacion - Fase 1

## Transporte

- **Capa**: Aplicacion sobre TCP
- **Puerto por defecto**: 5000
- **Codificacion de datos**: Texto UTF-8

## Estructura de la Trama

```
| Delimitador (2B) | Tipo (1B) | Secuencia (2B) | Longitud (2B) | Payload (N bytes) |
```

Todos los campos multi-byte usan **Big-Endian**.

### Campos

| Campo        | Tamano  | Descripcion                               |
|--------------|---------|-------------------------------------------|
| Delimitador  | 2 bytes | `0xAA 0x55` - marca de inicio de trama    |
| Tipo         | 1 byte  | Codigo de tipo de mensaje                 |
| Secuencia    | 2 bytes | Numero de secuencia (0-65535)             |
| Longitud     | 2 bytes | Cantidad de bytes del payload             |
| Payload      | N bytes | Datos del mensaje en UTF-8                |

**Total cabecera**: 7 bytes (sin payload)

## Tipos de Mensaje

| Codigo | Nombre | Descripcion                      |
|--------|--------|----------------------------------|
| 0x01   | DATA   | Datos enviados por el cliente    |
| 0x02   | ACK    | Confirmacion de recepcion        |
| 0x03   | NACK   | Negative acknowledgment (error) |
| 0x04   | PING   | Sonda de conexion (keep-alive)  |
| 0x05   | CLOSE  | Solicitud de cierre de conexion |

## Fase 1 - Sin robustecimiento (vulnerable a proposito)

- Sin CRC ni checksum
- Sin validacion de secuencia
- Sin timeouts ni retransmision
- Sin deteccion de duplicados

