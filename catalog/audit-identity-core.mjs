import {inferVersionStage} from './version-stage-core.mjs';
// An announcement verifies a metadata document, never its title as a standard name.
export function createAuditIdentity(a,p){
  return {standard_number:p.published_code_candidate,name:a.metadata_only?(a.standard_name??'规范名称待核'):(a.name??p.name),year:p.year,version_stage:p.stage};
}

export function updateAuditIdentity(standard,a){
  if(!a.version_verified||a.metadata_only)return standard;
  if(a.name&&standard.name!==a.name){standard.name_variants=[...new Set([...(standard.name_variants??[]),standard.name,a.name])];standard.name=a.name;}
  if(standard.version_stage==='正式文本候选')standard.version_stage='正式版（封面核验）';
  return standard;
}

// Content completeness of a draft is independent of the formal-PDF collection.
export function auditCompletenessFields(a){
  const isDraft=inferVersionStage({text:`${a.standard_number??''} ${a.name??''}`,explicitStage:a.draft_stage,versionClass:a.version_class})!=='正式文本候选';
  return {
    version_class:a.version_class??null,
    draft_stage:a.draft_stage??null,
    draft_content_complete:a.draft_content_complete===true,
    body_reading_recommendation:a.body_reading_recommendation??null,
    body_searchable:a.body_searchable??null,
    body_text_layer:a.body_text_layer??null,
    quality_anomalies:a.quality_anomalies??null,
    complete_pdf:a.complete_pdf===true&&a.version_verified===true&&!a.metadata_only&&!isDraft,
    quality_statement_type:'AI推断（基于独立GET、解析与目视检查）',
  };
}

// A placeholder code can become visible during audit without creating a new draft.
// Require the same candidate, URL-linked record and title; numbered versions never merge here.
export function matchUnnumberedAuditCandidate(a,p,link,standards){
  if(p.number&&p.number!=='XXX')return null;
  if(!a.candidate_id||!link?.candidate_ids?.includes(a.candidate_id))return null;
  const title=s=>String(s??'').normalize('NFKC').replace(/\s+/g,'');
  const matches=link.standard_ids.map(id=>standards.get(id)).filter(s=>s&&/^CECS-UNRESOLVED-/.test(s.standard_id)&&title(s.name)===title(a.name));
  return matches.length===1?matches[0].standard_id:null;
}
