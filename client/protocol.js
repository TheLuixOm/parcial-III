const { HEADER_SIZE, MSG_NAMES } = require("./config");

const DELIMITER = Buffer.from([0xaa, 0x55]);

function packFrame(msgType, seq, payload = "") {
  if (typeof payload === "string") {
    payload = Buffer.from(payload, "utf-8");
  }
  const length = payload.length;
  const header = Buffer.alloc(7);
  DELIMITER.copy(header, 0);
  header[2] = msgType;
  header.writeUInt16BE(seq, 3);
  header.writeUInt16BE(length, 5);
  return Buffer.concat([header, payload]);
}

function unpackFrame(data) {
  if (data.length < HEADER_SIZE) {
    return null;
  }
  if (data[0] !== 0xaa || data[1] !== 0x55) {
    return null;
  }
  const msgType = data[2];
  const seq = data.readUInt16BE(3);
  const length = data.readUInt16BE(5);
  const totalSize = HEADER_SIZE + length;

  if (data.length < totalSize) {
    return null;
  }

  const payload = data.subarray(HEADER_SIZE, totalSize);
  const remaining = data.subarray(totalSize);

  return { msgType, seq, payload, remaining };
}

function typeName(msgType) {
  return MSG_NAMES[msgType] || `UNKNOWN(0x${msgType.toString(16).padStart(2, "0")})`;
}

module.exports = { packFrame, unpackFrame, typeName };
