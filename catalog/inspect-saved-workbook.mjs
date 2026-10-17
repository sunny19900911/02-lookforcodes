import fs from 'node:fs/promises';
import path from 'node:path';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const out=import.meta.dirname;
const model=JSON.parse(await fs.readFile(path.join(out,'cecs-master.json'),'utf8'));
const workbook=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(out,'CECS可下载PDF总表.xlsx')));
const complete=model.links.filter(l=>l.complete_pdf&&l.active);
const row=9+complete.findIndex(l=>l.verified_standard_ids?.includes('CECS-22-2024-FORMAL'));
const stdRow=9+[...model.standards].sort((a,b)=>Number(b.baseline)-Number(a.baseline)||a.standard_number?.localeCompare(b.standard_number??'','en',{numeric:true})||a.standard_id.localeCompare(b.standard_id)).findIndex(s=>s.standard_id==='CECS-102-2002-FORMAL-E2012');
const old22Row=9+[...model.standards].sort((a,b)=>Number(b.baseline)-Number(a.baseline)||a.standard_number?.localeCompare(b.standard_number??'','en',{numeric:true})||a.standard_id.localeCompare(b.standard_id)).findIndex(s=>s.standard_id==='CECS-22-2005-FORMAL');
const targets=[['new22-recommendation','已验完整PDF',`A${row}:E${row}`],['new22-navigation','已验完整PDF',`H${row}:M${row}`],['102-edition','规范总表',`A${stdRow}:G${stdRow}`],['old22-status','规范总表',`E${old22Row}:F${old22Row}`],['old22-basis','规范总表',`X${old22Row}:Y${old22Row}`]];
if(model.coverage.verified_complete_draft_pdf_links)targets.push(['draft-identity','完整草案PDF','A8:F9'],['draft-navigation','完整草案PDF','H8:M9'],['draft-scope','完整草案PDF','T8:V9']);
for(const [name,sheet,range] of targets){const blob=await workbook.render({sheetName:sheet,range,scale:1.4,format:'png'});await fs.writeFile(path.join(out,'previews',`${name}.png`),new Uint8Array(await blob.arrayBuffer()));}
console.log(JSON.stringify({read_only:true,new22_excel_row:row,edition2012_excel_row:stdRow}));
