// Create the existing keyboard bridge pairing key without installing a Pico.
const fs=require('node:fs'),crypto=require('node:crypto'),path=require('node:path');
const file=path.resolve(__dirname,'../pico-keyboard/secret');
if(!fs.existsSync(file))fs.writeFileSync(file,crypto.randomBytes(16).toString('hex'),{flag:'wx',mode:0o600});
const key=fs.readFileSync(file,'utf8').trim();
if(!/^[0-9a-f]{32}$/i.test(key))throw Error('Existing pairing key is invalid');
console.log('Shared key ready: smilebasic/pico-keyboard/secret. Copy the file securely to the Pi.');
