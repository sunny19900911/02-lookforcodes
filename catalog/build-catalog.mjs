import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';

const root = path.resolve(import.meta.dirname, '..');
const out = import.meta.dirname;
const seedPath = path.resolve(root, '../cecs-catalog-20261017/CECS目录与下载路径.json');
const now = new Date().toISOString();
const sha = s => crypto.createHash('sha256').update(s).digest('hex');
const clean = s => String(s ?? '').normalize('NFKC').trim();
const slug = s => sha(s).slice(0,12);
const readJson = async p => { try{return JSON.parse((await fs.readFile(p,'utf8')).replace(/^\uFEFF/,''));}catch(e){if(e.code==='ENOENT') return null; throw e;} };
await fs.mkdir(out,{recursive:true});

function identify(raw, explicitYear=null, explicitStage=null) {
  const text = clean(raw).replace(/[∕／]/g,'/');
  const family = /CECS\s*-\s*CBIMU/i.test(text)?'CECS-CBIMU':'CECS';
  const parseText=text.replace(/CECS\s*-\s*CBIMU/i,'CECS');
  const codeMatch = parseText.match(/CECS(?:[\s_\-]*T)?[\s_\-]*(G\s*[:：]\s*[A-Z]\d+(?:-\d+)?|\d+|XXX)(?:\s*[:：\-]\s*|\s+)(19\d{2}|20\d{2}|\d{2}|202X)(?!\d)/i);
  const looseMatch = parseText.match(/CECS(?:[\s_\-]*T)?[\s_\-]*(G\s*[:：]\s*[A-Z]\d+(?:-\d+)?|\d+|XXX)(?!\d)/i);
  const m=codeMatch || looseMatch;
  const rawNumber = m?.[1]?.replace(/\s+/g,'').toUpperCase() ?? null;
  const number = /^\d+$/.test(rawNumber??'') ? String(Number(rawNumber)) : rawNumber;
  const yearText = explicitYear ? String(explicitYear) : codeMatch?.[2] ?? null;
  let year = yearText && /^(19|20)\d{2}$/.test(yearText) ? Number(yearText) : null;
  const issues=[];
  if (yearText && /^\d{2}$/.test(yearText)) {year=Number(yearText)>=50?1900+Number(yearText):2000+Number(yearText);issues.push(`文件名两位年份${yearText}按${year}登记，待权威核对`);}
  if(!number || number==='XXX') issues.push('标准编号不完整，待核实');
  if(year===null) issues.push('标准年份缺失或不完整，待核实');
  const report=/报批/.test(text) || /报批/.test(explicitStage??'');
  const draft=/征求意见|202X|XXX/i.test(text) || /征求意见|草案/.test(explicitStage??'');
  const stage=report?'报批稿':draft?'征求意见稿':'正式文本候选';
  const edition=(text.match(/(?:19|20)\d{2}年版/)?.[0]??null);
  const editionYear=edition?Number(edition.slice(0,4)):null;
  const identity=number && number!=='XXX'?`${family}-${number.replace(/[:]/g,'_')}-${year??'YEAR-UNKNOWN'}-${stage==='报批稿'?'APPROVAL-DRAFT':stage==='征求意见稿'?'CONSULT-DRAFT':'FORMAL'}${editionYear?`-E${editionYear}`:''}`:`CECS-UNRESOLVED-${slug(text)}`;
  let name=text.replace(/\.(?:pdf|docx?|zip)$/i,'').replace(/^T\s*[\/_\-]?\s*CHES\s*\d+[-:]\d{4}\s*/i,'');
  name=name.replace(/(?:T\s*[\/_\-]?\s*)?CECS(?:[\s_\-]*T)?[\s_\-]*(?:G\s*[:：]\s*[A-Z]\d+(?:-\d+)?|\d+|XXX)(?:(?:\s*[:：\-]\s*|\s+)(?:19\d{2}|20\d{2}|\d{2}|202X)(?!\d))?(?:-T)?/i,'').replace(/(?:19|20)\d{2}年版/,'').replace(/[《》【】_]/g,' ').replace(/征求意见稿|报批稿|作废|废止/g,'').replace(/\s*-\s*\d{8}$/,'').replace(/^[\s-]+|[\s-]+$/g,'').replace(/\s+/g,' ');
  const prefix=/(?:T\s*[\/_\-]?\s*CECS|CECS[\s_\-]*T|CECS\s*\d+\s*[:\-]\s*\d{4}\s*-T)/i.test(text)?'T/CECS':'CECS';
  return {id:identity,number,raw_number:rawNumber,family,year,year_text:yearText,name,stage,edition_label:edition,published_code_candidate: `${family==='CECS-CBIMU'?'T/CECS-CBIMU':prefix} ${number??'?'}${year?`-${year}`:''}`,issues};
}

const seed=await readJson(seedPath);
const groupData=await readJson(path.join(root,'search/seed-groups.json'));
const groupMap=new Map();
for(const g of groupData?.groups??[]) for(const id of g.ids) groupMap.set(Number(id),{id:g.id,name:g.name});
const groups=groupData?.groups?.map(g=>({id:g.id,name:g.name,seed_records:g.ids.length}))??[];
const standards=new Map(), links=new Map(), evidence=[], issues=[], original=[];
const evidenceKeys=new Set();
function addEvidence(e){const key=sha(JSON.stringify(e));if(!evidenceKeys.has(key)){evidenceKeys.add(key);evidence.push({evidence_id:`E-${key.slice(0,12)}`,...e});}return `E-${key.slice(0,12)}`;}
function addStandard(id, fields={}) {
  let s=standards.get(id);
  if(!s){s={standard_id:id,active:true,maintenance_action:'新增',baseline:false,original_names:[],seed_ids:[],standard_number:null,name:'',year:null,version_stage:'正式文本候选',edition_label:null,standard_type:'CECS协会标准/团体标准（具体类别待权威核验）',topic_group:null,topic_group_name:null,scope:'待核实',current_status:'未知',replacement_relationships:[],status_evidence_ids:[],status_checked_at:null,published_date:null,effective_date:null,source_pages:[],link_ids:[],best_link_id:null,usable_alternative_count:0,issues:[],created_at:now,updated_at:now,metadata_evidence_ids:[],directory_memberships:[],...fields};standards.set(id,s);}return s;
}
function addLink(s,url,fields={}) {
  if(!url)return null;
  const linkId=`L-${slug(url)}`;
  let l=links.get(linkId);
  if(!l){l={link_id:linkId,standard_ids:[],active:true,maintenance_action:'新增',source_page:null,requested_url:url,final_url:null,discovery_url:url,discovered_at:now,source_kind:'候选来源',download_status:'候选未实测',checked_at:null,http_status:null,access_restriction:null,url_expiry:null,pdf_bytes:null,pages:null,sha256:null,parse_ok:null,version_match:null,text_layer:null,search_copy:null,bookmarks:null,bookmark_navigation:null,clickable_toc:null,clarity:null,page_order:null,cropping_rotation:null,watermark:null,encrypted:null,completeness:'未核验',complete_pdf:false,recommendation:'待审',recommendation_reason:'尚未完成独立PDF质量核验',audit_evidence_paths:[],local_audit_file:null,source_ids:[],check_history:[],notes:[],...fields};links.set(linkId,l);}
  if(!l.standard_ids.includes(s.standard_id))l.standard_ids.push(s.standard_id);
  if(!s.link_ids.includes(linkId))s.link_ids.push(linkId);
  return l;
}

for(const r of seed.items){
  const p=identify(r['文件名']);const g=groupMap.get(Number(r['序号']));const sid=`S${String(r['序号']).padStart(3,'0')}`;
  const s=addStandard(p.id,{baseline:true,standard_number:p.published_code_candidate,name:p.name,year:p.year,version_stage:p.stage,edition_label:p.edition_label,topic_group:g?.id??null,topic_group_name:g?.name??'待分组'});
  s.baseline=true;s.seed_ids.push(sid);if(!s.original_names.includes(r['文件名']))s.original_names.push(r['文件名']);
  const eid=addEvidence({standard_id:s.standard_id,kind:'种子文件记录',statement_type:'原文事实',source_id:r.source_id,source_url:'https://knowledge.tjad.cloud/',observed_at:'2026-10-17',source_text:r['文件名'],claim:r['网页标注']?`原网页标注：${r['网页标注']}。尚未据此确认2026现行性。`:'文件存在于用户提供81条搜索结果中，不代表全国CECS全集',applicability:'来源目录记录'});s.metadata_evidence_ids.push(eid);
  if(!s.source_pages.includes('https://knowledge.tjad.cloud/'))s.source_pages.push('https://knowledge.tjad.cloud/');
  for(const issue of p.issues)if(!s.issues.includes(issue))s.issues.push(issue);
  if(r['网页标注']==='作废'||r['网页标注']==='废止')s.issues.push(`原网页标注${r['网页标注']}，待权威现行性核验`);
  const url=`https://knowledge.tjad.cloud${r['相对下载路径']}`;
  const l=addLink(s,url,{source_page:'https://knowledge.tjad.cloud/',source_kind:'用户目录候选',notes:['来源域名依据长截图文件名；协议及逐条下载尚未实测。根站本轮连接超时不代表逐条PDF永久失效。']});l.source_ids.push(r.source_id);
  original.push({seed_id:sid,standard_id:s.standard_id,original_name:r['文件名'],standard_number:p.published_code_candidate,number:p.number,year:p.year,year_text:p.year_text,edition_label:p.edition_label,draft_stage:p.stage,topic_group:g?.id??null,topic_group_name:g?.name??'待分组',source_id:r.source_id,source_annotation:r['网页标注'],relative_download_url:r['相对下载路径'],candidate_url:url,link_id:l.link_id,original_record:r,parsing_issues:p.issues});
}

// External evidence is imported without inventing legal status or PDF quality.
const receipts=[];
async function receipt(file){const j=await readJson(file);if(!j)return null;const raw=await fs.readFile(file,'utf8');receipts.push({path:path.relative(root,file).replace(/\\/g,'/'),sha256:sha(raw),imported_at:now});return j;}

const external = {search:[],directories:[],audit:[]};
let files=[];try{files=await fs.readdir(path.join(root,'search'));}catch{}
for(const name of files.filter(x=>/^candidates.*\.json$/i.test(x)).sort()){
  const j=await receipt(path.join(root,'search',name));
  for(const c of j?.candidates??[]){
    const p=identify(`${c.standard_number??''} ${c.name??''}`,c.year,c.draft_stage);
    const mapped=(c.seed_ids??[]).map(id=>original.find(x=>x.seed_id===id)?.standard_id).map(id=>standards.get(id)).find(x=>x);
    let s=(mapped?.standard_id===p.id?mapped:null)??addStandard(p.id,{standard_number:p.published_code_candidate,name:c.name??p.name,year:p.year,version_stage:p.stage});
    if(mapped&&mapped.standard_id!==p.id){s.issues.push(`候选${c.candidate_id}关联原记录${mapped.seed_ids.join(',')}，身份与原文件名不同，保留分列待核`);}
    if(c.name&&!s.name)s.name=c.name;
    if(c.topic_group){s.topic_group=c.topic_group;s.topic_group_name=groups.find(g=>g.id===c.topic_group)?.name??c.topic_group;}
    if(c.source_page&&!s.source_pages.includes(c.source_page))s.source_pages.push(c.source_page);
    const l=addLink(s,c.download_url,{source_page:c.source_page,source_kind:'公开检索候选',candidate_id:c.candidate_id,notes:[c.discovery_evidence??''].filter(Boolean)});if(l&&c.candidate_id)l.candidate_ids=[...(l.candidate_ids??[]),c.candidate_id];
    external.search.push(c);
    const discoveryId=addEvidence({standard_id:s.standard_id,kind:'检索发现',statement_type:'原文事实候选',source_id:c.candidate_id,source_url:c.source_page,source_text:c.discovery_evidence??'',claim:c.discovery_evidence??'公开候选尚待独立下载核验',observed_at:j.created_date??'2026-10-17'});s.metadata_evidence_ids.push(discoveryId);
    for(const e of c.metadata_evidence??[]){const eid=addEvidence({standard_id:s.standard_id,kind:'检索元数据证据',statement_type:'原文事实',...e});s.metadata_evidence_ids.push(eid);}
  }
}

// Institutional catalogues establish provenance and historical relationships only.
const directory=await receipt(path.join(root,'search/master-authority/authority-directory-records.json'));
for(const d of directory?.standards??[]){
  const p=identify(`${d.standard_number} ${d.name}`,d.year,d.draft_stage);
  const s=addStandard(p.id,{standard_number:d.standard_number,name:d.name,year:p.year,version_stage:p.stage,standard_family:d.standard_family});
  const eid=addEvidence({standard_id:s.standard_id,kind:d.historical_status?'历史目录':'官方实施清单',statement_type:'原文事实',source_id:d.source_id,source_url:d.source_url,source_page:d.source_page,source_text:d.raw_cells?.join(' / ')??'',claim:d.historical_status??d.status,observed_at:d.checked_at,applicability:d.historical_status?'仅证明2018年目录收录，不能证明2026现行性':'仅证明清单列明的实施日期，不单独证明当前未废止'});
  s.metadata_evidence_ids.push(eid);s.directory_memberships.push({source_id:d.source_id,evidence_id:eid,historical_status:d.historical_status??null,implementation_date_raw:d.implementation_date_raw});
  if(d.source_page&&!s.source_pages.includes(d.source_page))s.source_pages.push(d.source_page);
  const dm=String(d.implementation_date_raw??'').match(/^(\d{4})[年/.-](\d{1,2})[月/.-](\d{1,2})日?$/);
  if(dm){const val=`${dm[1]}-${dm[2].padStart(2,'0')}-${dm[3].padStart(2,'0')}`;if(s.effective_date&&s.effective_date!==val){s.issues.push(`实施日期冲突：${s.effective_date} / ${val}，来源${d.source_id}`);}else{s.effective_date=val;}}
  if(clean(d.replaces_raw)){
    s.replacement_relationships.push({kind:'历史目录载明替代',replaces_raw:d.replaces_raw,replaces:d.replaces||null,evidence_id:eid,source_id:d.source_id,applies_as_of:'2018-06-11'});
    // Only fully written years create a separate historical version. Raw two-digit years remain evidence.
    if(d.replaces&&/\d{4}$/.test(d.replaces)){const oldp=identify(d.replaces);const old=addStandard(oldp.id,{standard_number:d.replaces,name:'名称待核（历史替代关系中出现）',year:oldp.year,version_stage:oldp.stage});old.replacement_relationships.push({kind:'历史目录载明被替代',replaced_by:s.standard_id,evidence_id:eid,source_id:d.source_id,applies_as_of:'2018-06-11'});old.metadata_evidence_ids.push(eid);}
  }
  if(s.seed_ids.length&&s.issues.some(x=>/两位年份/.test(x))){s.issues=s.issues.filter(x=>!/两位年份/.test(x));s.metadata_evidence_ids.push(eid);}
  external.directories.push(d);
}

const auditInput=await receipt(path.join(root,'pdf-audit/audit-results.json'));
for(const a of auditInput?.results??[]){
  const p=identify(`${a.standard_number??''} ${a.name??''}`,a.year,a.draft_stage??(/征求意见/.test(a.version_match??'')?'征求意见稿':null));
  const existing=[...links.values()].find(l=>[l.requested_url,l.discovery_url,l.final_url].includes(a.requested_url??a.download_url));
  let ss=existing?.standard_ids.map(id=>standards.get(id)).filter(Boolean)??[];
  if(!ss.length)ss=[addStandard(p.id,{standard_number:p.published_code_candidate,name:a.name??p.name,year:p.year,version_stage:p.stage})];
  for(const s of ss){
    const l=addLink(s,a.requested_url??a.download_url,{source_page:a.source_page,source_kind:'独立审查公开候选'});
    if(!l)continue;
    const history=(a.audit_history??[]).map(h=>({...h,audit_id:a.audit_id}));
    Object.assign(l,{candidate_ids:[...new Set([...(l.candidate_ids??[]),a.candidate_id].filter(Boolean))],final_url:a.final_url??null,checked_at:a.visual_checked_at??a.checked_at,http_status:a.http_status??null,download_status:a.download_status,access_restriction:a.access_restriction??a.encryption_permissions??(a.http_status===200?'公开GET响应（本次）':'未证实'),url_expiry:a.url_expiry??'未声明；仅代表检查时可用',pdf_bytes:a.bytes??null,pages:a.pages??null,sha256:a.sha256??null,parse_ok:a.pdf_parse??null,version_match:a.version_match??null,version_verified:a.version_verified===true,text_layer:a.text_layer??null,search_copy:a.searchable??null,bookmarks:a.bookmark_count??null,bookmark_navigation:a.bookmark_navigation??null,clickable_toc:a.clickable_toc??null,clarity:a.clarity??null,page_order:a.page_order??null,cropping_rotation:JSON.stringify({rotation:a.rotation_summary,cropped:a.cropbox_diff_pages}),watermark:a.watermark??null,encrypted:a.encrypted??null,completeness:a.completeness??'未完成完整性核验',complete_pdf:a.complete_pdf===true&&a.version_verified===true,recommendation:a.recommendation??'待审',recommendation_reason:a.recommendation_reason??'',audit_evidence_paths:a.evidence_paths??[],local_audit_file:a.local_path??null,check_history:history,audit_id:a.audit_id,audit_result:a});
    if(a.error&&!l.notes.includes(a.error))l.notes.push(a.error);
    if(a.source_page&&!s.source_pages.includes(a.source_page))s.source_pages.push(a.source_page);
    const eid=addEvidence({standard_id:s.standard_id,kind:'独立PDF审查',statement_type:'原文事实（实测）',source_id:a.audit_id,source_url:a.final_url??a.requested_url??a.download_url,observed_at:a.checked_at,claim:a.completeness??a.download_status,evidence_paths:a.evidence_paths??[]});l.source_ids.push(eid);
  }
  external.audit.push(a);
}

// Explicit human maintenance is merged last; regeneration never loses these records.
const maintenance=await readJson(path.join(out,'maintenance-input.json'))??{schema_version:1,standards:[],links:[],note:'新增/更新/停用写入本文件；原始记录与证据永久保留。字段变更须注明reason/source_id。'};
if(!(await readJson(path.join(out,'maintenance-input.json'))))await fs.writeFile(path.join(out,'maintenance-input.json'),JSON.stringify(maintenance,null,2));
for(const [type,map] of [['standards',standards],['links',links]])for(const m of maintenance[type]??[]){const id=m.standard_id??m.link_id;let entry=map.get(id);if(!entry&&type==='standards'&&m.action==='新增')entry=addStandard(id,m.fields??{});if(!entry)throw new Error(`维护记录找不到${type}: ${id}`);if(!m.reason||!m.source_id)throw new Error(`维护记录须有reason与source_id: ${id}`);Object.assign(entry,m.fields??{});entry.active=m.action!=='停用';entry.maintenance_action=m.action;entry.maintenance_source={reason:m.reason,source_id:m.source_id,at:m.at??now};}
for(const s of standards.values()){
  s.metadata_evidence_ids=[...new Set(s.metadata_evidence_ids)];s.status_evidence_ids=[...new Set(s.status_evidence_ids)];s.issues=[...new Set(s.issues)];
  const ranked=s.link_ids.map(id=>links.get(id)).filter(l=>l.active&&l.complete_pdf).sort((a,b)=>({A:1,B:2,C:3,D:4}[a.recommendation]??9)-({A:1,B:2,C:3,D:4}[b.recommendation]??9)||(b.bookmarks??0)-(a.bookmarks??0));
  s.best_link_id=ranked[0]?.link_id??null;s.usable_alternative_count=Math.max(0,ranked.length-1);
  if(!s.link_ids.length)s.issues.push('尚未发现全文下载候选链接');
}

const model={schema_version:'1.1.0',generated_at:now,scope:{target:'全网现存CECS规范与历史版本，持续增补；本轮非穷尽性普查',baseline_definition:'用户提供结构专业知识库CECS搜索结果81条文件记录',baseline_records:81,baseline_distinct_filenames:77,baseline_source:seed.summary,coverage_denominator:'全国CECS全集总数未知，不用81或单站目录条数作为全国覆盖分母',groups,authority_directories:directory?.sources??[],directory_coverage:directory?.coverage??null},standards:[...standards.values()],links:[...links.values()],original_records:original,evidence,issues,external_inputs:receipts,external,coverage:{baseline_records_registered:original.length,baseline_standard_versions:[...standards.values()].filter(s=>s.baseline).length,registered_standard_versions:standards.size,registered_links:links.size,verified_complete_pdf_links:[...links.values()].filter(l=>l.complete_pdf).length,verified_complete_standard_versions:[...standards.values()].filter(s=>s.best_link_id).length,authority_records:directory?.standards?.length??0,independent_audit_results:external.audit.length,downloaded_parseable_pending:[...links.values()].filter(l=>l.pages&&!l.complete_pdf&&/可解析/.test(l.download_status)).length},change_log:[]};

for(const s of model.standards) for(const txt of s.issues) issues.push({issue_id:`I-${slug(s.standard_id+txt)}`,standard_id:s.standard_id,seed_ids:s.seed_ids,type:'识别或状态待核实',status:'待查',priority:'常规',action:txt,source_ids:s.metadata_evidence_ids});

const previous=await readJson(path.join(out,'cecs-master.json'));
const logPath=path.join(out,'change-log.jsonl');
const previousLinks=new Map((previous?.links??[]).map(l=>[l.link_id,l]));
for(const l of model.links){const old=previousLinks.get(l.link_id);if(old){l.discovered_at=old.discovered_at;l.check_history=[...new Map([...(old.check_history??[]),...l.check_history].map(h=>[sha(JSON.stringify(h)),h])).values()];}}
const previousStandards=new Map((previous?.standards??[]).map(s=>[s.standard_id,s]));
for(const s of model.standards){const old=previousStandards.get(s.standard_id);if(old)s.created_at=old.created_at;const a={...old},b={...s};for(const x of [a,b]){delete x.updated_at;delete x.created_at;delete x.maintenance_action;}if(!old||sha(JSON.stringify(a))!==sha(JSON.stringify(b))){model.change_log.push({change_id:`C-${slug(now+s.standard_id)}`,at:now,entity:'standard',id:s.standard_id,operation:old?'更新':'新增',reason:old?'合入新证据或链接':'首次登记',previous_fingerprint:old?sha(JSON.stringify(a)):null,current_fingerprint:sha(JSON.stringify(b))});s.maintenance_action=old?'更新':'新增';}else{s.updated_at=old.updated_at;s.maintenance_action=old.maintenance_action;}}
for(const l of model.links){const old=previousLinks.get(l.link_id);const stable=v=>{const n={...v};delete n.maintenance_action;return n;};const a=stable(old),b=stable(l);if(!old||sha(JSON.stringify(a))!==sha(JSON.stringify(b)))model.change_log.push({change_id:`C-${slug(now+l.link_id)}`,at:now,entity:'link',id:l.link_id,operation:old?'更新':'新增',reason:old?'合入独立下载/质量证据':'首次登记链接',previous_fingerprint:old?sha(JSON.stringify(a)):null,current_fingerprint:sha(JSON.stringify(b))});}
if(model.change_log.length)await fs.appendFile(logPath,model.change_log.map(x=>JSON.stringify(x)).join('\n')+'\n');
const allChanges=await fs.readFile(logPath,'utf8').catch(()=>'');model.change_log=allChanges.trim()?allChanges.trim().split('\n').map(x=>JSON.parse(x)):[];
await fs.writeFile(path.join(out,'seed-index.json'),JSON.stringify({schema_version:'1.0.0',generated_at:now,records:original.map(({original_record,...x})=>x),groups},null,2));
await fs.writeFile(path.join(out,'cecs-master.json'),JSON.stringify(model,null,2));
await fs.mkdir(path.join(out,'history'),{recursive:true});
await fs.writeFile(path.join(out,'history',`master-${now.replace(/[:.]/g,'-')}.json`),JSON.stringify(model,null,2));
console.log(JSON.stringify({mode:process.argv.includes('--index-only')?'index-only':'full',coverage:model.coverage,groups}));

if(process.argv.includes('--index-only')) process.exit(0);

// Workbook authoring is appended once search/audit imports are ready.
