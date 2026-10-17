import fs from 'node:fs';
import assert from 'node:assert/strict';
import test from 'node:test';
import {createAuditIdentity,updateAuditIdentity,auditCompletenessFields} from './audit-identity-core.mjs';
const audit=JSON.parse(fs.readFileSync(new URL('../pdf-audit/audit-results-freeze-1330.json',import.meta.url),'utf8'));
const announcement=audit.results.find(a=>a.audit_id==='AUD-796-ANNOUNCEMENT-QIXIN');
const code={published_code_candidate:'T/CECS 796-2021',year:2021,stage:'正式文本候选'};

test('verified announcement cannot name a newly created standard',()=>{
  assert.equal(announcement.metadata_only,true);assert.equal(announcement.version_verified,true);
  const standard=createAuditIdentity(announcement,code);
  assert.notEqual(standard.name,announcement.name);assert.doesNotMatch(standard.name,/发布公告/);
  assert.equal(standard.standard_number,'T/CECS 796-2021');assert.equal(standard.year,2021);
});
test('verified announcement cannot alter an existing standard name or draft stage',()=>{
  const before={name:'屋面结构雪荷载设计标准',version_stage:'正式性/年份冲突待核',name_variants:[]};
  const after=structuredClone(before);updateAuditIdentity(after,announcement);
  assert.deepEqual(after,before);
});
test('verified full standard still supplies its cover identity',()=>{
  const full=audit.results.find(a=>a.audit_id==='R03-G1-22-2024-ZGB-202603');
  assert.equal(full.complete_pdf,true);assert.equal(full.version_verified,true);
  const standard={name:'待核',version_stage:'正式文本候选'};updateAuditIdentity(standard,full);
  assert.equal(standard.name,'岩土锚杆技术规程');assert.equal(standard.version_stage,'正式版（封面核验）');
});

test('complete approval draft keeps its content fact outside formal complete PDFs',()=>{
  const round=JSON.parse(fs.readFileSync(new URL('../pdf-audit/audit-pending-round05-freeze-1350.json',import.meta.url),'utf8'));
  const a=round.results.find(a=>a.candidate_id==='R07-G5-DRAFT-ZERO-2025');
  const fields=auditCompletenessFields(a);
  assert.equal(fields.draft_content_complete,true);
  assert.equal(fields.version_class,'报批稿');assert.equal(fields.draft_stage,'报批稿');
  assert.equal(fields.complete_pdf,false);
  assert.equal(auditCompletenessFields({...a,complete_pdf:true}).complete_pdf,false);
});

test('metadata or unverified versions never qualify as formal complete PDFs',()=>{
  assert.equal(auditCompletenessFields({...announcement,complete_pdf:true}).complete_pdf,false);
  assert.equal(auditCompletenessFields({complete_pdf:true,version_verified:false}).complete_pdf,false);
  assert.equal(auditCompletenessFields({complete_pdf:true,version_verified:true,draft_stage:'正式发布版'}).complete_pdf,true);
});
