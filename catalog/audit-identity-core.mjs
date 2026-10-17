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
