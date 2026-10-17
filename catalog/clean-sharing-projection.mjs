import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {cleanSharingExternal} from './sharing-projection-core.mjs';
const out=import.meta.dirname,root=path.resolve(out,'..');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const masterPath=path.join(out,'cecs-master.json'),before=await fs.readFile(masterPath);
const master=JSON.parse(before),target=master.external.search[43];
if(!target?.candidate_id||!Object.hasOwn(target,'redirect_entry'))throw new Error('Unexpected target record');
const origins=[];
for(const input of master.external_inputs.filter(i=>i.path.startsWith('search/')&&i.path.endsWith('.json')&&!/web[-_]/i.test(path.basename(i.path)))){
  const source=JSON.parse(await fs.readFile(path.join(root,input.path),'utf8'));
  if((source.candidates??[]).some(c=>c.candidate_id===target.candidate_id&&Object.hasOwn(c,'redirect_entry')))origins.push({path:input.path,sha256:input.sha256});
}
if(origins.length!==1)throw new Error(`Expected one source file; got ${origins.length}`);
target._catalog_source=origins[0];
const changes=cleanSharingExternal(master.external);
if(changes.length!==1||changes[0].path!=='/external/search/43/redirect_entry')throw new Error('Unexpected redaction scope');
const at=new Date().toISOString();
master.external.sharing_projection={version:1,created_at:at,raw_master_sha256:sha(before),changed_paths:changes.map(c=>c.path),policy:'Transient query values removed from sharing projection; immutable source remains local. No parameter values copied to logs.'};
const body=JSON.stringify(master,null,2);
await fs.writeFile(masterPath,body);
await fs.writeFile(path.join(out,'history',`master-${master.generated_at.replace(/[:.]/g,'-')}-sharing-projection.json`),body,{flag:'wx'});
const receipt={created_at:at,snapshot_generated_at:master.generated_at,source:origins[0],changed_paths:changes.map(c=>c.path),raw_master_sha256:sha(before),sharing_master_sha256:sha(body),xlsx_sha256:sha(await fs.readFile(path.join(out,'CECS可下载PDF总表.xlsx'))),xlsx_unchanged:true};
await fs.writeFile(path.join(out,'sharing-projection-receipt.json'),JSON.stringify(receipt,null,2));
console.log(JSON.stringify(receipt));
