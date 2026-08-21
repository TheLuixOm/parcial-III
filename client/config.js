module.exports = {
  HOST: process.env.HOST || "127.0.0.1",
  PORT: parseInt(process.env.PORT || "9002", 10),
  HEADER_SIZE: 7,
  CRC_SIZE: 4,

  TIMEOUT_MS: 3000,  // timeout Stop-and-Wait en ms
  MAX_RETRIES: 3,    // maximo reintentos ante timeout/NACK

  MSG_DATA: 0x01,
  MSG_ACK: 0x02,
  MSG_NACK: 0x03,
  MSG_PING: 0x04,
  MSG_CLOSE: 0x05,
  MSG_ERROR: 0x06,

  ERR_BAD_DELIMITER: 0x01,
  ERR_BAD_LENGTH: 0x02,
  ERR_BAD_CRC: 0x03,
  ERR_UNKNOWN_TYPE: 0x04,

  MSG_NAMES: {
    0x01: "DATA",
    0x02: "ACK",
    0x03: "NACK",
    0x04: "PING",
    0x05: "CLOSE",
    0x06: "ERROR",
  },

  ERROR_NAMES: {
    0x01: "BAD_DELIMITER",
    0x02: "BAD_LENGTH",
    0x03: "BAD_CRC",
    0x04: "UNKNOWN_TYPE",
  },
};
