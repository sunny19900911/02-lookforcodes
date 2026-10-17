import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {createAuditIdentity,updateAuditIdentity} from './audit-identity-core.mjs';
import {cleanSharingExternal} from './sharing-projection-core.mjs';

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
  const joint=text.match(/CECS\s*-\s*(CBIMU|CREA)\b/i)?.[1]?.toUpperCase();
  const family = joint?`CECS-${joint}`:'CECS';
  const parseText=text.replace(/CECS\s*-\s*(?:CBIMU|CREA)\b/i,'CECS');
  const codeMatch = parseText.match(/CECS(?:[\s_\-]*T)?[\s_\-]*(G\s*[:：]\s*[A-Z]\d+(?:-\d+)?|\d+|XXX)(?:\s*[:：\-]\s*|\s+)(19\d{2}|20\d{2}|\d{2}|202X)(?!\d)/i);
  const looseMatch = parseText.match(/CECS(?:[\s_\-]*T)?[\s_\-]*(G\s*[:：]\s*[A-Z]\d+(?:-\d+)?|\d+|XXX)(?!\d)/i);
  const m=codeMatch || looseMatch;
  const rawNumber = m?.[1]?.replace(/\s+/g,'').toUpperCase() ?? null;
  const number = /^\d+$/.test(rawNumber??'') ? String(Number(rawNumber)) : rawNumber;
  const yearText = explicitYear ? String(explicitYear) : codeMatch?.[2] ?? null;
  let year = yearText && /^(19|20)\d{2}$/.test(yearText) ? Number(yearText) : null;
  const issues=[];
  if(explicitYear&&codeMatch?.[2]&&String(explicitYear)!==codeMatch[2]&&codeMatch[2].length===4)issues.push(`字段年份${explicitYear}与编号内年份${codeMatch[2]}冲突，保留原始记录待核`);
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
  return {id:identity,number,raw_number:rawNumber,family,year,year_text:yearText,name,stage,edition_label:edition,published_code_candidate: `${family==='CECS'?prefix:`T/${family}`} ${number??'?'}${year?`-${year}`:''}`,issues};
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
const receiptCache=new Map();
async function receipt(file){if(receiptCache.has(file))return receiptCache.get(file);const j=await readJson(file);if(!j)return null;const raw=await fs.readFile(file,'utf8');receipts.push({path:path.relative(root,file).replace(/\\/g,'/'),sha256:sha(raw),imported_at:now});receiptCache.set(file,j);return j;}
const checkpoint=process.argv.includes('--checkpoint1330')?'1330':process.argv.includes('--checkpoint1320')?'1320':null;
const searchManifests=[];
if(checkpoint){searchManifests.push(await receipt(path.join(root,'search/freeze-inputs-1320.json')));if(checkpoint==='1330')searchManifests.push(await receipt(path.join(root,'search/freeze-inputs-1330.json')));}
const manifestEntries=new Map();for(const m of searchManifests)for(const e of m.files){if(manifestEntries.has(e.path)&&manifestEntries.get(e.path).sha256!==e.sha256)throw new Error(`Conflicting frozen source: ${e.path}`);manifestEntries.set(e.path,e);}
const searchManifest=checkpoint?{checkpoint,files:[...manifestEntries.values()],manifests:searchManifests,input_file_count:manifestEntries.size}:null;
if(searchManifest){for(const e of searchManifest.files){const bytes=await fs.readFile(path.join(root,e.path));if(bytes.length!==e.bytes||sha(bytes)!==e.sha256)throw new Error(`Frozen search input changed: ${e.path}`);if(!e.path.endsWith('.json'))receipts.push({path:e.path,sha256:e.sha256,imported_at:now,content_kind:'text reference; not a data row'});}}

const external = {search:[],directories:[],audit:[]};
async function candidateFiles(dir){const found=[];for(const d of await fs.readdir(dir,{withFileTypes:true})){if(d.isDirectory()&&d.name!=='master-authority')found.push(...await candidateFiles(path.join(dir,d.name)));else if(d.isFile()&&/candidates.*\.json$|.*candidates\.json$|^extension-preview-routes\.json$/i.test(d.name))found.push(path.join(dir,d.name));}return found;}
const selectedSearchFiles=searchManifest?searchManifest.files.filter(e=>e.path.endsWith('.json')).map(e=>path.join(root,e.path)):await candidateFiles(path.join(root,'search'));
for(const file of selectedSearchFiles.sort()){
  const j=await receipt(file);
  const rootMetadata=j?.standard_number&&j?.metadata_evidence?[{...j,candidate_id:`META-${slug(j.standard_number+(j.edition_note??''))}`,discovery_evidence:j.quality_boundary??j.permission}]:[];
  const supplemented=j?.supplement_only?external.search.find(x=>x.candidate_id===j.candidate_id):null;
  const supplements=supplemented?[{...supplemented,...j,alternative_urls:(j.historical_links??[]).flatMap(h=>[h.url,h.https_variant].filter(Boolean)),discovery_evidence:j.summary}]:[];
  for(const raw of [...rootMetadata,...(j?.candidates??[]),...(j?.draft_candidates??[]),...supplements,...(j?.metadata_only??[]).map(x=>({...x,candidate_id:`META-${slug(x.standard_number)}`,discovery_evidence:x.download_status??x.search_route_lead})),...(j?.no_direct_candidate??[]).map(x=>({...x,candidate_id:`LEAD-${slug(x.standard_number)}`,discovery_evidence:x.reference_limit,metadata_evidence:[{source_url:x.metadata_reference,claim:x.reference_limit}]}))]){
    const c={...raw,download_url:raw.download_url??raw.direct_url??null,source_page:raw.source_page??raw.detail_url??raw.metadata_reference??raw.direct_url??null,alternative_urls:raw.alternative_urls??raw.alternate_urls??raw.backup_urls??[],discovered_by_query:raw.discovered_by_query??raw.discovery_query??null,discovery_evidence:raw.discovery_evidence??[raw.version_candidate,raw.permission_observed,raw.english_name_from_source?`来源英文名：${raw.english_name_from_source}`:null,raw.next_check].filter(Boolean).join('；'),topic_group:raw.topic_group??(file.includes('g2-public-routes')?'G2':null)};
    const p=identify(`${c.standard_number??''} ${c.name??''} ${c.edition_note??c.edition_label??''}`,c.year,c.draft_stage);
    const mapped=(c.seed_ids??[]).map(id=>original.find(x=>x.seed_id===id)?.standard_id).map(id=>standards.get(id)).find(x=>x);
    let s=(mapped?.standard_id===p.id?mapped:null)??addStandard(p.id,{standard_number:p.published_code_candidate,name:c.name??(p.name||'中文名称待封面核准'),year:p.year,version_stage:p.stage,edition_label:p.edition_label});
    if(c.source_id==='CABP-BOOK-105427-20261017'){
      s.edition_note=c.edition_note;s.metadata_date_layers=[{context:'出版方网页字段原值',published_date:'2012-04-24',effective_date:'2012-04-24',withdrawn_label:'废止',withdrawal_date:null},{context:'试读书内施行日期（搜索解析，待直接核封面）',effective_date:'2003-03-01',edition_printing:'2012年7月第3版；2015年1月第11次印刷'}];
      s.issues.push('2012年版保持编号CECS102:2002；网页2012-04-24与书内2003-03-01日期分层保留，主实施日期暂不择值；网页废止日为空，不补猜');
      const old=standards.get('CECS-102-2002-FORMAL');if(old)old.issues.push('本条副本未核版次，不等于已确认2002初版；与2012年版未完成版次匹配，不共享链接或建立替代关系');
    }
    if(mapped&&mapped.standard_id!==p.id){s.issues.push(`候选${c.candidate_id}关联原记录${mapped.seed_ids.join(',')}，身份与原文件名不同，保留分列待核`);}
    if(c.name&&!s.name)s.name=c.name;
    if(c.topic_group){s.topic_group=c.topic_group;s.topic_group_name=groups.find(g=>g.id===c.topic_group)?.name??c.topic_group;}
    if(c.source_page&&!s.source_pages.includes(c.source_page))s.source_pages.push(c.source_page);
    for(const issue of p.issues)if(!s.issues.includes(issue))s.issues.push(issue);
    const l=addLink(s,c.download_url,{source_page:c.source_page,source_kind:'公开检索候选',candidate_id:c.candidate_id,notes:[c.discovery_evidence??''].filter(Boolean)});if(l&&c.candidate_id)l.candidate_ids=[...(l.candidate_ids??[]),c.candidate_id];
    if(l&&/\.zip(?:[?#]|$)/i.test(c.download_url??'')){l.source_kind='ZIP容器目标（内容未审）';l.download_status='ZIP目标未GET，包内内容未知；非PDF直链';l.notes.push('URL后缀为ZIP；不能按ZIP文件名认定包内文件格式、版本或完整性。');}
    for(const u of c.alternative_urls??[]){const alt=addLink(s,u,{source_page:c.source_page,source_kind:'公开检索备用候选',candidate_ids:[c.candidate_id],notes:[c.discovery_evidence??''].filter(Boolean)});}
    c._catalog_source={path:path.relative(root,file).replace(/\\/g,'/'),sha256:receipts.find(r=>r.path===path.relative(root,file).replace(/\\/g,'/'))?.sha256??null};
    external.search.push(c);
    const discoveryId=addEvidence({standard_id:s.standard_id,kind:'检索发现',statement_type:'原文事实候选',source_id:c.candidate_id,source_url:c.source_page,source_text:c.discovery_evidence??'',claim:c.discovery_evidence??'公开候选尚待独立下载核验',observed_at:j.created_date??'2026-10-17'});s.metadata_evidence_ids.push(discoveryId);
    for(const e of [...(c.metadata_evidence??[]),...(c.other_primary??[])]){const eid=addEvidence({standard_id:s.standard_id,kind:'检索元数据证据',statement_type:'原文事实',...e,source_url:e.source_url??e.url??c.source_page,claim:e.claim??e.evidence??e.note??e.kind??e.conclusion??''});s.metadata_evidence_ids.push(eid);}
  }
}

// Institutional catalogues establish provenance and historical relationships only.
const directory=await receipt(path.join(root,'search/master-authority/authority-directory-records.json'));
for(const d of directory?.standards??[]){
  const p=identify(`${d.standard_number} ${d.name}`,d.year,d.draft_stage);
  const s=addStandard(p.id,{standard_number:d.standard_number,name:d.name,year:p.year,version_stage:p.stage,standard_family:d.standard_family});
  for(const issue of p.issues)if(!s.issues.includes(issue))s.issues.push(issue);
  if(s.name&&d.name&&clean(s.name)!==clean(d.name)){s.name_variants=[...new Set([...(s.name_variants??[]),s.name,d.name])];s.issues.push(`同号年名称存在差异：${s.name} / ${d.name}，来源${d.source_id}`);}
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

const supplementalDirectory=checkpoint?await receipt(path.join(root,'search/baseline-external-routes/directory-round02.json')):null;
const unresolvedDrafts=[];
for(const d of supplementalDirectory?.records??[]){
  const p=identify(`${d.standard_number} ${d.name}`,d.year,d.draft_stage);
  const s=addStandard(p.id,{standard_number:d.standard_number,name:d.name,year:p.year,version_stage:p.stage,standard_family:d.standard_family});
  if(s.name!==d.name){s.name_variants=[...new Set([...(s.name_variants??[]),s.name,d.name])];s.issues.push(`目录题名差异：${s.name} / ${d.name} [${d.source_id}]`);}
  const eid=addEvidence({standard_id:s.standard_id,kind:'政府专题历史目录（非规范全文）',statement_type:d.evidence_type,source_id:d.source_id,source_url:d.source_pdf,source_page:d.source_page,source_date:d.source_publication_date,observed_at:d.checked_at,source_printed_page:d.source_printed_page,pdf_page_one_based:d.pdf_page_one_based,source_text:d.raw_cells.join(' / '),claim:`目录原题名：${d.name}；原号：${d.raw_standard_number}；日期格：${d.date_cell_raw??''}；表头：${d.date_cell_heading??''}；原状态：${d.historical_status_raw??''}`,applicability:'历史目录收录；日期格含义待核，不写入实施日期；不能确认2026现行性',raw_record:d});
  s.metadata_evidence_ids.push(eid);s.directory_memberships.push({source_id:d.source_id,evidence_id:eid,source_printed_page:d.source_printed_page,date_cell_raw:d.date_cell_raw,date_cell_heading:d.date_cell_heading});
  if(d.source_page&&!s.source_pages.includes(d.source_page))s.source_pages.push(d.source_page);
  for(const issue of p.issues)s.issues.push(issue);
  external.directories.push(d);
}
for(const d of supplementalDirectory?.draft_records??[]){
  const parent=supplementalDirectory.sources.find(s=>d.source_id.startsWith(s.source_id));const draft_id=`D-${slug(d.source_id+d.name)}`;
  const eid=addEvidence({standard_id:null,draft_id,kind:'无编号在编名称（非正式版本）',statement_type:'原文事实（历史目录）',source_id:d.source_id,source_url:d.source_pdf,source_page:parent?.source_page,source_date:d.source_publication_date,observed_at:supplementalDirectory.checked_at,source_printed_page:d.source_printed_page,claim:`${d.name}；${d.stage}；${d.status}`,applicability:'来源页与检查时间继承目录级字段；不补猜编号或确认2026阶段',raw_record:d});
  unresolvedDrafts.push({draft_id,...d,source_page:parent?.source_page,checked_at:supplementalDirectory.checked_at,evidence_id:eid,resolution:null});
  issues.push({issue_id:`I-${slug(draft_id)}`,standard_id:null,draft_id,name:d.name,seed_ids:[],type:'无编号在编名称（非正式版本）',status:'待查',priority:'常规',action:`${d.stage}；印刷页${d.source_printed_page}；无编号，不进入正式版本或完整PDF计数。${d.note}`,source_ids:[eid]});
}
for(const i of supplementalDirectory?.issues??[]){
  const sid=i.standard_number?identify(i.standard_number).id:null;
  const eid=addEvidence({standard_id:standards.has(sid)?sid:null,kind:'来源内部冲突或访问限制',statement_type:'原文事实',source_id:i.id,source_url:i.source_pdf??null,observed_at:supplementalDirectory.checked_at,claim:i.evidence,applicability:i.handling});
  issues.push({issue_id:`I-${slug(i.id)}`,standard_id:standards.has(sid)?sid:null,seed_ids:[],type:i.type,status:'待核',priority:'常规',action:`${i.evidence}\n${i.handling}`,source_ids:[eid]});
  if(standards.has(sid))standards.get(sid).issues.push(`${i.type}：${i.evidence} ${i.handling}`);
}

// Dated publication/withdrawal events remain distinct from a 2026 current-status claim.
const withdrawnSource=evidence.find(e=>e.source_id==='HNIS-CECS-2185-20241115');
if(withdrawnSource){
  for(const [sid,event] of [['CECS-22-2024-FORMAL','公告载明实施'],['CECS-22-2005-FORMAL','公告载明废止并被2024版替代']]){const s=standards.get(sid);if(!s)continue;s.status_events=[...(s.status_events??[]),{event,event_date:'2025-04-01',published_date:'2024-11-12',evidence_id:withdrawnSource.evidence_id,source_id:withdrawnSource.source_id,evidence_level:'省级标准化机构转载协会第2185号公告，协会原页待复核'}];s.status_evidence_ids.push(withdrawnSource.evidence_id);s.status_checked_at=now;s.replacement_relationships.push({kind:event,replaces:sid.includes('-2024-')?'CECS-22-2005-FORMAL':null,replaced_by:sid.includes('-2005-')?'CECS-22-2024-FORMAL':null,applies_as_of:'2025-04-01',evidence_id:withdrawnSource.evidence_id,evidence_level:'机构转载，2026当前现行性另核'});s.issues.push('第2185号转载公告所载2025-04-01废止/实施事件可见；2024版2026现行性与协会原公告仍待核');}
}

const auditInput=await receipt(path.join(root,'pdf-audit/audit-results.json'));
if(checkpoint){const auditFreeze=await receipt(path.join(root,`pdf-audit/freeze-${checkpoint}-receipt.json`));const actual=sha(await fs.readFile(path.join(root,'pdf-audit/audit-results.json')));if(actual!==auditFreeze.sha256||auditInput.results.length!==auditFreeze.result_count)throw new Error('Audit freeze changed before import');}
for(const a of auditInput?.results??[]){
  const p=identify(`${a.standard_number??''} ${a.name??''}`,a.year,a.draft_stage??(/征求意见/.test(a.version_match??'')?'征求意见稿':null));
  const existing=[...links.values()].find(l=>[l.requested_url,l.discovery_url,l.final_url].includes(a.requested_url??a.download_url));
  let ss=existing?.standard_ids.filter(id=>id===p.id).map(id=>standards.get(id)).filter(Boolean)??[];
  if(!ss.length)ss=[addStandard(p.id,createAuditIdentity(a,p))];
  for(const s of ss){
    updateAuditIdentity(s,a);
    const l=addLink(s,a.requested_url??a.download_url,{source_page:a.source_page,source_kind:'独立审查公开候选'});
    if(!l)continue;
    if(a.metadata_only){l.source_kind='公告/元数据文档（非标准全文）';l.metadata_only=true;}
    for(const issue of p.issues)if(!s.issues.includes(issue))s.issues.push(issue);
    const history=(a.audit_history??[]).map(h=>({...h,audit_id:a.audit_id}));
    l.verified_standard_ids=a.version_verified===true?[p.id]:[];
    Object.assign(l,{candidate_ids:[...new Set([...(l.candidate_ids??[]),a.candidate_id].filter(Boolean))],final_url:a.final_url??null,checked_at:a.visual_checked_at??a.checked_at,http_status:a.http_status??null,download_status:a.download_status,access_restriction:a.access_restriction??a.encryption_permissions??(a.http_status===200?'公开GET响应（本次）':'未证实'),url_expiry:a.url_expiry??'未声明；仅代表检查时可用',pdf_bytes:a.bytes??null,pages:a.pages??null,sha256:a.sha256??null,parse_ok:a.pdf_parse??null,version_match:a.version_match??null,version_verified:a.version_verified===true,text_layer:a.text_layer??null,search_copy:a.searchable??null,bookmarks:a.bookmark_count??null,bookmark_navigation:a.bookmark_navigation??null,clickable_toc:a.clickable_toc??null,clarity:a.clarity??null,page_order:a.page_order??null,cropping_rotation:JSON.stringify({rotation:a.rotation_summary,cropped:a.cropbox_diff_pages}),watermark:a.watermark??null,encrypted:a.encrypted??null,completeness:a.completeness??'未完成完整性核验',complete_pdf:a.complete_pdf===true&&a.version_verified===true,recommendation:a.recommendation??'待审',recommendation_reason:a.recommendation_reason??'',audit_evidence_paths:a.evidence_paths??[],local_audit_file:a.local_path??null,check_history:history,audit_id:a.audit_id,audit_result:a});
    if(a.error&&!l.notes.includes(a.error))l.notes.push(a.error);
    if(a.metadata_only)l.complete_pdf=false;
    if(a.source_page&&!s.source_pages.includes(a.source_page))s.source_pages.push(a.source_page);
    const eid=addEvidence({standard_id:s.standard_id,kind:'独立PDF审查',statement_type:'原文事实（实测）',source_id:a.audit_id,source_url:a.final_url??a.requested_url??a.download_url,observed_at:a.checked_at,claim:a.completeness??a.download_status,evidence_paths:a.evidence_paths??[]});l.source_ids.push(eid);
  }
  external.audit.push(a);
}

const conflict=await receipt(path.join(root,'search/conflict-796-years.json'));
if(conflict){for(const value of conflict.retained_values??[]){const p=identify(`${value} ${conflict.name}`);const s=addStandard(p.id,{standard_number:value,name:conflict.name,year:p.year});s.name=conflict.name;s.version_stage='正式性/年份冲突待核';s.identity_conflict_group=conflict.source_id;s.identity_confirmed=false;s.issues.push(conflict.status);for(const e of conflict.evidence??[]){const id=addEvidence({standard_id:s.standard_id,kind:'编号年份冲突',observed_at:conflict.checked_at,...e});s.metadata_evidence_ids.push(id);}s.issues.push(...(conflict.next_test??[]));}}
const conflictSupplement=checkpoint==='1330'?await receipt(path.join(root,'search/round05-796-conflict-supplement.json')):null;
if(conflictSupplement){for(const id of ['CECS-796-2020-FORMAL','CECS-796-2021-FORMAL']){const s=standards.get(id);if(!s)continue;const e=addEvidence({standard_id:id,kind:'796公告副本与出版年份冲突',statement_type:'原文事实（所见副本）',source_id:conflictSupplement.source_id,source_url:conflictSupplement.source_url,observed_at:conflictSupplement.source_checked_at,claim:JSON.stringify(conflictSupplement.metadata_claim),applicability:'第三方托管协会公告副本1页，非标准全文；不消除出版方2020与公告2021冲突',raw_record:conflictSupplement});s.metadata_evidence_ids.push(e);s.metadata_date_layers=[...(s.metadata_date_layers??[]),{context:'第757号公告副本所载日期（非对身份冲突的裁决）',...conflictSupplement.metadata_claim}];s.issues.push(conflictSupplement.status);}}

// Explicit human maintenance is merged last; regeneration never loses these records.
const maintenance=await readJson(path.join(out,'maintenance-input.json'))??{schema_version:1,standards:[],links:[],note:'新增/更新/停用写入本文件；原始记录与证据永久保留。字段变更须注明reason/source_id。'};
if(!(await readJson(path.join(out,'maintenance-input.json'))))await fs.writeFile(path.join(out,'maintenance-input.json'),JSON.stringify(maintenance,null,2));
for(const [type,map] of [['standards',standards],['links',links]])for(const m of maintenance[type]??[]){const id=m.standard_id??m.link_id;let entry=map.get(id);if(!entry&&type==='standards'&&m.action==='新增')entry=addStandard(id,m.fields??{});if(!entry)throw new Error(`维护记录找不到${type}: ${id}`);if(!m.reason||!m.source_id)throw new Error(`维护记录须有reason与source_id: ${id}`);Object.assign(entry,m.fields??{});entry.active=m.action!=='停用';entry.maintenance_action=m.action;entry.maintenance_source={reason:m.reason,source_id:m.source_id,at:m.at??now};}
for(const s of standards.values()){
  s.metadata_evidence_ids=[...new Set(s.metadata_evidence_ids)];s.status_evidence_ids=[...new Set(s.status_evidence_ids)];s.issues=[...new Set(s.issues)];
  const ranked=s.link_ids.map(id=>links.get(id)).filter(l=>l.active&&l.complete_pdf&&l.verified_standard_ids?.includes(s.standard_id)).sort((a,b)=>({A:1,B:2,C:3,D:4}[a.recommendation]??9)-({A:1,B:2,C:3,D:4}[b.recommendation]??9)||(b.bookmarks??0)-(a.bookmarks??0));
  s.best_link_id=ranked[0]?.link_id??null;s.usable_alternative_count=Math.max(0,ranked.length-1);
  if(!s.link_ids.length)s.issues.push('尚未发现全文下载候选链接');
}

const model={schema_version:'1.1.0',generated_at:now,scope:{target:'全网现存CECS规范与历史版本，持续增补；本轮非穷尽性普查',baseline_definition:'用户提供结构专业知识库CECS搜索结果81条文件记录',baseline_records:81,baseline_distinct_filenames:77,baseline_source:seed.summary,coverage_denominator:'全国CECS全集总数未知，不用81或单站目录条数作为全国覆盖分母',groups,authority_directories:directory?.sources??[],directory_coverage:directory?.coverage??null},standards:[...standards.values()],links:[...links.values()],original_records:original,evidence,issues,external_inputs:receipts,external,coverage:{baseline_records_registered:original.length,baseline_standard_versions:[...standards.values()].filter(s=>s.baseline).length,registered_standard_versions:standards.size,registered_links:links.size,verified_complete_pdf_links:[...links.values()].filter(l=>l.complete_pdf).length,verified_complete_standard_versions:[...standards.values()].filter(s=>s.best_link_id).length,authority_records:directory?.standards?.length??0,independent_audit_results:external.audit.length,downloaded_parseable_pending:[...links.values()].filter(l=>l.pages&&!l.complete_pdf&&/可解析/.test(l.download_status)).length},change_log:[]};
model.coverage.verified_complete_unique_sha256=new Set(model.links.filter(l=>l.complete_pdf&&l.sha256).map(l=>l.sha256)).size;
model.unresolved_drafts=unresolvedDrafts;
model.coverage.unresolved_unnumbered_drafts=unresolvedDrafts.length;
model.coverage.supplemental_directory_records=supplementalDirectory?.records?.length??0;
model.coverage.authority_records+=(supplementalDirectory?.records?.length??0);
model.scope.authority_directories.push(...(supplementalDirectory?.sources??[]));
model.scope.directory_coverage={...model.scope.directory_coverage,supplemental:supplementalDirectory?.coverage??null};
model.scope.checkpoint=checkpoint;
model.scope.directory_unique_number_year_count=new Set(external.directories.map(d=>identify(d.standard_number,d.year).id)).size;
model.external.search_manifest=searchManifest;
model.external.search_manifests=searchManifests;
model.external.conflict_796_supplement=conflictSupplement;
if(checkpoint==='1330')model.external.completeness_feedback=await receipt(path.join(root,'search/round06-22-completeness-receipt.json'));
model.external.directory_supplement=supplementalDirectory;
model.external.search_coverage=checkpoint?await receipt(path.join(root,'search/g1-round03-coverage.json')):null;

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
const sharingChanges=cleanSharingExternal(model.external);
if(sharingChanges.length)model.external.sharing_projection={version:1,created_at:now,changed_paths:sharingChanges.map(c=>c.path),policy:'Transient query values removed; original frozen source remains local and is identified by source hash.'};
await fs.writeFile(path.join(out,'cecs-master.json'),JSON.stringify(model,null,2));
await fs.mkdir(path.join(out,'history'),{recursive:true});
await fs.writeFile(path.join(out,'history',`master-${now.replace(/[:.]/g,'-')}.json`),JSON.stringify(model,null,2));
console.log(JSON.stringify({mode:process.argv.includes('--index-only')?'index-only':'full',coverage:model.coverage,groups}));

if(process.argv.includes('--index-only')) process.exit(0);

const {Workbook,SpreadsheetFile}=await import('@oai/artifact-tool');
const workbook=Workbook.create();
const previewDir=path.join(out,'previews');await fs.mkdir(previewDir,{recursive:true});
const col=n=>{let s='';for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const cellText=v=>v===null||v===undefined?'':v instanceof Date?v:Array.isArray(v)?v.join('\n'):typeof v==='object'?JSON.stringify(v):v;
const dateValue=v=>v&&/^\d{4}-\d{2}-\d{2}$/.test(v)?new Date(`${v}T00:00:00Z`):v??'';
const stamp=v=>v?new Date(new Date(v).getTime()+8*3600000):'';
const full=model.links.filter(l=>l.complete_pdf&&l.active);
const sorted=[...model.standards].sort((a,b)=>Number(b.baseline)-Number(a.baseline)||a.standard_number?.localeCompare(b.standard_number??'','en',{numeric:true})||a.standard_id.localeCompare(b.standard_id));
const mapLinks=new Map(model.links.map(l=>[l.link_id,l]));
const pdfState=s=>{if(s.best_link_id)return '已验完整PDF';const ls=s.link_ids.map(id=>mapLinks.get(id));return ls.find(l=>l.pages&&/可解析/.test(l.download_status))?.download_status??(ls.length?ls.find(l=>l.checked_at)?.download_status??'候选未实测':'尚无下载候选');};
const standardRows=sorted.map(s=>[s.standard_number,`${s.name}${s.edition_label?`（${s.edition_label}）`:''}`,mapLinks.get(s.best_link_id)?.final_url??'',pdfState(s),s.current_status,s.version_stage,s.year,s.baseline?'基线':'新增',s.topic_group_name??'待分组',s.scope,s.standard_type,dateValue(s.effective_date),dateValue(s.published_date),s.status_checked_at?stamp(s.status_checked_at):'',s.source_pages[0]??'',s.usable_alternative_count,s.standard_id,s.issues.join('\n'),s.seed_ids.join(', '),s.link_ids.length,s.replacement_relationships.map(r=>`${r.kind}: ${r.replaces_raw??r.replaces??r.replaced_by??''}${r.applies_as_of?`；日期${r.applies_as_of}`:''}${r.evidence_level?`；${r.evidence_level}`:''} [${r.evidence_id}]`).join('\n'),s.status_evidence_ids.join(', '),s.name_variants?.join('\n')??'']);
const configs=[];
const nativeHyperlinks=[];
function makeSheet(name,title,headers,rows,{widths={},urls=[],dates=[],times=[],rowHeight=48,primary=false}={}){
  const sheet=workbook.worksheets.add(name);sheet.showGridLines=false;if(primary)sheet.tabColor='#253858';
  const end=Math.max(9,rows.length+8),last=col(headers.length-1);
  const used=sheet.getRange(`A1:${last}${end}`);used.format.font={name:'Arial',size:10,color:'#243247'};used.format.verticalAlignment='center';used.format.rowHeight=rowHeight;used.format.columnWidth=22;
  sheet.getRange('A2').values=[[title]];sheet.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:'#172B4D'};
  sheet.getRange(`A3:${col(Math.min(headers.length-1,7))}3`).format.borders={bottom:{style:'thin',color:'#7E94B2'}};
  sheet.getRange('A4:B4').values=[[stamp(now),stamp(now)]];sheet.getRange('A4').setNumberFormat('yyyy-mm-dd');sheet.getRange('B4').setNumberFormat('hh:mm" 北京"');
  sheet.getRange('A5').values=[['记录数']];sheet.getRange('B5').values=[[rows.length]];sheet.getRange('A5:B5').format.rowHeight=22;
  sheet.getRange(`A8:${last}8`).values=[headers];sheet.getRange(`A8:${last}8`).format={fill:'#253858',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},horizontalAlignment:'center',verticalAlignment:'center',wrapText:true,rowHeight:34};
  if(rows.length){sheet.getRange(`A9:${last}${rows.length+8}`).values=rows.map(r=>r.map(cellText));const t=sheet.tables.add(`A8:${last}${rows.length+8}`,true,`CECS${configs.length+1}`);t.showFilterButton=true;t.style='TableStyleLight9';}
  else{sheet.getRange('A9').values=[['本轮尚无满足版本与完整性双重核验的记录']];sheet.getRange('A9:H9').format.rowHeight=36;}
  sheet.freezePanes.freezeRows(8);sheet.freezePanes.freezeColumns(Math.min(2,headers.length));
  for(let i=0;i<headers.length;i++){sheet.getRange(`${col(i)}1:${col(i)}${end}`).format.columnWidth=widths[i]??22;}
  sheet.getRange(`A1:${last}1`).format.rowHeight=10;sheet.getRange(`A2:${last}2`).format.rowHeight=30;sheet.getRange(`A3:${last}3`).format.rowHeight=8;sheet.getRange(`A4:${last}5`).format.rowHeight=23;sheet.getRange(`A6:${last}7`).format.rowHeight=8;
  if(rows.length){sheet.getRange(`A9:${last}${end}`).format.wrapText=true;for(const c of urls){for(let r=0;r<rows.length;r++){const value=rows[r][c];if(typeof value==='string'&&/^https?:\/\//.test(value)){sheet.getRange(`${col(c)}${r+9}`).values=[['打开链接']];nativeHyperlinks.push({sheet:configs.length+1,cell:`${col(c)}${r+9}`,url:value});}}sheet.getRange(`${col(c)}9:${col(c)}${end}`).format.font.color='#1D57A0';}
  for(const c of dates)sheet.getRange(`${col(c)}9:${col(c)}${end}`).setNumberFormat('yyyy-mm-dd');for(const c of times)sheet.getRange(`${col(c)}9:${col(c)}${end}`).setNumberFormat('yyyy-mm-dd hh:mm');}
  configs.push({sheet,name,headers,rows,end,last});return sheet;
}
const main=makeSheet('规范总表','CECS 规范与下载总表', ['规范编号','规范名称','最佳PDF','PDF核验状态','2026现行性','稿型','年份','基线/新增','专业分组','适用范围','标准类型','实施日期','发布日期','现行性核验日期','来源详情页','有效备用数','稳定ID','待查问题','原记录映射','候选链接数','历史替代关系','状态证据ID','名称差异'],standardRows,{primary:true,urls:[2,14],dates:[11,12],times:[13],widths:{0:27,1:54,2:16,3:39,4:18,5:22,6:10,7:12,8:29,9:26,10:48,11:15,12:15,13:24,14:16,15:14,16:53,17:100,18:22,19:16,20:90,21:30,22:70},rowHeight:56});
main.getRange('D4').values=[['已验完整PDF链接']];main.getRange('E4').values=[[full.length]];main.getRange('D5').values=[['81条基线登记']];main.getRange('E5').values=[[model.coverage.baseline_records_registered]];main.getRange('G4').values=[['全集分母未知']];main.getRange('I4').values=[['历史目录不证明2026现行性']];
const completeRows=full.map(l=>[l.verified_standard_ids.map(id=>standards.get(id)?.standard_number).join(', '),l.verified_standard_ids.map(id=>standards.get(id)?.name).join(', '),l.final_url,l.recommendation,l.recommendation_reason,l.pages,l.pdf_bytes===null?null:l.pdf_bytes/1048576,l.search_copy,l.bookmarks,l.bookmark_navigation,l.clickable_toc,l.clarity,l.completeness,stamp(l.checked_at),l.source_page,l.link_id,l.sha256,l.local_audit_file,l.standard_ids.join(', ')]);
makeSheet('已验完整PDF','已确认版本与完整性的 PDF', ['规范编号','规范名称','最终PDF链接','推荐等级','推荐理由','页数','大小（MiB）','正文搜索复制','原生书签数','书签跳转','可点击目录','清晰度','完整性证据','核验时间','来源详情页','链接ID','SHA256','本地核验路径','关联版本ID'],completeRows,{primary:true,urls:[2,14],times:[13],widths:{0:27,1:54,2:18,3:14,4:100,5:10,6:16,7:90,8:14,9:50,10:85,11:90,12:110,13:24,14:18,15:28,16:70,17:100,18:55},rowHeight:88});
const linkRows=model.links.map(l=>[l.link_id,l.standard_ids.join('\n'),l.candidate_ids?.join(', ')??l.candidate_id??'',l.source_page,l.requested_url,l.final_url,l.download_status,cellText(l.access_restriction),l.url_expiry,stamp(l.checked_at),l.http_status,l.pages,l.pdf_bytes,l.pdf_bytes===null?null:l.pdf_bytes/1048576,l.sha256,cellText(l.parse_ok),l.version_match,l.version_verified===true?'已确认':'未确认',l.complete_pdf?'已验完整':'待核/不完整',l.completeness,l.recommendation,l.recommendation_reason,cellText(l.text_layer),l.search_copy,l.bookmarks,l.bookmark_navigation,l.clickable_toc,l.clarity,l.page_order,l.cropping_rotation,l.watermark,cellText(l.encrypted),l.audit_evidence_paths.join('\n'),l.local_audit_file,l.check_history.map(h=>`${h.checked_at} ${h.outcome}`).join('\n'),l.notes.join('\n'),l.active?'保留':'停用',l.verified_standard_ids?.join(', ')??'',l.requested_url,l.final_url]);
makeSheet('链接明细','全部候选与实际核验链接', ['链接ID','关联版本ID','候选ID','来源详情页','请求链接','最终链接','下载状态','权限状态','过期情况','核验时间','HTTP状态','页数','文件字节数','大小（MiB）','SHA256','解析结果','版本匹配证据','版本确认','完整性状态','完整性证据','推荐等级','推荐理由','文本层存在','正文搜索复制','原生书签数','书签跳转','目录点击','清晰度','页序','裁边与旋转','水印','加密','核验证据路径','本地核验文件','逐次检查历史','问题备注','维护状态','已确认适用版本','请求URL原文','最终URL原文'],linkRows,{urls:[3,4,5],times:[9],widths:{0:28,1:55,2:30,3:18,4:18,5:18,6:40,7:48,8:44,9:24,10:13,11:10,12:19,13:16,14:70,15:44,16:90,17:15,18:18,19:125,20:13,21:110,22:16,23:110,24:15,25:65,26:100,27:110,28:70,29:70,30:65,31:12,32:130,33:130,34:130,35:110,36:12,37:55,38:170,39:170},rowHeight:96});
const seedRows=original.map(r=>[r.seed_id,r.standard_id,r.original_name,r.standard_number,r.year,r.draft_stage,r.topic_group_name,r.source_annotation,r.source_id,r.candidate_url,r.link_id,r.parsing_issues.join('\n')]);
makeSheet('原始映射','81 条原始记录的不可丢失映射', ['原记录ID','规范稳定ID','原始文件名','解析编号','解析年份','稿型','专业分组','原网页标注','原始source_id','候选下载链接','链接ID','识别问题'],seedRows,{urls:[9],widths:{0:14,1:55,2:100,3:27,4:14,5:22,6:30,7:20,8:75,9:18,10:28,11:90},rowHeight:56});
const issueRows=issues.map(i=>[i.issue_id,i.standard_id??i.draft_id??'',standards.get(i.standard_id)?.standard_number??'',standards.get(i.standard_id)?.name??i.name??'',i.seed_ids.join(', '),i.type,i.status,i.priority,i.action,i.source_ids.join(', ')]);
makeSheet('待查与问题','缺全文与元数据冲突队列', ['问题ID','规范稳定ID','规范编号','规范名称','原记录ID','问题类别','处理状态','优先级','待查动作','证据ID'],issueRows,{widths:{0:28,1:55,2:27,3:54,4:22,5:30,6:14,7:14,8:140,9:100},rowHeight:58});
const evidenceRows=evidence.map(e=>[e.evidence_id,e.standard_id,e.kind,e.statement_type,e.source_id,e.source_url,e.source_page??'',e.observed_at??'',e.source_text??'',e.claim??'',e.applicability??'',e.evidence_paths?.join('\n')??'']);
makeSheet('状态与来源依据','状态、目录与独立审查证据', ['证据ID','规范稳定ID','证据种类','陈述类型','source_id','来源URL','来源详情页','来源记录或检查时间','原文摘录/原始行','证据说明','适用日期与限制','核验证据路径'],evidenceRows,{urls:[5,6],widths:{0:28,1:55,2:28,3:32,4:75,5:18,6:18,7:35,8:125,9:130,10:110,11:130},rowHeight:78});
const queryMap=new Map();for(const c of external.search){const key=c.candidate_id??c.download_url??c.source_page;const old=queryMap.get(key)??{};queryMap.set(key,{...old,...c});}
const queryRows=[...queryMap.values()].map(c=>[c.candidate_id,c.topic_group,c.standard_number,c.name,c.discovered_by_query,c.source_page,c.download_url,c.alternative_urls?.join('\n')??'',c.discovery_evidence,c.seed_ids?.join(', ')??'',c.checked_at??'2026-10-17',model.links.filter(l=>l.candidate_ids?.includes(c.candidate_id)&&l.complete_pdf).length]);
for(const batch of model.external.search_coverage?.query_rounds??[])for(const [i,q] of batch.queries.entries())queryRows.push([`QUERY-${checkpoint}-${batch.round}-${i+1}`,'G1','','实际查询',q,'','','','G1逐项覆盖；本批0新增直链','','2026-10-17',0]);
for(const c of model.external.search_coverage?.coverage??[])queryRows.push([`COVER-${checkpoint}-${slug(c.standard_number)}`,'G1',c.standard_number,c.name,'逐项覆盖；实际查询词见QUERY行',c.sources?.[0]??'','','',`${c.status}；下一试验：${c.next_test??''}`,c.seed_ids?.join(', ')??'','2026-10-17',0]);
makeSheet('检索记录','实际发现路线与待审候选', ['候选ID','分组','规范编号','规范名称','实际查询词','来源页','主候选URL','备用候选URL原文','发现证据与限制','原记录线索','发现/补查时间','已验完整链接数'],queryRows,{urls:[5,6],widths:{0:28,1:12,2:28,3:58,4:105,5:18,6:18,7:170,8:140,9:22,10:32,11:20},rowHeight:100});
const notes=[['范围','全网可发现的CECS编号与历史版本，持续增补；本次不宣称穷尽全网。'],['版本数量',model.coverage.registered_standard_versions],['原记录登记',model.coverage.baseline_records_registered],['目录原始行',model.coverage.authority_records],['目录不同标准号',directory?.coverage?.unique_number_year_count??650],['目录来源数',directory?.sources?.length??0],['下载链接数',model.coverage.registered_links],['独立审查结果数',model.coverage.independent_audit_results],['已验完整PDF链接数',model.coverage.verified_complete_pdf_links],['已验完整规范版本数',model.coverage.verified_complete_standard_versions],['可解析但完整性待核链接',model.coverage.downloaded_parseable_pending],['现行性','以来源证据为准。2018机构有效目录只证明历史收录，2025–2026月度实施清单只证明所列实施日期，均不能单独证明2026-10-17现行性。'],['标准范围','CECS协会或团体标准，不因来源网站所在地归为当地地方标准。T/CECS-CBIMU联合编号独立登记。'],['完整PDF门槛','独立审查必须同时显式确认version_verified与complete_pdf；HTTP200、PDF后缀、页数多和文本层布尔值均不能单独证明完整。'],['推荐等级A',auditInput?.rating_rules?.A??'版本和完整性确认，清晰可搜索且原生书签/目录导航良好。以独立审查理由为准。'],['推荐等级B',auditInput?.rating_rules?.B??'版本和完整性确认可读，文本层或原生导航存在不足。'],['推荐等级C',auditInput?.rating_rules?.C??'已下载解析，但版本/完整性未闭环；不进入完整PDF清单。'],['推荐等级D',auditInput?.rating_rules?.D??'仅预览/封面、非PDF、版本不符、受限或本次网络失败；不得当完整全文推荐。'],['书签与目录','原生书签、可点击目录分别实查。无原生书签不代表PDF不完整，少量网页文字不代表正文可搜索。'],['链接维护','保存请求URL、重定向最终URL及全部有效备用；链接只代表核验时情况，过期与权限变化须复查。'],['人工增删','通过maintenance-input.json登记新增、更新或停用，填写reason/source_id。停用不抹去原记录和历史证据。'],['文件与历史','本地核验文件仅辅助；PDF原件和截图不进入GitHub。主索引、变更日志和不可变快照用于追溯。'],['待核身份','737缺年份仍为YEAR-UNKNOWN；796的2020与2021证据冲突保持分列，草案与正式版分别登记。']];
notes.splice(10,0,['已验完整PDF不同SHA256文件数',model.coverage.verified_complete_unique_sha256]);
notes.find(r=>r[0]==='目录不同标准号')[1]=model.scope.directory_unique_number_year_count;
notes.find(r=>r[0]==='目录来源数')[1]=model.scope.authority_directories.length;
notes.push(['无编号在编名称',unresolvedDrafts.length],['混合日期格','湖北49行表头为实施日期/任务下达日期，仅保留原始格，不写入实施日期。'],['省略空白页口径','有同版或可信页面证据证明省略的是装帧空白、且全部内容闭合，才可按审查升B并注明；未证明仍C。'],['联合编号','T/CECS-CBIMU与T/CECS-CREA各自为独立编号族，不与普通CECS同数字号合并。']);
notes.push(['链接与文件分别计数','相同SHA256的主链与备用链分别保留为下载链接，只计一份不同文件；规范版本按稳定ID分别计数。']);
if(checkpoint==='1330')notes.push(['102版次','CECS102:2002（2012年版）单列E2012身份，编号年份仍为2002；无版次副本不被假定为初版，两者未完成版次匹配不共享下载链接。'],['公告与全文','33条实GET审查中包含1条796发布公告元数据；仅1页公告不计完整标准，年份冲突仍保留。']);
makeSheet('说明与覆盖','覆盖范围与维护口径', ['项目','内容'],notes,{widths:{0:40,1:145},rowHeight:60});
makeSheet('变更记录','追加保存的规范与链接变更', ['变更ID','变更时间','实体','稳定ID','操作','原因','原指纹','现指纹'],model.change_log.map(c=>[c.change_id,stamp(c.at),c.entity,c.id,c.operation,c.reason,c.previous_fingerprint,c.current_fingerprint]),{times:[1],widths:{0:28,1:24,2:16,3:55,4:14,5:65,6:72,7:72},rowHeight:32});
workbook.recalculate();
const inspections=[];
for(const c of configs){const r=await workbook.inspect({kind:'table',range:`'${c.name}'!A8:${col(Math.min(7,c.headers.length-1))}${Math.min(c.end,12)}`,include:'values,formulas',tableMaxRows:5,tableMaxCols:8,maxChars:2500});inspections.push({sheet:c.name,inspection:r.ndjson});}
const errors=await workbook.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:100},summary:'final formula error scan',maxChars:6000});
await fs.writeFile(path.join(out,'workbook-inspection.json'),JSON.stringify({generated_at:now,inspections,errors:errors.ndjson},null,2));
for(const c of configs){const lastCol=Math.min(c.headers.length-1,c.name==='说明与覆盖'?1:3);const image=await workbook.render({sheetName:c.name,range:`A1:${col(lastCol)}${Math.min(c.end,12)}`,scale:1.4,format:'png'});await fs.writeFile(path.join(previewDir,`${c.name}.png`),new Uint8Array(await image.arrayBuffer()));}
const file=await SpreadsheetFile.exportXlsx(workbook);await file.save(path.join(out,'CECS可下载PDF总表.xlsx'));
await fs.writeFile(path.join(out,'native-hyperlinks.json'),JSON.stringify(nativeHyperlinks));
const {execFileSync}=await import('node:child_process');execFileSync('C:/Users/mj528/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',[path.join(out,'patch-hyperlinks.py'),path.join(out,'CECS可下载PDF总表.xlsx'),path.join(out,'native-hyperlinks.json')],{stdio:'inherit'});
await fs.writeFile(path.join(out,'workbook-build-receipt.json'),JSON.stringify({generated_at:now,path:'catalog/CECS可下载PDF总表.xlsx',sheets:configs.map(c=>({name:c.name,records:c.rows.length,columns:c.headers.length})),coverage:model.coverage,formula_errors:errors.ndjson,authoring_library:'@oai/artifact-tool',visual_review:'预览已生成，须人工目视确认'},null,2));
console.log(JSON.stringify({xlsx:path.join(out,'CECS可下载PDF总表.xlsx'),sheets:configs.length,errors:errors.ndjson}));
