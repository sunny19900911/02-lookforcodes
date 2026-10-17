import fs from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {inferVersionStage} from './version-stage-core.mjs';

const formal = '正式文本候选';
const unknown = '草案（阶段待核）';
const audit = JSON.parse(fs.readFileSync(new URL('../pdf-audit/audit-pending-round09-freeze-1450-v2.json', import.meta.url), 'utf8'));
const previous = JSON.parse(fs.readFileSync(new URL('../pdf-audit/audit-results-freeze-1410.json', import.meta.url), 'utf8'));
const inferAudit = a => inferVersionStage({text: `${a.standard_number ?? ''} ${a.name ?? ''}`, explicitStage: a.draft_stage, versionClass: a.version_class});

test('1555 formal browser copy is not a draft because no draft mark was observed', () => {
  const a = audit.results.find(a => a.candidate_id === 'R11-1555-2024-FAIUSR');
  assert.match(a.draft_stage, /未见草案/);
  assert.equal(inferAudit(a), formal);
});

test('200 reflowed copy and 287 formally numbered layout remain formal candidates', () => {
  assert.equal(inferAudit(audit.results.find(a => a.candidate_id === 'R11-200-2006-DLSSYHT')), formal);
  assert.equal(inferAudit(previous.results.find(a => a.candidate_id === 'R08-WH-003')), formal);
});

test('243 non-draft statement and unresolved prefabrication prose do not invent phases',()=>{
  const r09=JSON.parse(fs.readFileSync(new URL('../pdf-audit/audit-pending-round07-freeze-1430.json',import.meta.url),'utf8'));
  const irrigation=r09.results.find(a=>a.candidate_id==='R09-WM-001');
  assert.equal(inferAudit(irrigation),formal);
  assert.equal(inferVersionStage({text:'T/CECS XXX-2025 装配式低碳建筑',explicitStage:'具体征求/送审/报批阶段未核'}),unknown);
});

test('audited complete approval and review drafts retain their actual phases', () => {
  assert.equal(inferAudit(previous.results.find(a => a.candidate_id === 'R07-G5-DRAFT-ZERO-2025')), '报批稿');
  assert.equal(inferAudit(previous.results.find(a => a.candidate_id === 'R08-CNASS-DRAFT-INDUSTRIAL-CONVERSION')), '送审稿');
});

test('affirmative filenames and cover observations can establish the phase', () => {
  assert.equal(inferVersionStage({text: 'TCECS XXX-202X 建筑结构技术标准（征求意见稿）.pdf'}), '征求意见稿');
  assert.equal(inferVersionStage({text: '建筑结构标准-征求意见.pdf'}), '征求意见稿');
  assert.equal(inferVersionStage({explicitStage: '公开搜索索引封面写征求意见稿、编号占位，完整性未核'}), '征求意见稿');
  assert.equal(inferVersionStage({explicitStage: '封面为报批稿；非正式标准全文'}), '报批稿');
});

test('placeholder alone never invents a consultation phase', () => {
  for (const text of ['T/CECS XXX-202X 建筑结构标准', 'T/CECS ××××-2025 建筑结构标准', 'T/CECS 123-20XX 标准']) {
    assert.equal(inferVersionStage({text}), unknown);
  }
  assert.equal(inferVersionStage({explicitStage: '具体征求意见/报批阶段待核'}), unknown);
  assert.equal(inferVersionStage({versionClass: '草案（阶段待核）'}), unknown);
});

test('negative explanations do not establish a draft phase', () => {
  for (const explicitStage of ['未见草案阶段标识，不据此证明出版终稿一致', '非报批稿', '不作为草案', '未见征求意见稿标识', '不确定是否送审稿']) {
    assert.equal(inferVersionStage({text: 'T/CECS 123-2024 建筑结构标准', explicitStage}), formal);
  }
  assert.equal(inferVersionStage({versionClass: '正式编号浏览版', explicitStage: '未见草案；具体报批阶段待核'}), formal);
  assert.equal(inferVersionStage({versionClass: '报批稿', explicitStage: '送审稿'}), '报批稿');
});
