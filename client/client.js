const net = require("net");
const readline = require("readline");
const { HOST, PORT, HEADER_SIZE, CRC_SIZE, TIMEOUT_MS, MAX_RETRIES, MSG_DATA, MSG_ACK, MSG_NACK, MSG_PING, MSG_CLOSE } = require("./config");
const { packFrame, unpackFrame, typeName } = require("./protocol");

const STATE_IDLE = 0;
const STATE_WAITING = 1;

let seq = 0;
let socket = null;
let connected = false;
let state = STATE_IDLE;
let retries = 0;
let timeoutTimer = null;
let pendingFrame = null;
let responseBuffer = Buffer.alloc(0);
let rl;

function log(msg) {
  console.log(`[CLIENT] ${msg}`);
}

function clearTimeoutTimer() {
  if (timeoutTimer) {
    clearTimeout(timeoutTimer);
    timeoutTimer = null;
  }
}

function startTimeout() {
  clearTimeoutTimer();
  timeoutTimer = setTimeout(() => {
    if (state !== STATE_WAITING) return;
    retries++;
    if (retries > MAX_RETRIES) {
      log(`AGOTADO: ${MAX_RETRIES} reintentos sin ACK para seq=${seq}`);
      state = STATE_IDLE;
      pendingFrame = null;
      retries = 0;
      rl.prompt();
      return;
    }
    log(`TIMEOUT - reenvio ${retries}/${MAX_RETRIES} seq=${seq}`);
    socket.write(pendingFrame);
    startTimeout();
  }, TIMEOUT_MS);
}

function sendDataFrame(text) {
  const s = (seq + 1) & 0xffff;
  seq = s;
  pendingFrame = packFrame(MSG_DATA, s, text);
  state = STATE_WAITING;
  retries = 0;
  socket.write(pendingFrame);
  log(`Enviado DATA seq=${s}: ${text}`);
  startTimeout();
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
      if (state === STATE_WAITING) {
        clearTimeoutTimer();
        state = STATE_IDLE;
        pendingFrame = null;
        retries = 0;
      }
    } else if (msgType === MSG_NACK) {
      log(`NACK recibido seq=${rSeq}`);
      if (state === STATE_WAITING) {
        retries++;
        if (retries > MAX_RETRIES) {
          log(`AGOTADO: ${MAX_RETRIES} reintentos sin ACK para seq=${seq}`);
          state = STATE_IDLE;
          pendingFrame = null;
          retries = 0;
        } else {
          log(`Retransmitiendo ${retries}/${MAX_RETRIES} seq=${seq}`);
          clearTimeoutTimer();
          socket.write(pendingFrame);
          startTimeout();
        }
      }
    } else if (msgType === MSG_CLOSE) {
      log(`CLOSE recibido seq=${rSeq} - conexion cerrada por servidor`);
      clearTimeoutTimer();
      cleanup();
      return;
    } else {
      const text = payload.toString("utf-8");
      log(`${typeName(msgType)} seq=${rSeq}: ${text}`);
    }
  }
}

function sendClose() {
  if (!connected) return;
  const s = (seq + 1) & 0xffff;
  seq = s;
  const frame = packFrame(MSG_CLOSE, s);
  socket.write(frame);
  log(`Enviado CLOSE seq=${s}`);
}

function cleanup() {
  connected = false;
  clearTimeoutTimer();
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
    log(`Stop-and-Wait activo (timeout=${TIMEOUT_MS}ms, max_retries=${MAX_RETRIES})`);
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
    clearTimeoutTimer();
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
      const s = (seq + 1) & 0xffff;
      seq = s;
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

    if (state === STATE_WAITING) {
      log("Esperando ACK... intenta de nuevo en un momento");
      rl.prompt();
      return;
    }

    sendDataFrame(trimmed);
    rl.prompt();
  });

  rl.on("close", () => {
    sendClose();
    setTimeout(cleanup, 500);
  });
}

main();
