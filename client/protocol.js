const { HEADER_SIZE, CRC_SIZE, MSG_NAMES } = require("./config");

const DELIMITER = Buffer.from([0xaa, 0x55]);

const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let crc = i;
    for (let j = 0; j < 8; j++) {
      crc = crc & 1 ? (crc >>> 1) ^ 0xedb88320 : crc >>> 1;
    }
    table[i] = crc >>> 0;
  }
  return table;
})();

function calcCrc32(buf) {
  let crc = 0xffffffff;
  for (let i = 0; i < buf.length; i++) {
    crc = CRC_TABLE[(crc ^ buf[i]) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function packFrame(msgType, seq, payload = "") {
  if (typeof payload === "string") {
    payload = Buffer.from(payload, "utf-8");
  }
  const length = payload.length;
  const header = Buffer.alloc(HEADER_SIZE);
  DELIMITER.copy(header, 0);
  header[2] = msgType;
  header.writeUInt16BE(seq, 3);
  header.writeUInt16BE(length, 5);

  const typeBuf = Buffer.alloc(1);
  typeBuf[0] = msgType;
  const seqBuf = Buffer.alloc(2);
  seqBuf.writeUInt16BE(seq, 0);
  const lenBuf = Buffer.alloc(2);
  lenBuf.writeUInt16BE(length, 0);
  const crcData = Buffer.concat([typeBuf, seqBuf, lenBuf, payload]);
  const crc = calcCrc32(crcData);
  const crcField = Buffer.alloc(CRC_SIZE);
  crcField.writeUInt32BE(crc, 0);

  return Buffer.concat([header, payload, crcField]);
}

function unpackFrame(data) {
  const minFrame = HEADER_SIZE + CRC_SIZE;
  if (data.length < minFrame) {
    return null;
  }
  if (data[0] !== 0xaa || data[1] !== 0x55) {
    return null;
  }
  const msgType = data[2];
  const seq = data.readUInt16BE(3);
  const length = data.readUInt16BE(5);
  const totalSize = HEADER_SIZE + length + CRC_SIZE;

  if (data.length < totalSize) {
    return null;
  }

  const payload = data.subarray(HEADER_SIZE, HEADER_SIZE + length);
  const crcReceived = data.readUInt32BE(HEADER_SIZE + length);

  const typeBuf = Buffer.alloc(1);
  typeBuf[0] = msgType;
  const seqBuf = Buffer.alloc(2);
  seqBuf.writeUInt16BE(seq, 0);
  const lenBuf = Buffer.alloc(2);
  lenBuf.writeUInt16BE(length, 0);
  const crcData = Buffer.concat([typeBuf, seqBuf, lenBuf, payload]);
  const crcComputed = calcCrc32(crcData);

  const remaining = data.subarray(totalSize);

  return { msgType, seq, payload, valid: crcReceived === crcComputed, remaining };
}

function typeName(msgType) {
  return MSG_NAMES[msgType] || `UNKNOWN(0x${msgType.toString(16).padStart(2, "0")})`;
}

module.exports = { packFrame, unpackFrame, typeName };
