import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
const out=import.meta.dirname,root=path.resolve(out,'..');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const master=JSON.parse(await fs.readFile(path.join(out,'cecs-master.json'),'utf8'));
if(master.generated_at!=='2026-10-17T05:24:50.658Z')throw new Error('Unexpected snapshot');
const manifest=JSON.parse(await fs.readFile(path.join(root,'search/freeze-inputs-1320.json'),'utf8'));
const finalized=new Date().toISOString(),verified=[];
for(const file of manifest.files){
  const bytes=await fs.readFile(path.join(root,file.path));
  if(sha(bytes)!==file.sha256||bytes.length!==file.bytes)throw new Error(`Changed source ${file.path}`);
  if(!master.external_inputs.some(r=>r.path===file.path))master.external_inputs.push({path:file.path,sha256:file.sha256,imported_at:finalized,content_kind:'text reference; not a data row'});
  verified.push({...file,verified:true});
}
master.receipt_finalized_at=finalized;
const body=JSON.stringify(master,null,2);
await fs.writeFile(path.join(out,'cecs-master.json'),body);
await fs.writeFile(path.join(out,'history',`master-${master.generated_at.replace(/[:.]/g,'-')}-receipt-finalized.json`),body,{flag:'wx'});
const xlsx=await fs.readFile(path.join(out,'CECS可下载PDF总表.xlsx'));
const receipt={checkpoint:'1320',snapshot_generated_at:master.generated_at,verified_at:finalized,search_inputs:verified,audit_sha256:master.external_inputs.find(r=>r.path==='pdf-audit/audit-results.json').sha256,master_sha256:sha(body),xlsx_sha256:sha(xlsx),xlsx_content_changed:false};
await fs.writeFile(path.join(out,'inputs-1320-receipt.json'),JSON.stringify(receipt,null,2));
console.log(JSON.stringify({input_count:verified.length,master_sha256:receipt.master_sha256,xlsx_sha256:receipt.xlsx_sha256}));
