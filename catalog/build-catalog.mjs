import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {createAuditIdentity,updateAuditIdentity,auditCompletenessFields,matchUnnumberedAuditCandidate} from './audit-identity-core.mjs';
import {cleanSharingExternal} from './sharing-projection-core.mjs';
import {inferVersionStage} from './version-stage-core.mjs';
import {applyDownloadSourceRegions} from './download-source-regions.mjs';

const root = path.resolve(import.meta.dirname, '..');
const out = import.meta.dirname;
const seedPath = path.resolve(root, '../cecs-catalog-20261017/CECS目录与下载路径.json');
const now = new Date().toISOString();
const sha = s => crypto.createHash('sha256').update(s).digest('hex');
const clean = s => String(s ?? '').normalize('NFKC').trim();
const slug = s => sha(String(s??'')).slice(0,12);
const readJson = async p => { try{return JSON.parse((await fs.readFile(p,'utf8')).replace(/^\uFEFF/,''));}catch(e){if(e.code==='ENOENT') return null; throw e;} };
await fs.mkdir(out,{recursive:true});

function identify(raw, explicitYear=null, explicitStage=null, versionClass=null) {
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
  const stage=inferVersionStage({text,explicitStage,versionClass});
  const edition=(text.match(/(?:19|20)\d{2}年版/)?.[0]??null);
  const editionYear=edition?Number(edition.slice(0,4)):null;
  const identity=number && number!=='XXX'?`${family}-${number.replace(/[:]/g,'_')}-${year??'YEAR-UNKNOWN'}-${stage==='报批稿'?'APPROVAL-DRAFT':stage==='送审稿'?'REVIEW-DRAFT':stage==='征求意见稿'?'CONSULT-DRAFT':stage==='草案（阶段待核）'?'DRAFT-STAGE-UNKNOWN':'FORMAL'}${editionYear?`-E${editionYear}`:''}`:`CECS-UNRESOLVED-${slug(text)}`;
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
const checkpoint=process.argv.includes('--checkpoint1510')?'1510':process.argv.includes('--checkpoint1410')?'1410':process.argv.includes('--checkpoint1350')?'1350':process.argv.includes('--checkpoint1330')?'1330':process.argv.includes('--checkpoint1320')?'1320':null;
const has1410=['1410','1510'].includes(checkpoint),has1350=['1350','1410','1510'].includes(checkpoint),has1330=['1330','1350','1410','1510'].includes(checkpoint);
const searchManifests=[];
if(checkpoint){searchManifests.push(await receipt(path.join(root,'search/freeze-inputs-1320.json')));if(has1330)searchManifests.push(await receipt(path.join(root,'search/freeze-inputs-1330.json')));}
if(has1350)for(const name of ['freeze-inputs-1340.json','freeze-inputs-1340-water-mep-addendum-v2.json','freeze-inputs-g2-round02-share-1350.json'])searchManifests.push(await receipt(path.join(root,'search',name)));
if(has1410)for(const name of ['freeze-inputs-1400.json','master-authority/freeze-ttbz-p1-1410.json'])searchManifests.push(await receipt(path.join(root,'search',name)));
if(checkpoint==='1510')for(const name of ['freeze-inputs-1420.json','freeze-inputs-1430.json','freeze-inputs-1440.json'])searchManifests.push(await receipt(path.join(root,'search',name)));
const manifestEntries=new Map();for(const m of searchManifests)for(const e of m.files){if(manifestEntries.has(e.path)&&manifestEntries.get(e.path).sha256!==e.sha256)throw new Error(`Conflicting frozen source: ${e.path}`);manifestEntries.set(e.path,e);}
// Select the reviewed sharing projection before reading any legacy raw candidate.
if(has1350)manifestEntries.delete('search/g2-public-routes/round02-candidates.json');
const searchManifest=checkpoint?{checkpoint,files:[...manifestEntries.values()],manifests:searchManifests,input_file_count:manifestEntries.size}:null;
if(searchManifest){for(const e of searchManifest.files){const bytes=await fs.readFile(path.join(root,e.path));if(bytes.length!==e.bytes||sha(bytes)!==e.sha256)throw new Error(`Frozen search input changed: ${e.path}`);if(!e.path.endsWith('.json'))receipts.push({path:e.path,sha256:e.sha256,imported_at:now,content_kind:'text reference; not a data row'});}}

const external = {search:[],directories:[],audit:[]};
function metadataExtras(j){
  const rows=value=>Array.isArray(value)?value:[];
  const nonpdf=rows(j.non_pdf_metadata_routes).map(x=>({...x,candidate_id:x.route_id??`META-NONPDF-${slug(x.source_id)}`,document_url:x.download_url??x.original_url,name_raw:x.standard_name??x.name,download_url:null,direct_url:null,alternative_urls:[],alternates:[],counting_boundary:x.status??'非PDF路线，未读原文，不计PDF候选或完整PDF',discovery_evidence:x.status}));
  const previews=[...rows(j.short_pdf_routes),...rows(j.preview_routes)].filter(x=>x.standard_number||x.name||x.standard_name).map(x=>({...x,candidate_id:x.route_id??`META-PREVIEW-${slug(x.source_id??x.standard_number)}`,preview_route_url:x.preview_url??x.download_url??x.direct_url,download_url:null,direct_url:null,alternative_urls:[],alternates:[],discovery_evidence:x.boundary??x.status??x.limitation??'短预览路线，不计实得完整PDF'}));
  const alternate=j.additional_indexed_pdf_url?[{...j,candidate_id:j.existing_candidate_id??j.source_id,name:standards.get(identify(j.standard_number).id)?.name,download_url:j.additional_indexed_pdf_url,discovery_evidence:j.access_status}]:[];
  const blocked=rows(j.blocked_routes).filter(x=>x.standard_number).map(x=>({...x,candidate_id:`META-BLOCKED-${slug(x.source_id)}`,name:x.standard_name??x.standard_name_hint??null,download_url:null,direct_url:null,alternative_urls:[],alternates:[],metadata_route_kind:'索引受阻路线（非可访问PDF候选）',discovery_evidence:[x.evidence??x.status,x.action].filter(Boolean).join('；')}));
  return [...nonpdf,...previews,...alternate,...blocked];
}
async function candidateFiles(dir){const found=[];for(const d of await fs.readdir(dir,{withFileTypes:true})){if(d.isDirectory()&&d.name!=='master-authority')found.push(...await candidateFiles(path.join(dir,d.name)));else if(d.isFile()&&/candidates.*\.json$|.*candidates\.json$|^extension-preview-routes\.json$/i.test(d.name))found.push(path.join(dir,d.name));}return found;}
const selectedSearchFiles=searchManifest?searchManifest.files.filter(e=>e.path.endsWith('.json')).map(e=>path.join(root,e.path)):await candidateFiles(path.join(root,'search'));
if(checkpoint==='1510'){
  const share=path.join(root,'pdf-audit/candidates-r11-alt31-share.json');
  if(sha(await fs.readFile(share))!=='2aa5cd96cfcc3f9d3848c7046575bb72e53b7426fb602f8b58b191558b94a61d')throw new Error('Alternate sharing projection changed');
  selectedSearchFiles.push(share);
}
for(const file of selectedSearchFiles.sort()){
  const j=await receipt(file);
  if(j.notice_only_index_routes?.length){external.route_observations??=[];external.route_observations.push(...j.notice_only_index_routes.map(x=>({...x,route_class:'公告索引待核，不建立编号题名已绑定的规范身份',catalog_source_file:path.relative(root,file).replace(/\\/g,'/')})));}
  const rootMetadata=[...(j?.standard_number&&j?.metadata_evidence?[{...j,candidate_id:`META-${slug(j.standard_number+(j.edition_note??''))}`,discovery_evidence:j.quality_boundary??j.permission}]:[]),...metadataExtras(j)];
  const supplemented=j?.supplement_only?external.search.find(x=>x.candidate_id===j.candidate_id):null;
  const supplements=supplemented?[{...supplemented,...j,alternative_urls:(j.historical_links??[]).flatMap(h=>[h.url,h.https_variant].filter(Boolean)),discovery_evidence:j.summary}]:[];
  for(const raw of [...rootMetadata,...(j?.candidates??[]),...(j?.draft_candidates??[]),...supplements,...(j?.metadata_only??[]).map(x=>({...x,candidate_id:`META-${slug(x.standard_number)}`,discovery_evidence:x.download_status??x.search_route_lead})),...(j?.metadata_only_non_pdf_routes??[]).map(x=>({...x,candidate_id:`META-NONPDF-${slug(x.document_url)}`,standard_number:x.name_raw,name:x.name_raw.match(/《([^》]+)》/)?.[1]??null,download_url:null,discovery_evidence:x.counting_boundary,metadata_evidence:[{source_url:x.source_page,source_id:x.source_id,claim:`附件原名：${x.name_raw}；格式${x.format}；${x.counting_boundary}`}]})),...(j?.zero_candidate_or_pending_routes??[]).map(x=>({...x,candidate_id:`META-ROUTE-${slug(x.standard_number)}`,download_url:null,alternative_urls:[],discovery_evidence:x.transient_parameter_note??x.status})),...(j?.no_direct_candidate??[]).map(x=>({...x,candidate_id:`LEAD-${slug(x.standard_number)}`,discovery_evidence:x.reference_limit,metadata_evidence:[{source_url:x.metadata_reference,claim:x.reference_limit}]}))]){
    if(!raw.standard_number&&!raw.name&&!raw.standard_name){external.route_observations??=[];external.route_observations.push({...raw,catalog_source_file:path.relative(root,file).replace(/\\/g,'/')});continue;}
    const c={...raw,name:raw.name??raw.standard_name??null,download_url:raw.download_url??raw.direct_url??null,source_page:raw.source_page??raw.detail_url??raw.metadata_reference??raw.direct_url??null,alternative_urls:raw.alternative_urls??raw.alternate_urls??raw.backup_urls??raw.alternates??[],discovered_by_query:raw.discovered_by_query??raw.discovery_query??null,discovery_evidence:raw.discovery_evidence??raw.observation??raw.boundary??[raw.version_candidate,raw.permission_observed,raw.english_name_from_source?`来源英文名：${raw.english_name_from_source}`:null,raw.next_check].filter(Boolean).join('；'),topic_group:raw.topic_group??(file.includes('g2-public-routes')?'G2':null)};
    const p=identify(`${c.standard_number??''} ${c.name??''} ${c.edition_note??c.edition_label??''}`,c.year,c.draft_stage);
    const mapped=(c.seed_ids??[]).map(id=>original.find(x=>x.seed_id===id)?.standard_id).map(id=>standards.get(id)).find(x=>x);
    let s=(mapped?.standard_id===p.id?mapped:null)??addStandard(p.id,{standard_number:p.published_code_candidate,name:c.name??(p.name||'中文名称待封面核准'),year:p.year,version_stage:p.stage,edition_label:p.edition_label});
    if(!p.number||p.number==='XXX')s.placeholder_code_observations=[...(s.placeholder_code_observations??[]),{context:'检索候选原始编号',standard_number:c.standard_number,source_id:c.candidate_id}];
    if(c.document_url){s.non_pdf_routes=[...(s.non_pdf_routes??[]),{document_url:c.document_url,format:c.format,source_id:c.source_id,source_page:c.source_page,original_name:c.name_raw}];s.issues.push(c.counting_boundary);}
    if(c.preview_route_url){s.preview_routes=[...(s.preview_routes??[]),{url:c.preview_route_url,source_id:c.source_id,boundary:c.discovery_evidence}];s.issues.push(c.discovery_evidence);}
    if(c.metadata_route_kind)s.issues.push(`${c.metadata_route_kind}：${c.discovery_evidence}`);
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
    for(const u of c.alternative_urls??[]){const alt=addLink(s,u,{source_page:c.source_page,source_kind:'公开检索备用候选',candidate_ids:[c.candidate_id],observations_scope:'此URL单独观察，主候选的页数/访问/质量不外推',notes:['备用URL独立候选；仅主候选的页数、访问与质量观察不适用于此URL。']});}
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

const round07Directory=has1350?await receipt(path.join(root,'search/round07-broad-attachments/directory/directory-round07.json')):null;
const round08Directory=has1410?await receipt(path.join(root,'search/round08-public-expansion/directory2/directory-round08.json')):null;
for(const directDirectory of [round07Directory,round08Directory].filter(Boolean))for(const d of directDirectory.records??[]){
  // These are numbered entries. The enclosing directory's own draft stage is not theirs.
  const p=identify(`${d.standard_number} ${d.name}`,d.year);
  const s=addStandard(p.id,{standard_number:d.standard_number,name:d.name,year:p.year,version_stage:p.stage,standard_family:d.standard_family});
  if(s.name!==d.name){s.name_variants=[...new Set([...(s.name_variants??[]),s.name,d.name])];s.issues.push(`直接目录题名差异：${s.name} / ${d.name} [${d.source_id}]`);}
  const eid=addEvidence({standard_id:s.standard_id,kind:'直接政府PDF目录（非规范全文）',statement_type:d.evidence_type??'原文事实（直接政府PDF表格解析）',source_id:d.source_id,source_url:d.source_pdf,source_page:d.source_page,source_date:d.source_publication_date,observed_at:directDirectory.checked_at,source_printed_page:d.source_printed_page,pdf_page_one_based:d.pdf_page_one_based,source_text:d.raw_cells.join(' / '),claim:`直接PDF目录原题名：${d.name}；原号：${d.raw_standard_number}；日期格：${d.date_cell_raw??''}；历史状态：${typeof d.historical_status_raw==='object'?JSON.stringify(d.historical_status_raw):d.historical_status_raw??''}`,applicability:`目录不是规范全文，混合日期格不写实施日期；${d.directory_stage??''}；${d.standard_version_stage??''}；不据此确认2026现行性`,raw_record:d});
  s.metadata_evidence_ids.push(eid);s.directory_memberships.push({source_id:d.source_id,evidence_id:eid,pdf_page_one_based:d.pdf_page_one_based,source_printed_page:d.source_printed_page,date_cell_raw:d.date_cell_raw});
  if(d.source_page&&!s.source_pages.includes(d.source_page))s.source_pages.push(d.source_page);
  for(const issue of p.issues)s.issues.push(issue);
  const prior=external.directories.findIndex(x=>x.source_id===d.source_id);
  if(prior<0)external.directories.push(d);
  else{const old=external.directories[prior];external.directories[prior]={...d,previous_observations:[...(old.previous_observations??[]),old]};}
}
const directoryCorrections=has1350?await receipt(path.join(root,'search/round07-broad-attachments/directory/corrections-round02.json')):null;
for(const c of directoryCorrections?.corrections??[]){
  const p=identify(c.standard_number),s=standards.get(p.id);if(!s)throw new Error(`Correction has no standard: ${c.standard_number}`);
  const eid=addEvidence({standard_id:s.standard_id,kind:'目录题名更正（保留旧索引证据）',statement_type:'原文事实（直接PDF原格）',source_id:`DIRECT-PDF-CORRECTION-${p.id}`,source_url:c.source_pdf,pdf_page_one_based:c.pdf_page_one_based,source_printed_page:c.source_printed_page,observed_at:directoryCorrections.checked_at,source_text:`旧索引：${c.old_name}；PDF原格：${c.new_direct_pdf_name}`,claim:c.reason,applicability:'优先直接原件题名，旧索引原文件及证据不改',raw_record:c});
  s.name_variants=[...new Set([...(s.name_variants??[]),s.name,c.old_name,c.new_direct_pdf_name])];
  s.name_correction_events=[...(s.name_correction_events??[]),{old_name:c.old_name,new_name:c.new_direct_pdf_name,evidence_id:eid,source_id:`DIRECT-PDF-CORRECTION-${p.id}`,at:directoryCorrections.checked_at}];
  s.name=c.new_direct_pdf_name;s.metadata_evidence_ids.push(eid);
}

const unresolvedDirectoryEntries=[];
for(const g of [...(round08Directory?.gaps??[]),...(round08Directory?.parse_issues??[])]){
  const entry_id=`GAP-${slug(JSON.stringify(g))}`,isMissingVersion=Boolean(g.name&&g.source_row_id);
  const eid=addEvidence({standard_id:null,entry_id,kind:isMissingVersion?'目录不完整编号/年份缺口':'目录说明行或解析位置待核',statement_type:'原文事实（直接PDF原格）',source_id:`${g.source_directory_id}:${g.source_row_id??g.pdf_page_one_based+'-'+g.row_index_in_table}`,source_url:g.source_pdf,pdf_page_one_based:g.pdf_page_one_based,source_printed_page:g.source_printed_page,observed_at:round08Directory.checked_at,source_text:g.raw_cells.join(' / '),claim:g.reason,applicability:'保留原格与页码，不自动补全年份，不计编号版本；不是无编号在编草案',raw_record:g});
  const entry={entry_id,...g,raw_code:g.raw_cells?.[2]??null,entry_class:isMissingVersion?'编号/四位年份未闭合':'非标准说明或解析待核',evidence_id:eid};
  unresolvedDirectoryEntries.push(entry);
  issues.push({issue_id:`I-${slug(entry_id)}`,standard_id:null,entry_id,name:g.name??'目录说明/解析缺口',seed_ids:[],type:entry.entry_class,status:'待核',priority:'常规',action:`${g.reason}；PDF顺序${g.pdf_page_one_based}/印刷${g.source_printed_page??'无'}；原格${g.raw_cells.join(' / ')}`,source_ids:[eid]});
}

const ttbzDirectory=has1410?await receipt(path.join(root,'search/master-authority/ttbz-ui-observed-20261017-p1.json')):null;
for(const d of ttbzDirectory?.standards??[]){
  const p=identify(`${d.standard_number} ${d.name}`,d.year);
  const s=addStandard(p.id,{standard_number:d.standard_number,name:d.name,year:p.year,version_stage:'正式目录记录'});
  if(s.name!==d.name){s.name_variants=[...new Set([...(s.name_variants??[]),s.name,d.name])];s.issues.push(`平台当前题名差异待核：${s.name} / ${d.name}`);}
  const eid=addEvidence({standard_id:s.standard_id,kind:'全国团体平台公开DOM当前目录',statement_type:d.statement_type,source_id:d.source_id,source_url:d.source_page,source_page:d.list_source_page,observed_at:d.status_checked_at,source_text:`平台标注${d.current_status_reported}；公布${d.public_announcement_date}；发布${d.published_date}；实施${d.effective_date}`,claim:d.status_basis,applicability:'仅实际匿名DOM观察的10条/1页；2960组织徽章及前100上限不当已采集数；非全文或具体工程适用性证明',raw_record:d});
  s.metadata_evidence_ids.push(eid);s.status_evidence_ids.push(eid);s.directory_memberships.push({source_id:d.source_id,evidence_id:eid,source_kind:'TTBZ公开DOM'});
  s.current_status='现行（全国团体平台标注）';s.status_checked_at=d.status_checked_at;s.status_basis=d.status_basis;s.status_source_scope='全国团体标准信息平台公开列表，10条实际观察';s.standard_type=d.standard_type;s.public_announcement_date=d.public_announcement_date;
  s.metadata_date_layers=[...(s.metadata_date_layers??[]),{context:'全国团体平台公开DOM详细标签',source_id:d.source_id,public_announcement_date:d.public_announcement_date,published_date:d.published_date,effective_date:d.effective_date}];
  for(const key of ['published_date','effective_date']){if(s[key]&&s[key]!==d[key])s.issues.push(`${key}日期冲突：${s[key]} / ${d[key]} [${d.source_id}]`);else s[key]=d[key];}
  if(!s.source_pages.includes(d.source_page))s.source_pages.push(d.source_page);
  external.directories.push(d);
}

const recentDirectories=[];
if(checkpoint==='1510')for(const file of ['search/round09-new-sources/recent-directory/recent-directory-r09.json','search/round10-public-sources/monthly-directory/monthly-directory-r10.json','search/round11-public-sources/monthly-directory/monthly-directory-r11.json']){
  const batch=await receipt(path.join(root,file));recentDirectories.push({file,data:batch});
  const sourceMap=new Map(batch.sources.map(s=>[s.source_id,s]));
  for(const d of batch.records){
    if(!d.number_year_key||!d.year)continue;
    const p=identify(`${d.standard_number_as_published} ${d.standard_name_as_published}`,d.year);
    if(!p.number||!p.year)throw new Error(`Unparsed resolved monthly code: ${d.record_id}`);
    const source=sourceMap.get(d.source_id),category=d.source_category??source?.source_category??'government';
    const dateConflicts=(batch.conflicts??[]).filter(c=>c.record_id===d.record_id);
    const s=addStandard(p.id,{standard_number:d.standard_number_as_published,name:d.standard_name_as_published,year:p.year,version_stage:'正式目录记录'});
    if(s.name!==d.standard_name_as_published){s.name_variants=[...new Set([...(s.name_variants??[]),s.name,d.standard_name_as_published])];s.issues.push(`月度目录题名差异：${s.name} / ${d.standard_name_as_published} [${d.record_id}]`);}
    const eid=addEvidence({standard_id:s.standard_id,kind:category==='government'?'政府月度实施目录':'研究院公开信息平台实施目录（补充来源）',statement_type:d.fact_type??'原文事实',source_id:d.record_id,publisher_source_id:d.source_id,source_url:d.source_page,source_page:d.source_page,source_category:category,source_location:d.source_location,webpage_published_date:d.webpage_published_date,observed_at:source?.checked_at??batch.generated_at,source_text:d.raw_cells.join(' / '),claim:`目录列载${d.standard_number_as_published} ${d.standard_name_as_published}；实施格${d.effective_date_as_published}；网页标题${source?.title_as_published??''}`,applicability:'仅证明目录原格；网页日期不是标准发布日期，历史实施列表不确认2026现行性；机构补充不冒充政府/协会',raw_record:d});
    s.metadata_evidence_ids.push(eid);s.directory_memberships.push({source_id:d.record_id,source_directory_id:d.source_id,evidence_id:eid,source_category:category,source_location:d.source_location});
    s.metadata_date_layers=[...(s.metadata_date_layers??[]),{context:'月度实施清单原格',source_id:d.record_id,webpage_published_date:d.webpage_published_date,title_as_published:source?.title_as_published,effective_date_as_published:d.effective_date_as_published,effective_date:d.effective_date,standard_published_date:null,date_conflicts:dateConflicts}];
    if(dateConflicts.length){s.issues.push(`来源标题/实施格年份冲突：${source?.title_as_published} / ${d.effective_date_as_published} [${d.record_id}]；本来源实施值不静默采用`);}
    else if(d.effective_date){if(s.effective_date&&s.effective_date!==d.effective_date)s.issues.push(`实施日期来源冲突：${s.effective_date} / ${d.effective_date} [${d.record_id}]`);else s.effective_date=d.effective_date;}
    if(!s.source_pages.includes(d.source_page))s.source_pages.push(d.source_page);
    external.directories.push({...d,source_id:d.record_id,source_directory_id:d.source_id,standard_number:d.standard_number_as_published,name:d.standard_name_as_published,number:p.number,year:p.year,source_category:category});
  }
  for(const g of batch.gaps??[]){
    const entry_id=`GAP-${slug(g.record_id)}`,source=sourceMap.get(g.source_id);
    const eid=addEvidence({standard_id:null,entry_id,kind:'月度目录图集短年码缺口',statement_type:'原文事实',source_id:g.record_id,source_url:source?.source_page,source_location:g.source_location,source_text:g.raw_cells.join(' / '),claim:g.reason,observed_at:source?.checked_at??batch.generated_at,applicability:'不展开两位尾码，不计四位年编号版本',raw_record:g});
    unresolvedDirectoryEntries.push({entry_id,...g,entry_class:'图集编号/年份待核',raw_code:g.raw_cells[1],evidence_id:eid});
    issues.push({issue_id:`I-${slug(entry_id)}`,standard_id:null,entry_id,name:g.raw_cells[2],seed_ids:[],type:'图集编号/年份待核',status:'待核',priority:'常规',action:`${g.reason}；${JSON.stringify(g.source_location)}`,source_ids:[eid]});
  }
}

// Dated publication/withdrawal events remain distinct from a 2026 current-status claim.
const withdrawnSource=evidence.find(e=>e.source_id==='HNIS-CECS-2185-20241115');
if(withdrawnSource){
  for(const [sid,event] of [['CECS-22-2024-FORMAL','公告载明实施'],['CECS-22-2005-FORMAL','公告载明废止并被2024版替代']]){const s=standards.get(sid);if(!s)continue;s.status_events=[...(s.status_events??[]),{event,event_date:'2025-04-01',published_date:'2024-11-12',evidence_id:withdrawnSource.evidence_id,source_id:withdrawnSource.source_id,evidence_level:'省级标准化机构转载协会第2185号公告，协会原页待复核'}];s.status_evidence_ids.push(withdrawnSource.evidence_id);s.status_checked_at=now;s.replacement_relationships.push({kind:event,replaces:sid.includes('-2024-')?'CECS-22-2005-FORMAL':null,replaced_by:sid.includes('-2005-')?'CECS-22-2024-FORMAL':null,applies_as_of:'2025-04-01',evidence_id:withdrawnSource.evidence_id,evidence_level:'机构转载，2026当前现行性另核'});s.issues.push('第2185号转载公告所载2025-04-01废止/实施事件可见；2024版2026现行性与协会原公告仍待核');}
}

const repeal69=checkpoint==='1510'?await receipt(path.join(root,'pdf-audit/evidence-85-repeal-cecs69-94.json')):null;
if(repeal69){
  for(const [id,old] of [['CECS-69-1994-FORMAL',true],['CECS-69-2011-FORMAL',false]]){
    const s=standards.get(id);if(!s)throw new Error(`Missing 85 event identity ${id}`);
    const eid=addEvidence({standard_id:id,kind:'出版物内协会第85号公告',statement_type:repeal69.statement_type,source_id:repeal69.source_id,source_url:repeal69.source_url,observed_at:repeal69.checked_at,source_text:repeal69.quote,pdf_page_one_based:2,source_printed_page:null,claim:'2011-06-22公告；69:2011自2011-10-01施行，旧69:94同时废止',applicability:'PDF2左半无印刷页码为公告；PDF16右印25为批准日/公告号旁证；不确认2011版2026现行性',raw_record:repeal69});
    s.status_evidence_ids.push(eid);s.status_checked_at=repeal69.checked_at;s.status_events=[...(s.status_events??[]),{event:old?'旧版同时废止':'新版施行',event_date:'2011-10-01',published_date:'2011-06-22',source_id:repeal69.source_id,evidence_id:eid}];
    if(old){s.current_status='已废止（依据2011-10-01公告事件）';s.withdrawal_date='2011-10-01';s.replaced_by='CECS-69-2011-FORMAL';s.status_basis='实得出版物第85号公告，PDF顺序2左半无印页，双审目视；PDF16右印25为旁证；依据PDF-CECS-85-REPEAL-20261017';}
    else{s.published_date='2011-06-22';s.effective_date='2011-10-01';}
  }
}

const repealEvidence=has1350?await receipt(path.join(root,'pdf-audit/evidence-2185-repeal-cecs22-2005.json')):null;
if(repealEvidence){
  for(const [id,old] of [['CECS-22-2005-FORMAL',true],['CECS-22-2024-FORMAL',false]]){
    const s=standards.get(id);if(!s)throw new Error(`Missing 2185 event identity: ${id}`);
    const eid=addEvidence({standard_id:id,kind:'出版物内协会第2185号公告',statement_type:repealEvidence.statement_type,source_id:repealEvidence.source_id,source_url:repealEvidence.document.final_url,observed_at:repealEvidence.checked_at,source_text:repealEvidence.short_quote,claim:repealEvidence.event.claim,pdf_page_one_based:5,source_printed_page:null,applicability:old?'2025-04-01旧版同时废止事件；保留历史PDF':'仅公告所载施行事件，2024版2026现行性另核',raw_record:repealEvidence});
    s.status_evidence_ids.push(eid);s.status_checked_at=repealEvidence.checked_at;
    s.status_events=[...(s.status_events??[]),{event:old?'旧版同时废止':'新版施行',event_date:'2025-04-01',published_date:'2024-11-12',evidence_id:eid,source_id:repealEvidence.source_id,evidence_level:'实得出版物内公告图像，PDF顺序第5页、无印刷页码，双审目视'}];
    if(old){s.current_status='已废止（依据2025-04-01公告事件）';s.withdrawal_date='2025-04-01';s.replaced_by='CECS-22-2024-FORMAL';s.status_basis='实得第三方托管出版物内协会第2185号公告；PDF顺序第5页、无印刷页码，双审目视确认2025-04-01同时废止；依据PDF-CECS-2185-REPEAL-20261017';}
    else{s.effective_date='2025-04-01';s.published_date='2024-11-12';}
  }
}

const auditInput=await receipt(path.join(root,'pdf-audit/audit-results.json'));
if(checkpoint){const auditFreeze=await receipt(path.join(root,`pdf-audit/freeze-${checkpoint}-receipt.json`));const actual=sha(await fs.readFile(path.join(root,'pdf-audit/audit-results.json')));if(actual!==auditFreeze.sha256||auditInput.results.length!==auditFreeze.result_count)throw new Error('Audit freeze changed before import');}
for(const a of auditInput?.results??[]){
  const p=identify(`${a.standard_number??''} ${a.name??''}`,a.year,a.draft_stage??(/征求意见/.test(a.version_match??'')?'征求意见稿':null),a.version_class);
  const existing=[...links.values()].find(l=>[l.requested_url,l.discovery_url,l.final_url].includes(a.requested_url??a.download_url));
  const matchedUnnumbered=matchUnnumberedAuditCandidate(a,p,existing,standards);
  if(matchedUnnumbered)p.id=matchedUnnumbered;
  let ss=existing?.standard_ids.filter(id=>id===p.id).map(id=>standards.get(id)).filter(Boolean)??[];
  if(!ss.length)ss=[addStandard(p.id,createAuditIdentity(a,p))];
  for(const s of ss){
    updateAuditIdentity(s,a);
    if((!p.number||p.number==='XXX')&&a.standard_number){s.placeholder_code_observations=[...(s.placeholder_code_observations??[]),{context:'独立审查所见占位编号',standard_number:a.standard_number,source_id:a.audit_id,observed_at:a.checked_at}];s.standard_number=a.standard_number;}
    const l=addLink(s,a.requested_url??a.download_url,{source_page:a.source_page,source_kind:'独立审查公开候选'});
    if(!l)continue;
    if(a.metadata_only){l.source_kind='公告/元数据文档（非标准全文）';l.metadata_only=true;}
    for(const issue of p.issues)if(!s.issues.includes(issue))s.issues.push(issue);
    const history=(a.audit_history??[]).map(h=>({...h,audit_id:a.audit_id}));
    l.verified_standard_ids=a.version_verified===true?[p.id]:[];
    Object.assign(l,{candidate_ids:[...new Set([...(l.candidate_ids??[]),a.candidate_id].filter(Boolean))],final_url:a.final_url??null,checked_at:a.visual_checked_at??a.checked_at,http_status:a.http_status??null,download_status:a.download_status,access_restriction:a.access_restriction??a.encryption_permissions??(a.http_status===200?'公开GET响应（本次）':'未证实'),url_expiry:a.url_expiry??'未声明；仅代表检查时可用',pdf_bytes:a.bytes??null,pages:a.pages??null,sha256:a.sha256??null,parse_ok:a.pdf_parse??null,version_match:a.version_match??null,version_verified:a.version_verified===true,text_layer:a.text_layer??null,search_copy:a.searchable??null,bookmarks:a.bookmark_count??null,bookmark_navigation:a.bookmark_navigation??null,clickable_toc:a.clickable_toc??null,clarity:a.clarity??null,page_order:a.page_order??null,cropping_rotation:JSON.stringify({rotation:a.rotation_summary,cropped:a.cropbox_diff_pages}),watermark:a.watermark??null,encrypted:a.encrypted??null,completeness:a.completeness??'未完成完整性核验',complete_pdf:a.complete_pdf===true&&a.version_verified===true,recommendation:a.recommendation??'待审',recommendation_reason:a.recommendation_reason??'',audit_evidence_paths:a.evidence_paths??[],local_audit_file:a.local_path??null,check_history:history,audit_id:a.audit_id,audit_result:a});
    Object.assign(l,auditCompletenessFields(a));
    if(l.draft_content_complete){s.version_stage=a.version_class??p.stage;s.draft_content_complete=true;s.version_class=a.version_class;s.draft_stage=a.draft_stage;}
    if(a.error&&!l.notes.includes(a.error))l.notes.push(a.error);
    if(a.metadata_only)l.complete_pdf=false;
    if(a.source_page&&!s.source_pages.includes(a.source_page))s.source_pages.push(a.source_page);
    const observedId=addEvidence({standard_id:s.standard_id,kind:'GET与解析观测',statement_type:'原文事实（HTTP与解析实测）',source_id:a.audit_id,source_url:a.final_url??a.requested_url??a.download_url,observed_at:a.checked_at,claim:`HTTP ${a.http_status??'未知'}；字节 ${a.bytes??'未知'}；页数 ${a.pages??'未知'}；SHA256 ${a.sha256??'无'}`,evidence_paths:a.evidence_paths??[]});
    const eid=addEvidence({standard_id:s.standard_id,kind:'PDF完整性与阅读质量判断',statement_type:l.quality_statement_type,source_id:a.audit_id,source_url:a.final_url??a.requested_url??a.download_url,observed_at:a.checked_at,claim:`${a.completeness??a.download_status}；等级${a.recommendation??'未定'}：${a.recommendation_reason??''}`,applicability:'AI基于实测的审查判断，不是出版方认证；正式全文与草案内容完整性分开',evidence_paths:a.evidence_paths??[]});l.source_ids.push(observedId,eid);
  }
  external.audit.push(a);
}

const conflict=await receipt(path.join(root,'search/conflict-796-years.json'));
if(conflict){for(const value of conflict.retained_values??[]){const p=identify(`${value} ${conflict.name}`);const s=addStandard(p.id,{standard_number:value,name:conflict.name,year:p.year});s.name=conflict.name;s.version_stage='正式性/年份冲突待核';s.identity_conflict_group=conflict.source_id;s.identity_confirmed=false;s.issues.push(conflict.status);for(const e of conflict.evidence??[]){const id=addEvidence({standard_id:s.standard_id,kind:'编号年份冲突',observed_at:conflict.checked_at,...e});s.metadata_evidence_ids.push(id);}s.issues.push(...(conflict.next_test??[]));}}
const conflictSupplement=has1330?await receipt(path.join(root,'search/round05-796-conflict-supplement.json')):null;
if(conflictSupplement){for(const id of ['CECS-796-2020-FORMAL','CECS-796-2021-FORMAL']){const s=standards.get(id);if(!s)continue;const e=addEvidence({standard_id:id,kind:'796公告副本与出版年份冲突',statement_type:'原文事实（所见副本）',source_id:conflictSupplement.source_id,source_url:conflictSupplement.source_url,observed_at:conflictSupplement.source_checked_at,claim:JSON.stringify(conflictSupplement.metadata_claim),applicability:'第三方托管协会公告副本1页，非标准全文；不消除出版方2020与公告2021冲突',raw_record:conflictSupplement});s.metadata_evidence_ids.push(e);s.metadata_date_layers=[...(s.metadata_date_layers??[]),{context:'第757号公告副本所载日期（非对身份冲突的裁决）',...conflictSupplement.metadata_claim}];s.issues.push(conflictSupplement.status);}}

const frozenBaseline1410=has1410?await readJson(path.join(out,'history/master-before-1410.json')):null;
if(has1410&&!frozenBaseline1410)throw new Error('1410 requires its immutable pre-merge master snapshot');
const round08Conflicts=has1410?await receipt(path.join(root,'search/round08-public-expansion/directory2/directory-conflicts.json')):null;
for(const c of round08Conflicts?.conflicts??[]){
  const id=identify(c.variants[0].standard_number).id,s=standards.get(id);if(!s)throw new Error(`Missing conflict identity ${id}`);
  const names=[...new Set(c.variants.map(v=>v.name))],old=frozenBaseline1410?.standards.find(s=>s.standard_id===id);
  s.name_variants=[...new Set([...(s.name_variants??[]),s.name,...names])];s.name=old?.name??'题名冲突待核';s.name_resolution_status='同号异名待核；未选定正式题名';s.identity_confirmed=false;s.identity_conflict_group=`XJ-R08-${c.number}-${c.year}`;
  s.directory_name_conflicts=c.variants;
  const conflictEvidence=c.variants.map(v=>addEvidence({standard_id:id,kind:'政府目录同编号年份多题名',statement_type:'原文事实（直接PDF原格，另有目视复核）',source_id:`${s.identity_conflict_group}:${v.source_row_id}`,source_url:round08Directory.records[0].source_pdf,pdf_page_one_based:v.pdf_page_one_based,source_printed_page:v.source_printed_page,observed_at:round08Conflicts.checked_at,source_text:v.raw_cells.join(' / '),claim:`目录所见题名：${v.name}；${c.type}`,applicability:'保留全部原始取值及页码；不按行顺序选择正式题名，不拆成两个已确认规范',raw_record:v}));
  s.metadata_evidence_ids.push(...conflictEvidence);s.issues.push(`${c.type}：${names.join(' / ')}`);
  issues.push({issue_id:`I-${slug(s.identity_conflict_group)}`,standard_id:id,seed_ids:s.seed_ids,type:'同编号年份多题名冲突',status:'待核',priority:'常规',action:c.variants.map(v=>`${v.name} [PDF顺序${v.pdf_page_one_based}/印刷${v.source_printed_page}]`).join('；')+'；待官方核号，不选定正式题名',source_ids:conflictEvidence});
}

// Explicit human maintenance is merged last; regeneration never loses these records.
const maintenance=await readJson(path.join(out,'maintenance-input.json'))??{schema_version:1,standards:[],links:[],note:'新增/更新/停用写入本文件；原始记录与证据永久保留。字段变更须注明reason/source_id。'};
if(!(await readJson(path.join(out,'maintenance-input.json'))))await fs.writeFile(path.join(out,'maintenance-input.json'),JSON.stringify(maintenance,null,2));
for(const [type,map] of [['standards',standards],['links',links]])for(const m of maintenance[type]??[]){const id=m.standard_id??m.link_id;let entry=map.get(id);if(!entry&&type==='standards'&&m.action==='新增')entry=addStandard(id,m.fields??{});if(!entry)throw new Error(`维护记录找不到${type}: ${id}`);if(!m.reason||!m.source_id)throw new Error(`维护记录须有reason与source_id: ${id}`);Object.assign(entry,m.fields??{});entry.active=m.action!=='停用';entry.maintenance_action=m.action;entry.maintenance_source={reason:m.reason,source_id:m.source_id,at:m.at??now};}
for(const s of standards.values()){
  s.metadata_evidence_ids=[...new Set(s.metadata_evidence_ids)];s.status_evidence_ids=[...new Set(s.status_evidence_ids)];s.issues=[...new Set(s.issues)];
  const ranked=s.link_ids.map(id=>links.get(id)).filter(l=>l.active&&l.complete_pdf&&l.verified_standard_ids?.includes(s.standard_id)).sort((a,b)=>({A:1,B:2,C:3,D:4}[a.recommendation]??9)-({A:1,B:2,C:3,D:4}[b.recommendation]??9)||(b.bookmarks??0)-(a.bookmarks??0));
  s.best_link_id=ranked[0]?.link_id??null;s.usable_alternative_count=Math.max(0,ranked.length-1);
  const completeDrafts=s.link_ids.map(id=>links.get(id)).filter(l=>l.active&&l.draft_content_complete&&l.version_verified&&l.verified_standard_ids?.includes(s.standard_id)&&/报批|征求意见|送审|草案/.test(l.version_class??l.draft_stage??''));
  s.best_draft_link_id=completeDrafts[0]?.link_id??null;
  if(!s.link_ids.length)s.issues.push('尚未发现全文下载候选链接');
}

const model={schema_version:'1.1.0',generated_at:now,scope:{target:'全网现存CECS规范与历史版本，持续增补；本轮非穷尽性普查',baseline_definition:'用户提供结构专业知识库CECS搜索结果81条文件记录',baseline_records:81,baseline_distinct_filenames:77,baseline_source:seed.summary,coverage_denominator:'全国CECS全集总数未知，不用81或单站目录条数作为全国覆盖分母',groups,authority_directories:directory?.sources??[],directory_coverage:directory?.coverage??null},standards:[...standards.values()],links:[...links.values()],original_records:original,evidence,issues,external_inputs:receipts,external,coverage:{baseline_records_registered:original.length,baseline_standard_versions:[...standards.values()].filter(s=>s.baseline).length,registered_standard_versions:standards.size,registered_links:links.size,verified_complete_pdf_links:[...links.values()].filter(l=>l.complete_pdf).length,verified_complete_standard_versions:[...standards.values()].filter(s=>s.best_link_id).length,authority_records:directory?.standards?.length??0,independent_audit_results:external.audit.length,downloaded_parseable_pending:[...links.values()].filter(l=>l.pages&&!l.complete_pdf&&/可解析/.test(l.download_status)).length},change_log:[]};
model.coverage.verified_complete_unique_sha256=new Set(model.links.filter(l=>l.complete_pdf&&l.sha256).map(l=>l.sha256)).size;
model.unresolved_drafts=unresolvedDrafts;
model.coverage.unresolved_unnumbered_drafts=unresolvedDrafts.length;
model.unresolved_directory_entries=unresolvedDirectoryEntries;
model.coverage.unresolved_directory_version_gaps=unresolvedDirectoryEntries.filter(e=>e.entry_class==='编号/四位年份未闭合').length;
model.coverage.directory_nonstandard_or_parse_gaps=unresolvedDirectoryEntries.filter(e=>e.entry_class==='非标准说明或解析待核').length;
model.coverage.unresolved_recent_directory_gaps=unresolvedDirectoryEntries.filter(e=>e.entry_class==='图集编号/年份待核').length;
model.coverage.verified_complete_draft_pdf_links=model.links.filter(l=>l.draft_content_complete&&l.version_verified&&!l.complete_pdf).length;
model.coverage.verified_complete_draft_versions=model.standards.filter(s=>s.best_draft_link_id).length;
model.coverage.supplemental_directory_records=supplementalDirectory?.records?.length??0;
model.coverage.round07_directory_observations=round07Directory?.records?.length??0;
model.coverage.round08_directory_observations=round08Directory?.records?.length??0;
model.coverage.ttbz_observed_records=ttbzDirectory?.standards?.length??0;
model.coverage.recent_directory_rows_including_gaps=recentDirectories.reduce((n,b)=>n+b.data.records.length,0);
model.coverage.recent_directory_resolved_rows=recentDirectories.reduce((n,b)=>n+b.data.records.filter(d=>d.number_year_key&&d.year).length,0);
model.coverage.directory_observation_count=(directory?.standards?.length??0)+(supplementalDirectory?.records?.length??0)+(round07Directory?.records?.length??0)+(round08Directory?.records?.length??0)+(ttbzDirectory?.standards?.length??0)+model.coverage.recent_directory_resolved_rows;
model.coverage.authority_records=external.directories.length;
model.scope.authority_directories.push(...(supplementalDirectory?.sources??[]));
if(ttbzDirectory)model.scope.authority_directories.push({source_id:ttbzDirectory.source_id,source_page:ttbzDirectory.source_page,checked_at:ttbzDirectory.checked_at,scope:ttbzDirectory.coverage});
for(const batch of recentDirectories)model.scope.authority_directories.push(...batch.data.sources);
model.scope.directory_coverage={...model.scope.directory_coverage,supplemental:supplementalDirectory?.coverage??null,round07:round07Directory?.coverage??null,round08:round08Directory?.coverage??null,ttbz_public_dom:ttbzDirectory?.coverage??null};
model.scope.directory_coverage.recent=recentDirectories.map(b=>({file:b.file,summary:b.data.summary}));
model.scope.checkpoint=checkpoint;
if(checkpoint==='1510'){
  const policy=await receipt(path.join(out,'scope-policy-20261017.json'));if(policy.active_instruction_id!=='USER-20261017-CECS-ENGINEERING-ALL')throw new Error('Wrong active CECS scope');
  model.scope.active_instruction_id=policy.active_instruction_id;model.scope.active_scope='工程相关CECS均可收集下载，房屋结构优先';model.scope.target='工程相关CECS与历史版本持续增补，保留专业与适用范围分类；非穷尽性普查';model.scope.classification_policy='沿用现有专业/交叉标签和适用范围，本批不大规模重分类；非房屋结构不构成排除理由';model.scope.instruction_history=policy.instruction_history;model.external.scope_policy=policy;
  model.external.current_alternate_share=await receipt(path.join(root,'pdf-audit/candidates-r11-alt31-share.json'));model.external.alternate_publication_selection=await receipt(path.join(root,'pdf-audit/audit-round09-publication-selection-1450.json'));
}
if(checkpoint==='1510'){
  const regions=await receipt(path.join(out,'download-source-region-evidence-1510.json'));
  if(!regions||regions.source_id!=='USER-20261017-CECS-DOWNLOAD-SOURCE-REGION')throw new Error('Download source region evidence registry required');
  for(const input of regions.supplemental_inputs??[]){const file=path.join(root,input.path);if(sha(await fs.readFile(file))!==input.sha256)throw new Error(`Region metadata input changed: ${input.path}`);await receipt(file);}
  applyDownloadSourceRegions(model,regions);
  for(const r of regions.evidence??[])addEvidence({standard_id:null,kind:'资料下载来源主体省市依据',statement_type:r.statement_type??'原文事实（官方机构联系地址）',source_id:r.region_evidence_id,source_url:r.proof_url,source_text:r.proof_excerpt,observed_at:r.checked_at,claim:`${r.source_entity}；来源省市${r.province??'待核'}/${r.city??'待核'}`,applicability:'仅资料来源主体所在地，不是标准适用地区、机房/IP或CDN运营商地址；匹配实际下载host或明确附件URL',raw_record:r});
  model.scope.download_source_region_policy={source_id:regions.source_id,meaning:'实际资料发布/下载来源主体省市；不是标准适用地区、目录来源传递、服务器或CDNIP所在地',unknown:'无明确证据标待核；无下载链接不借用目录地区',registry:'catalog/download-source-region-evidence-1510.json'};
}
model.scope.directory_unique_number_year_count=new Set(external.directories.map(d=>identify(d.standard_number,d.year).id)).size;
model.external.search_manifest=searchManifest;
model.external.search_manifests=searchManifests;
model.external.conflict_796_supplement=conflictSupplement;
if(has1330)model.external.completeness_feedback=await receipt(path.join(root,'search/round06-22-completeness-receipt.json'));
model.external.directory_supplement=supplementalDirectory;
model.external.directory_round07=round07Directory;
model.external.directory_round08=round08Directory;
model.external.directory_round08_conflicts=round08Conflicts;
model.external.ttbz_public_dom=ttbzDirectory;
model.external.directory_corrections=directoryCorrections;
model.external.repeal_2185=repealEvidence;
model.external.repeal_85=repeal69;
model.external.recent_directories=recentDirectories;
if(has1350)model.external.round07_water_mep=await receipt(path.join(root,'search/round07-broad-attachments/water-mep/candidates-round07-water-mep-share-v2.json'));
model.external.search_coverage=checkpoint?await receipt(path.join(root,'search/g1-round03-coverage.json')):null;

for(const s of model.standards) for(const txt of s.issues) issues.push({issue_id:`I-${slug(s.standard_id+txt)}`,standard_id:s.standard_id,seed_ids:s.seed_ids,type:'识别或状态待核实',status:'待查',priority:'常规',action:txt,source_ids:s.metadata_evidence_ids});

const previous=await readJson(path.join(out,'cecs-master.json'));
const mergeBaseline=checkpoint==='1510'?await readJson(path.join(out,'history/master-before-1510.json')):checkpoint==='1410'?frozenBaseline1410:has1350?await readJson(path.join(out,'history/master-before-1350.json')):previous;
const round07Baseline=has1350?await readJson(path.join(out,'history/master-before-1350.json')):mergeBaseline;
if(round07Directory&&round07Baseline){
  const baselineIds=new Set(round07Baseline.standards.map(s=>s.standard_id));
  const roundIds=new Set(round07Directory.records.map(d=>identify(`${d.standard_number} ${d.name}`,d.year).id));
  model.coverage.round07_directory_unique_identities=roundIds.size;
  model.coverage.round07_directory_new_identities_against_frozen_master=[...roundIds].filter(id=>!baselineIds.has(id)).length;
}
if(mergeBaseline){
  const baselineIds=new Set(mergeBaseline.standards.map(s=>s.standard_id));
  if(round08Directory){const ids=new Set(round08Directory.records.map(d=>identify(`${d.standard_number} ${d.name}`,d.year).id)),r08base=new Set((frozenBaseline1410??mergeBaseline).standards.map(s=>s.standard_id));model.coverage.round08_directory_unique_identities=ids.size;model.coverage.round08_directory_new_identities_against_frozen_master=[...ids].filter(id=>!r08base.has(id)).length;}
  if(ttbzDirectory){const old=new Set((frozenBaseline1410??mergeBaseline).standards.map(s=>s.standard_id));model.coverage.ttbz_new_identities_against_frozen_master=ttbzDirectory.standards.filter(d=>!old.has(identify(d.standard_number,d.year).id)).length;}
  if(recentDirectories.length){const ids=new Set(recentDirectories.flatMap(b=>b.data.records.filter(d=>d.number_year_key&&d.year).map(d=>identify(d.standard_number_as_published,d.year).id)));model.coverage.recent_directory_unique_identities=ids.size;model.coverage.recent_directory_new_identities_against_frozen_master=[...ids].filter(id=>!baselineIds.has(id)).length;}
  model.coverage.merge_net_new_identities=model.standards.filter(s=>!baselineIds.has(s.standard_id)).length;
  model.scope.merge_baseline={generated_at:mergeBaseline.generated_at,registered_standard_versions:mergeBaseline.standards.length,registered_links:mergeBaseline.links.length};
}
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
const drafts=model.links.filter(l=>l.draft_content_complete&&l.version_verified&&!l.complete_pdf&&l.active);
const sorted=[...model.standards].sort((a,b)=>Number(b.baseline)-Number(a.baseline)||a.standard_number?.localeCompare(b.standard_number??'','en',{numeric:true})||a.standard_id.localeCompare(b.standard_id));
const mapLinks=new Map(model.links.map(l=>[l.link_id,l]));
const pdfState=s=>{if(s.best_link_id)return '已验完整PDF';if(s.best_draft_link_id)return `完整${s.version_class??s.draft_stage??'草案'}，非正式标准全文`;const ls=s.link_ids.map(id=>mapLinks.get(id));return ls.find(l=>l.pages&&/可解析/.test(l.download_status))?.download_status??(ls.length?ls.find(l=>l.checked_at)?.download_status??'候选未实测':'尚无下载候选');};
const standardRows=sorted.map(s=>[s.standard_number,`${s.name}${s.edition_label?`（${s.edition_label}）`:''}${s.name_resolution_status&&s.name!=='题名冲突待核'?'（同号异名待核）':''}`,mapLinks.get(s.best_link_id??s.best_draft_link_id)?.final_url??'',pdfState(s),s.current_status,s.version_stage,s.year,s.baseline?'基线':'新增',s.topic_group_name??'待分组',s.scope,s.standard_type,dateValue(s.effective_date),dateValue(s.published_date),s.status_checked_at?stamp(s.status_checked_at):'',s.source_pages[0]??'',s.usable_alternative_count,s.standard_id,s.issues.join('\n'),s.seed_ids.join(', '),s.link_ids.length,s.replacement_relationships.map(r=>`${r.kind}: ${r.replaces_raw??r.replaces??r.replaced_by??''}${r.applies_as_of?`；日期${r.applies_as_of}`:''}${r.evidence_level?`；${r.evidence_level}`:''} [${r.evidence_id}]`).join('\n'),s.status_evidence_ids.join(', '),s.name_variants?.join('\n')??'',dateValue(s.withdrawal_date),s.status_basis??'',dateValue(s.public_announcement_date),s.download_source_region_summary??'尚未分类']);
const configs=[];
const nativeHyperlinks=[];
const regionBasisText=r=>(r?.region_basis??[]).map(b=>`${b.source_entity??''}；${b.province??'省份待核'}/${b.city??'城市待核'}；${b.proof_excerpt??''} [${b.proof_url??''}]；证据${b.region_evidence_id}；匹配${(b.matches??[]).map(m=>`${m.field}:${m.host}`).join('、')}`).join('\n');
function makeSheet(name,title,headers,rows,{widths={},urls=[],dates=[],times=[],rowHeight=48,primary=false}={}){
  headers=headers.map(h=>h==='章节书签数'?'书签总数（标签类型见跳转）':h);
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
const main=makeSheet('规范总表','CECS 规范与下载总表', ['规范编号','规范名称','推荐PDF（草案见稿型）','PDF核验状态','2026现行性','稿型','年份','基线/新增','专业分组','适用范围','标准类型','实施日期','发布日期','现行性核验日期','来源详情页','有效备用数','稳定ID','待查问题','原记录映射','候选链接数','历史替代关系','状态证据ID','名称差异','废止日期','状态依据与定位','平台公布日期','下载来源省市汇总'],standardRows,{primary:true,urls:[2,14],dates:[11,12,23,25],times:[13],widths:{0:27,1:54,2:23,3:39,4:35,5:22,6:10,7:12,8:29,9:26,10:48,11:15,12:15,13:24,14:16,15:14,16:53,17:100,18:22,19:16,20:90,21:30,22:70,23:15,24:110,25:18,26:60},rowHeight:56});
main.getRange('D4').values=[['已验完整PDF链接']];main.getRange('E4').values=[[full.length]];main.getRange('D5').values=[['81条基线登记']];main.getRange('E5').values=[[model.coverage.baseline_records_registered]];main.getRange('G4').values=[['全集分母未知']];main.getRange('I4').values=[['历史目录不证明2026现行性']];
if(checkpoint==='1510'){
  const regionLinks=[...model.links].sort((a,b)=>Number(!a.download_source_region.province)-Number(!b.download_source_region.province)||(a.download_source_region.province??'').localeCompare(b.download_source_region.province??'','zh-CN')||(a.download_source_region.city??'').localeCompare(b.download_source_region.city??'','zh-CN')||a.link_id.localeCompare(b.link_id));
  const rows=regionLinks.map(l=>{const r=l.download_source_region;return [r.province??'来源省份待核',r.city??'来源城市待核',r.source_entity??'来源主体待核',l.standard_ids.map(id=>standards.get(id)?.standard_number).join('\n'),l.standard_ids.map(id=>standards.get(id)?.name).join('\n'),l.final_url??l.requested_url,l.source_page,l.download_status,l.recommendation,l.body_reading_recommendation??'',r.region_status,regionBasisText(r),r.region_evidence_ids.join('\n'),l.link_id,l.standard_ids.join('\n')];});
  makeSheet('地区下载索引','按资料下载来源主体省市分类',['来源省份','来源城市/地区','来源主体','规范编号','规范名称','下载/候选链接','来源详情页','下载核验状态','全文推荐等级','正文阅读等级','地区核实状态','地区依据','地区证据ID','链接ID','版本ID'],rows,{primary:true,urls:[5,6],widths:{0:22,1:24,2:55,3:32,4:65,5:18,6:18,7:55,8:17,9:50,10:23,11:110,12:65,13:28,14:65},rowHeight:72});
}
const pdfRow=l=>[l.verified_standard_ids.map(id=>standards.get(id)?.standard_number).join(', '),l.verified_standard_ids.map(id=>standards.get(id)?.name).join(', '),l.final_url,l.recommendation,l.recommendation_reason,l.pages,l.pdf_bytes===null?null:l.pdf_bytes/1048576,l.search_copy,l.bookmarks,l.bookmark_navigation,l.clickable_toc,l.clarity,l.completeness,stamp(l.checked_at),l.source_page,l.link_id,l.sha256,l.local_audit_file,l.verified_standard_ids.join(', ')];
const pdfHeaders=['规范编号','规范名称','最终PDF链接','推荐等级','推荐理由','页数','大小（MiB）','正文搜索复制','书签总数','书签跳转/标签类型','可点击目录','清晰度','完整性证据（AI审查判断）','核验时间','来源详情页','链接ID','SHA256','本地核验路径','已确认版本ID'];
const pdfLayout={primary:true,urls:[2,14],times:[13],widths:{0:27,1:54,2:18,3:14,4:100,5:10,6:16,7:90,8:14,9:50,10:85,11:90,12:110,13:24,14:18,15:28,16:70,17:100,18:55},rowHeight:88};
const completeRows=full.map(pdfRow);
makeSheet('已验完整PDF','已确认版本与完整性的正式 PDF',pdfHeaders,completeRows,pdfLayout);
makeSheet('完整草案PDF','内容完整的草案，非正式标准全文',[...pdfHeaders,'稿型','草案内容完整','正式全文集合'],drafts.map(l=>[...pdfRow(l),l.version_class??l.draft_stage,'内容完整（AI审查判断）','不计正式完整PDF']),{...pdfLayout,widths:{...pdfLayout.widths,19:20,20:35,21:30}});
const linkRows=model.links.map(l=>[l.link_id,l.standard_ids.join('\n'),l.candidate_ids?.join(', ')??l.candidate_id??'',l.source_page,l.requested_url,l.final_url,l.download_status,cellText(l.access_restriction),l.url_expiry,stamp(l.checked_at),l.http_status,l.pages,l.pdf_bytes,l.pdf_bytes===null?null:l.pdf_bytes/1048576,l.sha256,cellText(l.parse_ok),l.version_match,l.version_verified===true?'已确认':'未确认',l.complete_pdf?'已验完整':'待核/不完整',l.completeness,l.recommendation,l.recommendation_reason,cellText(l.text_layer),l.search_copy,l.bookmarks,l.bookmark_navigation,l.clickable_toc,l.clarity,l.page_order,l.cropping_rotation,l.watermark,cellText(l.encrypted),l.audit_evidence_paths.join('\n'),l.local_audit_file,l.check_history.map(h=>`${h.checked_at} ${h.outcome}`).join('\n'),l.notes.join('\n'),l.active?'保留':'停用',l.verified_standard_ids?.join(', ')??'',l.requested_url,l.final_url]);
const anomalyText=value=>Array.isArray(value)?value.map(v=>typeof v==='object'?`PDF${(v.pdf_pages??[]).join('/')}：${v.observed??JSON.stringify(v)}`:String(v)).join('\n'):cellText(value);
linkRows.forEach((row,i)=>{const l=model.links[i];if(l.draft_content_complete)row[18]='完整草案（非正式全文）';row.push(l.version_class??l.draft_stage??'',l.draft_content_complete?'内容完整（草案）':'',l.quality_statement_type??'',l.body_reading_recommendation??'',l.body_searchable??'',l.body_text_layer??'',anomalyText(l.quality_anomalies));});
linkRows.forEach((row,i)=>{const r=model.links[i].download_source_region;row.push(r?.province??'',r?.city??'',r?.source_entity??'',r?.region_status??'尚未分类',r?.region_evidence_ids.join('\n')??'',regionBasisText(r));});
makeSheet('链接明细','全部候选与实际核验链接', ['链接ID','关联版本ID','候选ID','来源详情页','请求链接','最终链接','下载状态','权限状态','过期情况','核验时间','HTTP状态','页数','文件字节数','大小（MiB）','SHA256','解析结果','版本匹配证据','版本确认','完整性状态','完整性证据','全文推荐等级','全文推荐理由','文本层存在','正文搜索复制','章节书签数','书签跳转','目录点击','清晰度','页序','裁边与旋转','水印','加密','核验证据路径','本地核验文件','逐次检查历史','问题备注','维护状态','已确认适用版本','请求URL原文','最终URL原文','稿型（审查）','草案内容完整','评级陈述类型','正文阅读等级（仅已收录范围）','正文可检索（独立字段）','正文文本层（独立字段）','质量异常（原审查）','下载来源省份','下载来源城市/地区','下载来源主体','来源地区核实状态','来源地区证据ID','来源地区依据'],linkRows,{urls:[3,4,5],times:[9],widths:{0:28,1:55,2:30,3:18,4:18,5:18,6:40,7:48,8:44,9:24,10:13,11:10,12:19,13:16,14:70,15:44,16:90,17:15,18:32,19:125,20:16,21:110,22:16,23:110,24:15,25:65,26:100,27:110,28:70,29:70,30:65,31:12,32:130,33:130,34:130,35:110,36:12,37:55,38:170,39:170,40:26,41:28,42:60,43:50,44:30,45:100,46:130,47:22,48:24,49:55,50:22,51:65,52:110},rowHeight:96});
const seedRows=original.map(r=>[r.seed_id,r.standard_id,r.original_name,r.standard_number,r.year,r.draft_stage,r.topic_group_name,r.source_annotation,r.source_id,r.candidate_url,r.link_id,r.parsing_issues.join('\n')]);
makeSheet('原始映射','81 条原始记录的不可丢失映射', ['原记录ID','规范稳定ID','原始文件名','解析编号','解析年份','稿型','专业分组','原网页标注','原始source_id','候选下载链接','链接ID','识别问题'],seedRows,{urls:[9],widths:{0:14,1:55,2:100,3:27,4:14,5:22,6:30,7:20,8:75,9:18,10:28,11:90},rowHeight:56});
const issueRows=issues.map(i=>[i.issue_id,i.standard_id??i.draft_id??i.entry_id??'',standards.get(i.standard_id)?.standard_number??'',standards.get(i.standard_id)?.name??i.name??'',i.seed_ids.join(', '),i.type,i.status,i.priority,i.action,i.source_ids.join(', ')]);
makeSheet('待查与问题','缺全文与元数据冲突队列', ['问题ID','规范稳定ID','规范编号','规范名称','原记录ID','问题类别','处理状态','优先级','待查动作','证据ID'],issueRows,{widths:{0:28,1:55,2:27,3:54,4:22,5:30,6:14,7:14,8:140,9:100},rowHeight:58});
const evidenceRows=evidence.map(e=>[e.evidence_id,e.standard_id,e.kind,e.statement_type,e.source_id,e.source_url,e.source_page??'',e.observed_at??'',e.source_text??'',e.claim??'',e.applicability??'',e.evidence_paths?.join('\n')??'',e.pdf_page_one_based??'',e.source_printed_page??'',e.source_category??'',e.source_location?JSON.stringify(e.source_location):'',dateValue(e.webpage_published_date)]);
makeSheet('状态与来源依据','状态、目录与独立审查证据', ['证据ID','规范稳定ID','证据种类','陈述类型','source_id','来源URL','来源详情页','来源记录或检查时间','原文摘录/原始行','证据说明','适用日期与限制','核验证据路径','PDF顺序页','印刷页码','来源层级','HTML/表格实际定位','网页发布时间（非标准发布日）'],evidenceRows,{urls:[5,6],dates:[16],widths:{0:28,1:55,2:28,3:32,4:75,5:18,6:18,7:35,8:125,9:130,10:110,11:130,12:16,13:16,14:40,15:110,16:28},rowHeight:78});
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
if(has1330)notes.push(['102版次','CECS102:2002（2012年版）单列E2012身份，编号年份仍为2002；无版次副本不被假定为初版，两者未完成版次匹配不共享下载链接。'],['公告与全文',`${model.coverage.independent_audit_results}条实GET审查中包含1条796发布公告元数据；仅1页公告不计完整标准，年份冲突仍保留。`]);
if(has1350)notes.push(['完整草案PDF链接数',drafts.length],['草案完整性','内容完整的报批稿、送审稿等单列在完整草案PDF，按实际稿型显示；draft_content_complete表示内容闭合，complete_pdf只用于正式完整集合，不能据false改写为内容待核。'],['评级陈述类型','完整性、可读性与推荐等级为AI基于实测的审查判断，不是出版方认证；HTTP、字节、页数与原文公告分别作为观测/原文事实。'],['旧22废止依据','CECS22:2005据实得出版物内协会第2185号公告，2025-04-01同时废止；PDF顺序第5页无印刷页码，双审目视。旧PDF继续保留，2024版2026现行性仍未知。'],['R07目录去重',`137条直接目录观测，135身份；对当时冻结811身份净增${model.coverage.round07_directory_new_identities_against_frozen_master}。全部目录现${model.coverage.authority_records}条不同来源行，含${model.coverage.directory_observation_count}次历史及新观测，不用相对58目录的85当净增。`],['608题名更正','仅608-2019按湖北PDF顺序22/印刷21的直接原格更名为绿色建筑运营后评估标准；旧后评价索引题名与证据保留，10065/10066不改名。']);
if(has1410)notes.push(['R08目录去重',`新疆新增165来源行/156号年，对全部旧889身份净增${model.coverage.round08_directory_new_identities_against_frozen_master}；19条已登记重核链接不重复计数。15条编号/年份未闭合独立列问题，不自动补年或混入原3条在编。`],['同号异名冲突','1137-2022与22-2012保留全部原图题名和物理/印刷页，不按行序或目录草案状态选择正式题名。'],['平台DOM当前标注','实际匿名观察10条/1页，其中新增身份1；现行仅表示全国团体平台标注及检查日，不是具体工程适用性确认；2960徽章与前100上限不是已采集分母。公布/发布/实施分存。'],['Word元数据路线','DOC/DOCX附件只登记元数据、格式与来源，未读取原文，不作为PDF链接或完整PDF。'],['正式完整件限制','212/235/122/17评B；122/17为按本件目录范围闭合的数字重排副本，不宣称出版社原页式；122页脚局部字形裁切保留。333/287仍C，不能把287因占位号直接定草案。']);
if(checkpoint==='1510'){
  const r=model.coverage.download_source_region_counts;
  notes[0][1]='工程相关CECS均收集，房屋结构优先；保留专业分组和适用范围，持续增补，不宣称穷尽。';
  notes.push(['资料下载来源地区','按下载主体的公开地址分类省市；不是规范适用地区。每条链接独立分类，同规范多来源可跨地区；无下载链接不借用目录所在地。source_id: USER-20261017-CECS-DOWNLOAD-SOURCE-REGION'],['地区核实覆盖',`${r.total_links}条下载/候选链接；省级有证据${r.province_evidenced_links}，省市均有证据${r.fully_identified_links}，部分核实${r.partial_links}，待核${r.pending_links}。证据和官网地址见地区下载索引。`],['天津来源边界','本批尚无明确的天津下载主体地址证据，不凭域名或销售区域猜归属；不表示全库没有天津来源。'],['R09—R11目录',`${model.coverage.recent_directory_rows_including_gaps}原始行，${model.coverage.recent_directory_resolved_rows}完整号年行，${model.coverage.recent_directory_unique_identities}唯一号年；对旧1008身份净增${model.coverage.recent_directory_new_identities_against_frozen_master}。3条图集短年码留问题，不补年。`],['月度日期冲突','R09中33行存在页标题2024年9月与表格实施2025-09-01冲突；全部原值分层保留并列问题，不静默选择实施日期。网页发布时间不作标准发布日期。'],['CECS69旧版废止','据第85号公告，CECS69:94于2011-10-01同时废止；证据在2011版PDF顺序第2页左半、无印刷页码。PDF第16页右半印25仅为批准日期/公告号旁证。2011版在2026是否现行仍待核。'],['全文与正文等级','全文推荐等级与仅已收录正文阅读等级分列。1555浏览版全文D、已收录正文B；200缺实质说明且100mm漏mm，全文D，不补造正文B。'],['草案阶段与书签','肯定稿型证据才确定报批/送审/征求意见，未见草案等否定语不触发；占位编号无阶段证据标阶段待核。书签总数包含前置题名或页码分组，不能全部称章节。']);
}
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
