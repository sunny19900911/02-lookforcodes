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
if(model.coverage.verified_complete_draft_pdf_links){const end=8+model.coverage.verified_complete_draft_pdf_links;targets.push(['draft-identity','完整草案PDF',`A8:F${end}`],['draft-navigation','完整草案PDF',`H8:M${end}`],['draft-scope','完整草案PDF',`T8:V${end}`]);}
if(['1410','1510'].includes(model.scope.checkpoint)){
  const sorted=[...model.standards].sort((a,b)=>Number(b.baseline)-Number(a.baseline)||a.standard_number?.localeCompare(b.standard_number??'','en',{numeric:true})||a.standard_id.localeCompare(b.standard_id));
  const platformRow=9+sorted.findIndex(s=>s.standard_id==='CECS-2253-2026-FORMAL');
  targets.push(['ttbz-current-status','规范总表',`A${platformRow}:G${platformRow}`],['ttbz-dates','规范总表',`L${platformRow}:N${platformRow}`],['ttbz-announcement','规范总表',`Y${platformRow}:Z${platformRow}`]);
  for(const sid of ['CECS-1137-2022-FORMAL','CECS-22-2012-FORMAL']){const r=9+sorted.findIndex(s=>s.standard_id===sid);targets.push([`conflict-${sid}`,'规范总表',`A${r}:B${r}`]);}
  for(const sid of ['CECS-212-2006-FORMAL','CECS-235-2008-FORMAL','CECS-122-2001-FORMAL','CECS-17-2000-FORMAL']){const r=9+complete.findIndex(l=>l.verified_standard_ids?.includes(sid));targets.push([`new-formal-${sid}`,'已验完整PDF',`A${r}:G${r}`]);}
}
if(model.scope.checkpoint==='1510'){
  targets.push(['regions-first-rows','地区下载索引','A8:G14'],['regions-evidence','地区下载索引','K8:M11']);
  const sorted=[...model.standards].sort((a,b)=>Number(b.baseline)-Number(a.baseline)||a.standard_number?.localeCompare(b.standard_number??'','en',{numeric:true})||a.standard_id.localeCompare(b.standard_id));
  const old69=9+sorted.findIndex(s=>s.standard_id==='CECS-69-1994-FORMAL');
  targets.push(['old69-status','规范总表',`A${old69}:G${old69}`],['old69-repeal','规范总表',`X${old69}:Y${old69}`]);
  for(const n of ['1555','200','197']){
    const idx=model.links.findIndex(l=>l.standard_ids.some(id=>id.startsWith(`CECS-${n}-`))&&l.checked_at&&(!['1555','200'].includes(n)||l.recommendation==='D'));
    if(idx<0)throw new Error(`Missing saved body check ${n}`);
    const r=9+idx;targets.push([`body-${n}-overall`,'链接明细',`S${r}:V${r}`],[`body-${n}-separate`,'链接明细',`AR${r}:AU${r}`]);
  }
}
for(const [name,sheet,range] of targets){const blob=await workbook.render({sheetName:sheet,range,scale:1.4,format:'png'});await fs.writeFile(path.join(out,'previews',`${name}.png`),new Uint8Array(await blob.arrayBuffer()));}
console.log(JSON.stringify({read_only:true,new22_excel_row:row,edition2012_excel_row:stdRow}));
