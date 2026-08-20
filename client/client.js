const net = require("net");
const readline = require("readline");
const { HOST, PORT, HEADER_SIZE, CRC_SIZE, MSG_DATA, MSG_ACK, MSG_NACK, MSG_PING, MSG_CLOSE } = require("./config");
const { packFrame, unpackFrame, typeName } = require("./protocol");

let seq = 0;
let socket = null;
let connected = false;
let responseBuffer = Buffer.alloc(0);
let rl;

function nextSeq() {
  seq = (seq + 1) & 0xffff;
  return seq;
}

function log(msg) {
  console.log(`[CLIENT] ${msg}`);
}

function processDataBuffer() {
  while (responseBuffer.length >= HEADER_SIZE + CRC_SIZE) {
    const result = unpackFrame(responseBuffer);
    if (!result) break;

    const { msgType, seq: rSeq, payload, valid, remaining } = result;
    responseBuffer = remaining;

    if (!valid) {
      log(`CRC INVALIDO en ${typeName(msgType)} seq=${rSeq} - trama descartada`);
      continue;
    }

    if (msgType === MSG_ACK) {
      log(`ACK recibido seq=${rSeq}`);
    } else if (msgType === MSG_NACK) {
      log(`NACK recibido seq=${rSeq} - servidor rechazo la trama (CRC invalido)`);
    } else if (msgType === MSG_CLOSE) {
      log(`CLOSE recibido seq=${rSeq} - conexion cerrada por servidor`);
      cleanup();
      return;
    } else {
      const text = payload.toString("utf-8");
      log(`${typeName(msgType)} seq=${rSeq}: ${text}`);
    }
  }
}

function sendMessage(text) {
  if (!connected) {
    log("No hay conexion activa");
    return;
  }
  const s = nextSeq();
  const frame = packFrame(MSG_DATA, s, text);
  socket.write(frame);
  log(`Enviado DATA seq=${s}: ${text}`);
}

function sendClose() {
  if (!connected) return;
  const s = nextSeq();
  const frame = packFrame(MSG_CLOSE, s);
  socket.write(frame);
  log(`Enviado CLOSE seq=${s}`);
}

function cleanup() {
  connected = false;
  if (socket) {
    socket.destroy();
    socket = null;
  }
  process.exit(0);
}

function main() {
  rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    prompt: "> ",
  });

  socket = new net.Socket();

  socket.connect(PORT, HOST, () => {
    connected = true;
    log(`Conectado a ${HOST}:${PORT}`);
    log("Escribe mensajes para enviar. Comandos: /ping, /close, /quit");
    rl.prompt();
  });

  socket.on("data", (data) => {
    responseBuffer = Buffer.concat([responseBuffer, data]);
    processDataBuffer();
    if (connected) rl.prompt();
  });

  socket.on("error", (err) => {
    log(`Error de conexion: ${err.message}`);
    connected = false;
  });

  socket.on("close", () => {
    if (connected) {
      log("Conexion cerrada");
      connected = false;
    }
  });

  rl.on("line", (line) => {
    const trimmed = line.trim();
    if (!trimmed) {
      rl.prompt();
      return;
    }

    if (trimmed === "/quit" || trimmed === "/exit") {
      sendClose();
      setTimeout(cleanup, 500);
      return;
    }

    if (trimmed === "/ping") {
      const s = nextSeq();
      const frame = packFrame(MSG_PING, s);
      socket.write(frame);
      log(`Enviado PING seq=${s}`);
      rl.prompt();
      return;
    }

    if (trimmed === "/close") {
      sendClose();
      return;
    }

    sendMessage(trimmed);
    rl.prompt();
  });

  rl.on("close", () => {
    sendClose();
    setTimeout(cleanup, 500);
  });
}

main();
