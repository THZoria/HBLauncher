const fs=require('node:fs'),path=require('node:path');
function tool(environment,name){
 const local=path.resolve(__dirname,'../tools',name+(process.platform==='win32'?'.exe':''));
 return process.env[environment]||(fs.existsSync(local)?local:name);
}
function python(){return process.env.PYTHON||(process.platform==='win32'?'python':'python3');}
module.exports={tool,python};
