module.exports = {
  HOST: "127.0.0.1",
  PORT: 9002,
  HEADER_SIZE: 7,

  MSG_DATA: 0x01,
  MSG_ACK: 0x02,
  MSG_NACK: 0x03,
  MSG_PING: 0x04,
  MSG_CLOSE: 0x05,

  MSG_NAMES: {
    0x01: "DATA",
    0x02: "ACK",
    0x03: "NACK",
    0x04: "PING",
    0x05: "CLOSE",
  },
};
