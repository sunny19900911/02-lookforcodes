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
  const isDraft=/报批|征求意见|送审|草案/.test(`${a.version_class??''} ${a.draft_stage??''}`);
  return {
    version_class:a.version_class??null,
    draft_stage:a.draft_stage??null,
    draft_content_complete:a.draft_content_complete===true,
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
