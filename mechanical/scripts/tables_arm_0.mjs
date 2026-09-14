import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const root=process.cwd();
const require=createRequire(path.join(root,'analysis/v4/table_runtime/package.json'));
const {Workbook}=await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const matrices=JSON.parse(await fs.readFile(path.join(root,'analysis/v4/tables_input.json'),'utf8'));
const cfg=JSON.parse(await fs.readFile(path.join(root,'mechanical/arm_0_parameters.json'),'utf8'));
const params=matrices['parameter_summary.csv'];
for(const r of params.slice(1))if(r[2]==='mm unless count/ratio')r[2]=r[0]==='MotorCount'?'count':'mm';
for(const key of ['MotorCount','FoldLane','UpperLane'])if(!params.some(r=>r[0]===key))params.push([key,cfg.dimensions[key],key==='MotorCount'?'count':'mm','CONFIRMED_BASELINE','Frozen']);
const manifestRows=matrices['assembly_manifest.csv'];
const owners=new Map(manifestRows.slice(1).map(r=>[r[0],r[manifestRows[0].indexOf('rigid_link')]]));
const interfaceOwners=new Map();
for(const r of matrices['fastener_schedule.csv'].slice(1)){
 if(r[8]==='METAL_TAPPED_THREAD' && r[2]===r[3]){r[7]='Upper jaw diameter 3.4 through to split; lower jaw diameter 2.5 M3 tap pilot; depth TBD';r[16]+=' | Do not clearance-drill both clamp jaws.';}
 const owner=r[11].split(' in ').at(-1);interfaceOwners.set(r[0],owner);
 r[16]=r[16].replace(/(removal prerequisites: detached rigid subassembly; )([^|]*)/,(all,prefix,list)=>prefix+list.split(',').map(v=>v.trim()).filter(n=>n==='CHILD_LINKS'||owners.get(n)===owner).join(', ')+' ');
}
// Remove irrelevant cross-link names from the displayed prerequisite list only.
// The checker already tests the detached rigid subassembly, so numerical results are unchanged.
const validationPath=path.join(root,'analysis/v4/assembly_validation.json');
const validation=JSON.parse(await fs.readFile(validationPath,'utf8'));
for(const r of validation.service)r.remove=r.remove.filter(n=>n==='CHILD_LINKS'||owners.get(n)===interfaceOwners.get(r.id));
await fs.writeFile(validationPath,JSON.stringify(validation,null,2),'utf8');
const bom=matrices['arm_0_BOM.csv'];
matrices['arm_0_BOM.csv']=[bom[0],...bom.slice(1).filter(r=>r[3]!=='rotor').map(r=>{
 if(r[3]==='motor'){const original=r[1];r[1]=original.replace('_Stator','_Motor');r[3]='MOTOR_REFERENCE';r[4]='Purchased motor';r[5]='Purchased';r[9]=`One motor assembly: ${original} + ${original.replace('_Stator','_Rotor')} reference shapes. Hardware verify.`;}
 return r;
})];
matrices['fastener_schedule.csv']=[matrices['fastener_schedule.csv'][0],...matrices['fastener_schedule.csv'].slice(1).sort((a,b)=>a[0].localeCompare(b[0]))];
const workbook=Workbook.create();
function Column_GetName(n){let s='';while(n){n--;s=String.fromCharCode(65+n%26)+s;n=Math.floor(n/26);}return s;}
const sheets=[];
for(const [file,matrix] of Object.entries(matrices)){
  const sheet=workbook.worksheets.add(file.replace('.csv',''));const address=`A1:${Column_GetName(matrix[0].length)}${matrix.length}`;
  if(matrix.some(row=>row.length!==matrix[0].length))throw new Error('Ragged table '+file);
  sheet.getRange(address).values=matrix;sheets.push({file,sheet,address,matrix});
}
await workbook.recalculate();
const audit=[];
for(const {file,sheet,address,matrix} of sheets){
  const values=sheet.getRange(address).values;
  if(values.length!==matrix.length)throw new Error('Row loss '+file);
  const csv=values.map(row=>row.map(v=>'"'+String(v??'').replaceAll('"','""')+'"').join(',')).join('\r\n')+'\r\n';
  const imported=await Workbook.fromCSV(csv,{sheetName:'Verify'});
  const back=imported.worksheets.getItem('Verify').getRange(address).values;
  if(back.length!==values.length)throw new Error('CSV roundtrip '+file);
  for(let r=0;r<values.length;r++)for(let c=0;c<values[r].length;c++)if(String(back[r][c]??'')!==String(values[r][c]??''))throw new Error(`CSV mismatch ${file} ${r} ${c}`);
  await fs.writeFile(path.join(root,'mechanical/docs',file),'\ufeff'+csv,'utf8');
  audit.push({file,rows:values.length-1,columns:values[0].length,roundtrip:true,sha256:createHash('sha256').update('\ufeff'+csv,'utf8').digest('hex')});
}
const fast=matrices['fastener_schedule.csv'];const receivers=new Set(['CYBERGEAR_THREAD','METAL_TAPPED_THREAD','HEX_NUT','LOCK_NUT','FOUR_WAY_NUT_BLOCK']);
if(new Set(fast.slice(1).map(r=>r[0])).size!==fast.length-1||fast.slice(1).some(r=>!receivers.has(r[8])))throw new Error('Fastener IDs / receivers');
console.log((await workbook.inspect({kind:'region',sheetId:'fastener_schedule',range:'A1:F4',maxChars:1200,tableMaxCols:6,tableMaxRows:4})).ndjson);
const preview=Workbook.create();const sh=preview.worksheets.add('Review');
sh.getRange('A1:D7').values=[['Table','Rows','Columns','CSV roundtrip'],...audit.map(v=>[v.file,v.rows,v.columns,'PASS'])];
sh.getRange('A1:A7').format.columnWidth=34;sh.getRange('B1:D7').format.columnWidth=18;sh.getRange('A1:D1').format.font.bold=true;
await preview.recalculate();const png=await preview.render({sheetName:'Review',autoCrop:'all',scale:1.5,format:'png'});await fs.writeFile(path.join(root,'analysis/v4/table_preview.png'),new Uint8Array(await png.arrayBuffer()));
await fs.writeFile(path.join(root,'analysis/v4/table_checks.json'),JSON.stringify(audit,null,2));
console.log(JSON.stringify(audit));
