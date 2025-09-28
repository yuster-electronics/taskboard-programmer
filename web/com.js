function appendLog(txt){
    log.value += txt + "\n";
    log.scrollTop = log.scrollHeight;
}

async function connect() {
    try {
        // Request a port (shows browser dialog)
        port = await navigator.serial.requestPort();
        const baud = 115200;
        await port.open({
            baudRate: baud,     // adjust as needed
            dataBits: 8,        // 8 data bits
            parity: "none",     // no parity
            stopBits: 1,        // 1 stop bit
            flowControl: "none" // (or "hardware" for RTS/CTS)
        });

        btnConnect.disabled = true;
        btnDisconnect.disabled = false;
        sendBtn.disabled = false;
        clearBtn.disabled = false;

        // Setup reader
        const textDecoder = new TextDecoderStream();
        readableStreamClosed = port.readable.pipeTo(textDecoder.writable);
        reader = textDecoder.readable.getReader();

        // Setup writer
        const textEncoder = new TextEncoderStream();
        writableStreamClosed = textEncoder.readable.pipeTo(port.writable);
        writer = textEncoder.writable.getWriter();

        const resp = await queryCmd("i");
        if (resp.startsWith("TaskBoard")) {
            appendLog("Connected to " + resp);
        } else {
            appendLog("Connected to TaskBoard");
        }

        // Read loop
        // readLoop();
    } catch (err) {
        appendLog("Error: " + err);
    }
}

async function readLoop() {
    try {
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            if (value) appendLog("RX: " + value);
        }
    } catch (err) {
        appendLog("Read error: " + err);
    } finally {
        reader && reader.releaseLock();
    }
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function flushRx() {
    if (!reader) return;
    try {
        while (true) {
            const { value, done } = await reader.read();
            if (done || !value) break;
            // discard value
        }
    } catch {
    // ignore
    }
}

async function queryCmd(cmd) {
    flushRx();
    sendCmd(cmd);
    const resp = await readWithTimeout(1000);
    return resp.value;
}

async function readWithTimeout(timeoutMs) {
    return await Promise.race([
        reader.read(),
        new Promise(resolve => setTimeout(() => resolve({done:true}), timeoutMs))
    ]);
}

async function disconnect(){
    try {
        appendLog("Disconnecting...");
        if (reader) { await reader.cancel(); reader.releaseLock(); reader = null; }
        if (writer) { await writer.close(); writer.releaseLock(); writer = null; }
        if (readableStreamClosed) await readableStreamClosed.catch(()=>{});
        if (writableStreamClosed) await writableStreamClosed.catch(()=>{});
        if (port) { await port.close(); port = null; }
        appendLog("Disconnected");
    } catch (err) {
        appendLog("Disconnect error: "+err);
    } finally {
        btnConnect.disabled = false;
        btnDisconnect.disabled = true;
        sendBtn.disabled = true;
    }
}

async function send(title_text, desc_text) {
    let data = "\x00" + String.fromCharCode(title_text.length) + title_text + String.fromCharCode(desc_text.length) + desc_text;
    const crc = xorChecksum(data)
    data += String.fromCharCode(crc)

    if (!writer) { appendLog("Not connected"); return; }
    try {
        await writer.write(data);
    } catch (err) {
        appendLog("Write error: " + err);
    }
}

async function sendCmd(cmd) {
    let data = cmd
    const crc = xorChecksum(data)
    data += String.fromCharCode(crc)

    if (!writer) { appendLog("Not connected"); return; }
    try {
        await writer.write(data);
    } catch (err) {
        appendLog("Write error: " + err);
    }
}

function send_tag() {
    const title_text = clean_string(title.value);
    const desc_text = clean_string(desc.value + "\n");
    send(title_text, desc_text);
}

function clear_tag() {
    title.value = '';
    desc.value = '';
    // send('', '');
    queryCmd("i");
}

function xorChecksum(str) {
    let crc = 0;
    for (let i = 0; i < str.length; i++) {
        crc ^= str.charCodeAt(i) & 0xFF;
    }
    return crc & 0xFF; // ensure 8-bit
}

// Feature detection
if (!("serial" in navigator)) {
    appendLog("Web Serial API not supported in this browser. Use Chrome/Edge (Chromium) or use server-side proxy.");
}
