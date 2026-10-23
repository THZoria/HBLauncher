// Local dependency checks only; never prints pairing keys or Wi-Fi settings.
const fs=require('node:fs'),path=require('node:path'),{spawnSync}=require('node:child_process');
const {tool,python}=require('./toolchain.cjs');const root=path.resolve(__dirname,'..');let failed=false;
function check(name,ok,fix){console.log((ok?'OK   ':'NEED ')+name+(ok?'':' — '+fix));if(!ok)failed=true;}
function runs(command,args){const r=spawnSync(command,args,{stdio:'ignore'});return !r.error&&r.status===0;}
check('Node.js 22+',Number(process.versions.node.split('.')[0])>=22,'Install Node.js 22 or newer');
check('Python 3 + Pillow',runs(python(),['-c','from PIL import Image,ImageDraw,ImageFont']),'Install Python 3 and Pillow');
check('TrueType font',runs(python(),['-c',`import sys; sys.path.insert(0, ${JSON.stringify(__dirname)}); from font import font_path; font_path()`]),'Install DejaVu Sans or set HB_FONT');
check('SPIR-V validator',runs(tool('SPIRV_VAL','spirv-val'),['--version']),'Install spirv-tools or set SPIRV_VAL');
for(const file of ['homebrew-launcher/shaders/launcher.comp.spv','homebrew-launcher/shaders/launcher.frag.spv','apps/hello-world/app.json'])check(file,fs.existsSync(path.join(root,file)),'Use the complete release archive');
if(!process.argv.includes('--host-only')){let key='';try{key=fs.readFileSync(path.join(root,'smilebasic/pico-keyboard/secret'),'utf8').trim();}catch{}check('Local keyboard pairing key',/^[a-f0-9]{32}$/i.test(key),'Run node smilebasic/pi-keyboard/pair.cjs, then copy the secret file to the Pi');}
if(process.argv.includes('--build'))check('GLSL compiler',runs(tool('GLSLANG','glslangValidator'),['--version']),'Install glslang-tools or set GLSLANG');
if(failed)process.exitCode=1;else console.log('Host checks passed. Check console versions, USB gadget and network reachability on the devices.');
