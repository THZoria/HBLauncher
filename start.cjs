// Start the existing console host directly on Windows or Linux.
const path=require('node:path'),{spawnSync}=require('node:child_process');
const root=__dirname;
const result=spawnSync(process.execPath,[path.join(root,'scripts/doctor.cjs')],{cwd:root,stdio:'inherit'});
if(result.error||result.status!==0){if(result.error)console.error(result.error);process.exitCode=result.status||1;}
else require('./homebrew-launcher/start-launcher.cjs');
