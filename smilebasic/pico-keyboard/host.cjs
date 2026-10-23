const net = require('node:net');
const crypto = require('node:crypto');

const PORT = 39381;
const HELLO = 'CLS:PRINT "HELLO WORLD!"';

function start({host, command, key, port = PORT, onStatus = () => {}}) {
  if (!net.isIPv4(host) || !Number.isInteger(port) || port < 0 || port > 65535 ||
      (command !== HELLO && !/^V=START\([0-9,]+\)$/.test(command)) ||
      !/^[0-9a-f]{32}$/.test(key || ''))
    return Promise.reject(Error('Pico mode needs a host IPv4 address and a 32-character hex key'));
  const expected = Buffer.from(key, 'hex');
  const sockets = new Set();
  let claimed = false;
  const server = net.createServer(socket => {
    sockets.add(socket);
    socket.setTimeout(120000);
    let input = '', authorized = false, done = false;
    const reject = () => socket.destroy();
    socket.on('data', chunk => {
      input += chunk.toString('ascii');
      if (input.length > 256) return reject();
      for (let end; (end = input.indexOf('\n')) >= 0;) {
        const line = input.slice(0, end).replace(/\r$/, '');
        input = input.slice(end + 1);
        if (!authorized) {
          const supplied = /^NS2KEY1 ([0-9a-f]{32})$/.exec(line);
          if (claimed || !supplied ||
              !crypto.timingSafeEqual(Buffer.from(supplied[1], 'hex'), expected)) {
            onStatus('Keyboard bridge authentication rejected');
            return reject();
          }
          claimed = authorized = true;
          socket.write(command + '\n');
          onStatus(command === HELLO ? 'Keyboard bridge connected; Hello world command sent' : 'Keyboard bridge connected; fresh V=START command sent');
        } else if (line === 'READY') {
          onStatus('Keyboard bridge validated the command');
        } else if (line === 'TYPING') {
          socket.setTimeout(20 * 60 * 1000);
          onStatus('Keyboard bridge is entering commands in SmileBASIC');
        } else if (line === 'DONE') {
          done = true;
          onStatus('Keyboard bridge finished entering commands');
          socket.end();
        } else if (line.startsWith('ERROR ')) {
          onStatus('Keyboard bridge error: ' + line.slice(6, 100));
          return reject();
        } else return reject();
      }
    });
    socket.on('timeout', reject);
    socket.on('error', () => {});
    socket.on('close', () => {
      sockets.delete(socket);
      if (authorized && !done) onStatus('Keyboard bridge disconnected before confirming completion; inspect the Switch screen');
    });
  });
  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(port, host, () => {
      server.off('error', reject);
      resolve({port: server.address().port, close: () => {
        for (const socket of sockets) socket.destroy();
        return new Promise(done => server.close(done));
      }});
    });
  });
}

module.exports = {start, PORT, HELLO};
