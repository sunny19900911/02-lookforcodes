import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';

// Independent release validator. Reads selected sharing inputs only; never opens
// the original G2 input, raw water-MEP responses, v1 sharing inputs, or R08 files.
const out = import.meta.dirname;
const root = path.resolve(out, '..');
const outputPath = path.join(out, 'freeze-1350-validation.json');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const normalizePath = p => String(p).replaceAll('\\', '/');
const cache = new Map();
const checks = [];
const failures = [];
const transientPaths = new Set();
const report = { checkpoint: '1350', checked_at: new Date().toISOString(), hashes: {}, counts: {}, checks, failures };
const rawG2 = 'search/g2-public-routes/round02-candidates.json';
const waterAllow = new Set([
  'search/round07-broad-attachments/water-mep/candidates-round07-water-mep-share-v2.json',
  'search/round07-broad-attachments/water-mep/query-ledger-r07-water-mep-share.json',
  'search/round07-broad-attachments/water-mep/addendum-r07-water-mep.json',
  'search/round07-broad-attachments/water-mep/share-review-v2.json',
]);
const forbidden = p => p === rawG2 || /(?:^|[/_.-])(?:r08|round08)(?:[/_.-]|$)/i.test(p)
  || (p.includes('/water-mep/') && !waterAllow.has(p));
let activeReadPath = '/runtime';

async function readBytes(relative) {
  const rel = normalizePath(relative);
  activeReadPath = '/' + rel;
  assert.ok(!forbidden(rel));
  const absolute = path.resolve(root, rel);
  const within = path.relative(root, absolute);
  assert.ok(within && !within.startsWith('..') && !path.isAbsolute(within));
  if (!cache.has(rel)) cache.set(rel, await fs.readFile(absolute));
  return cache.get(rel);
}
async function readJson(relative) {
  return JSON.parse((await readBytes(relative)).toString('utf8').replace(/^\uFEFF/, ''));
}
function check(pointer, fn) {
  try { fn(); checks.push({ path: pointer, passed: true }); }
  catch { checks.push({ path: pointer, passed: false }); failures.push({ path: pointer }); }
}
const esc = key => String(key).replaceAll('~', '~0').replaceAll('/', '~1');
// No matched text or query value is retained, even when a check fails.
const temporaryQuery = /[?&](?:amp;)?(?:uhash|access_token|auth_token|session_token|jsessionid|phpsessid|token|signature|sign|expires|ossaccesskeyid|awsaccesskeyid|x-amz-[^=&\s]+|x-oss-[^=&\s]+)=/i;
function scanTransient(value, pointer) {
  if (typeof value === 'string') {
    let decoded = value;
    for (let round = 0; round < 3; round++) {
      if (temporaryQuery.test(decoded)) transientPaths.add(pointer);
      try { const next = decodeURIComponent(decoded); if (next === decoded) break; decoded = next; }
      catch { break; }
    }
  } else if (Array.isArray(value)) value.forEach((v, i) => scanTransient(v, pointer + '/' + i));
  else if (value && typeof value === 'object') for (const [key, v] of Object.entries(value)) scanTransient(v, pointer + '/' + esc(key));
}
function directoryId(row) {
  const code = String(row.standard_number ?? '').normalize('NFKC').replaceAll('∕', '/');
  const family = /CECS\s*-\s*CREA/i.test(code) ? 'CECS-CREA' : /CECS\s*-\s*CBIMU/i.test(code) ? 'CECS-CBIMU' : 'CECS';
  const number = /^\d+$/.test(String(row.number)) ? String(Number(row.number)) : String(row.number);
  assert.ok(number && /^(19|20)\d{2}$/.test(String(row.year)));
  return family + '-' + number.replaceAll(':', '_') + '-' + row.year + '-FORMAL';
}
function observationCount(row) { return 1 + (row.previous_observations ?? []).reduce((n, r) => n + observationCount(r), 0); }
const draftPattern = /报批|征求意见|送审|草案/;
const aiJudgment = value => /^AI推断(?:[（(]|$)/.test(String(value ?? ''));

try {
  const masterBytes = await readBytes('catalog/cecs-master.json');
  const master = JSON.parse(masterBytes.toString('utf8'));
  const baseline = await readJson('catalog/history/master-before-1350.json');
  const standards = new Map(master.standards.map(s => [s.standard_id, s]));
  const links = new Map(master.links.map(l => [l.link_id, l]));
  const evidence = new Map(master.evidence.map(e => [e.evidence_id, e]));
  report.hashes.master_sha256 = sha(masterBytes);
  report.hashes.xlsx_sha256 = sha(await readBytes('catalog/CECS可下载PDF总表.xlsx'));
  report.snapshot_generated_at = master.generated_at;
  check('/scope/checkpoint', () => assert.equal(master.scope.checkpoint, '1350'));
  check('/standards/count', () => assert.equal(master.standards.length, 889));
  check('/identity/unique_ids', () => { assert.equal(standards.size, master.standards.length); assert.equal(links.size, master.links.length); });
  check('/coverage/arrays_consistent', () => {
    assert.equal(master.coverage.registered_standard_versions, master.standards.length);
    assert.equal(master.coverage.registered_links, master.links.length);
    assert.equal(master.coverage.independent_audit_results, master.external.audit.length);
  });

  const manifests = [
    'search/freeze-inputs-1320.json', 'search/freeze-inputs-1330.json',
    'search/freeze-inputs-1340.json', 'search/freeze-inputs-1340-water-mep-addendum-v2.json',
    'search/freeze-inputs-g2-round02-share-1350.json',
  ];
  const expected = new Map();
  for (const file of manifests) for (const entry of (await readJson(file)).files) {
    const rel = normalizePath(entry.path);
    check('/manifests/duplicate/' + esc(rel), () => { if (expected.has(rel)) assert.equal(expected.get(rel).sha256, entry.sha256); });
    expected.set(rel, entry);
  }
  expected.delete(rawG2); // inspect its manifest annotation only; never read it.
  const selected = master.external.search_manifest.files;
  const selectedByPath = new Map(selected.map(e => [normalizePath(e.path), e]));
  const receipts = new Map(master.external_inputs.map(e => [normalizePath(e.path), e]));
  check('/selected_files/count_and_set', () => {
    assert.equal(expected.size, 47); assert.equal(selected.length, 47); assert.equal(selectedByPath.size, 47);
    assert.deepEqual([...selectedByPath.keys()].sort(), [...expected.keys()].sort());
    assert.equal(master.external.search_manifest.checkpoint, '1350');
    for (const rel of selectedByPath.keys()) assert.ok(!forbidden(rel));
  });
  for (const [rel, entry] of selectedByPath) {
    if (forbidden(rel)) { failures.push({ path: '/selected_files/' + esc(rel) }); continue; }
    const bytes = await readBytes(rel);
    check('/selected_files/receipt/' + esc(rel), () => {
      assert.equal(sha(bytes), entry.sha256); assert.equal(bytes.length, entry.bytes);
      assert.equal(entry.sha256, expected.get(rel)?.sha256); assert.equal(entry.bytes, expected.get(rel)?.bytes);
      assert.equal(receipts.get(rel)?.sha256, entry.sha256);
    });
    if (rel.endsWith('.json')) scanTransient(JSON.parse(bytes.toString('utf8').replace(/^\uFEFF/, '')), '/selected_files/' + esc(rel));
    else scanTransient(bytes.toString('utf8'), '/selected_files/' + esc(rel));
  }
  scanTransient(master, '/master');
  check('/sharing/transient_query', () => assert.equal(transientPaths.size, 0));

  const auditBytes = await readBytes('pdf-audit/audit-results.json');
  const audits = JSON.parse(auditBytes.toString('utf8')).results;
  const freeze = await readJson('pdf-audit/freeze-1350-receipt.json');
  const prior = (await readJson('pdf-audit/audit-results-freeze-1330.json')).results;
  const auditById = new Map(audits.map(a => [a.audit_id ?? a.candidate_id, a]));
  const pendingBytes = await readBytes('pdf-audit/audit-pending-round05-freeze-1350.json');
  const pending = JSON.parse(pendingBytes.toString('utf8')).results;
  const pendingReceipt = await readJson('pdf-audit/audit-round05-receipt-1350.json');
  report.hashes.audit_sha256 = sha(auditBytes);
  report.hashes.pending_audit_sha256 = sha(pendingBytes);
  check('/audit/freeze', () => {
    assert.equal(audits.length, 40); assert.equal(auditById.size, 40); assert.equal(freeze.result_count, 40);
    assert.equal(freeze.sha256, sha(auditBytes)); assert.equal(receipts.get('pdf-audit/audit-results.json')?.sha256, sha(auditBytes));
    assert.deepEqual(master.external.audit, audits);
  });
  check('/audit/pending_seven', () => {
    assert.equal(pending.length, 7); assert.equal(pendingReceipt.sha256, sha(pendingBytes));
    assert.equal(sha(pendingBytes), '90081712aea2c2ddb78202101d3e31753828ed6e663af87a139ec9e007e7dcf8');
    for (const a of pending) {
      const canonical = auditById.get(a.audit_id ?? a.candidate_id);
      assert.ok(canonical);
      const { audit_history: pendingHistory = [], ...pendingBody } = a;
      const { audit_history: canonicalHistory = [], ...canonicalBody } = canonical;
      assert.deepEqual(canonicalBody, pendingBody);
      assert.equal(canonicalHistory.length, pendingHistory.length + 1);
      assert.deepEqual(canonicalHistory.slice(0, pendingHistory.length), pendingHistory);
      assert.deepEqual(canonicalHistory.at(-1), {
        checked_at: freeze.frozen_at,
        method: '主控明确批准13:50固定七条GET回灌；原始审查及证据字段全部保留',
        outcome: '新增候选实测；草案内容完整与正式完整计数分开',
      });
    }
  });
  check('/audit/old_33_unchanged', () => {
    assert.equal(prior.length, 33);
    for (const a of prior) assert.deepEqual(auditById.get(a.audit_id ?? a.candidate_id), a);
  });

  const full = master.links.filter(l => l.complete_pdf);
  const formalVersions = new Set(full.flatMap(l => l.verified_standard_ids ?? []));
  const fullHashes = new Set(full.map(l => l.sha256));
  check('/formal/counts', () => {
    assert.equal(full.length, 10); assert.equal(formalVersions.size, 8); assert.equal(fullHashes.size, 8);
    assert.equal(master.coverage.verified_complete_pdf_links, 10);
    assert.equal(master.coverage.verified_complete_standard_versions, 8);
    assert.equal(master.coverage.verified_complete_unique_sha256, 8);
  });
  check('/formal/gates_and_relations', () => {
    for (const l of master.links) {
      assert.ok(l.standard_ids.length);
      for (const id of l.standard_ids) assert.ok(standards.get(id)?.link_ids.includes(l.link_id));
      if (!l.complete_pdf) continue;
      assert.equal(l.active, true); assert.equal(l.version_verified, true); assert.equal(l.audit_result?.complete_pdf, true);
      assert.equal(l.audit_result?.version_verified, true); assert.notEqual(l.metadata_only, true); assert.notEqual(l.audit_result?.metadata_only, true);
      assert.ok(!draftPattern.test(String(l.version_class ?? '') + ' ' + String(l.draft_stage ?? '')));
      assert.ok(l.verified_standard_ids.length); assert.ok(l.sha256 && l.pages > 0 && l.pdf_bytes > 0 && l.final_url && l.audit_evidence_paths.length);
      for (const id of l.verified_standard_ids) assert.ok(standards.has(id) && l.standard_ids.includes(id));
    }
    for (const s of master.standards) {
      for (const id of s.link_ids) assert.ok(links.get(id)?.standard_ids.includes(s.standard_id));
      if (s.best_link_id) { const l = links.get(s.best_link_id); assert.ok(l?.active && l.complete_pdf && l.version_verified && l.verified_standard_ids.includes(s.standard_id)); }
    }
  });
  const drafts = master.links.filter(l => l.draft_content_complete);
  check('/draft/one_complete_approval', () => {
    assert.equal(drafts.length, 1);
    const l = drafts[0]; assert.equal(l.version_class, '报批稿'); assert.equal(l.version_verified, true); assert.equal(l.complete_pdf, false);
    assert.equal(l.pages, 84); assert.equal(l.active, true); assert.equal(l.http_status, 200); assert.ok(l.final_url && l.sha256);
    assert.equal(l.audit_result.draft_content_complete, true); assert.equal(l.audit_result.complete_pdf, false);
    assert.equal(l.verified_standard_ids.length, 1);
    const s = standards.get(l.verified_standard_ids[0]); assert.equal(s.best_draft_link_id, l.link_id); assert.equal(s.best_link_id, null);
    assert.equal(s.version_class, '报批稿'); assert.ok(!formalVersions.has(s.standard_id));
    assert.equal(master.standards.filter(s => s.best_draft_link_id).length, 1);
  });
  check('/evidence/quality_is_ai_inference', () => {
    const quality = master.evidence.filter(e => e.kind === 'PDF完整性与阅读质量判断');
    assert.equal(quality.length, 40);
    for (const e of quality) assert.ok(aiJudgment(e.statement_type));
    for (const l of master.links.filter(l => l.audit_id)) assert.ok(aiJudgment(l.quality_statement_type));
    for (const a of audits) assert.ok(quality.some(e => e.source_id === a.audit_id));
  });

  const directoryRows = master.external.directories;
  const round07 = master.external.directory_round07.records;
  const roundIds = new Set(round07.map(directoryId));
  const baselineIds = new Set(baseline.standards.map(s => s.standard_id));
  check('/directory/counts_and_net_additions', () => {
    assert.equal(directoryRows.length, 798); assert.equal(new Set(directoryRows.map(r => r.source_id)).size, 798);
    assert.equal(directoryRows.reduce((n, r) => n + observationCount(r), 0), 847);
    assert.equal(master.coverage.authority_records, 798); assert.equal(master.coverage.directory_observation_count, 847);
    assert.equal(round07.length, 137); assert.equal(roundIds.size, 135);
    assert.equal([...roundIds].filter(id => !baselineIds.has(id)).length, 72);
    assert.equal(master.standards.filter(s => !baselineIds.has(s.standard_id)).length, 78);
    assert.equal(master.coverage.round07_directory_unique_identities, 135);
    assert.equal(master.coverage.round07_directory_new_identities_against_frozen_master, 72);
    assert.equal(master.coverage.merge_net_new_identities, 78);
  });
  check('/directory/608_correction_and_unchanged_names', () => {
    const s = standards.get('CECS-608-2019-FORMAL'); assert.equal(s.name, '绿色建筑运营后评估标准');
    assert.ok(s.name_variants.includes('绿色建筑运营后评价标准'));
    assert.ok(s.name_correction_events.some(e => e.old_name === '绿色建筑运营后评价标准' && e.new_name === s.name && evidence.has(e.evidence_id)));
    for (const id of ['CECS-10065-2019-FORMAL', 'CECS-10066-2019-FORMAL']) assert.equal(standards.get(id).name, baseline.standards.find(s => s.standard_id === id).name);
  });
  check('/metadata/four_no_download_routes', () => {
    for (const id of ['CECS-10267-2023-FORMAL', 'CECS-10309-2023-FORMAL', 'CECS-10222-2022-FORMAL', 'CECS-10403-2024-FORMAL']) {
      assert.ok(standards.has(id)); assert.equal(standards.get(id).link_ids.length, 0); assert.equal(standards.get(id).best_link_id, null);
    }
  });
  check('/identity/102_edition', () => {
    const old = standards.get('CECS-102-2002-FORMAL'), ed = standards.get('CECS-102-2002-FORMAL-E2012');
    assert.equal(ed.year, 2002); assert.equal(ed.edition_label, '2012年版'); assert.equal(ed.published_date, null); assert.equal(ed.effective_date, null);
    assert.ok(ed.metadata_date_layers.some(l => l.context.includes('网页') && l.effective_date === '2012-04-24'));
    assert.ok(ed.metadata_date_layers.some(l => l.context.includes('书内') && l.effective_date === '2003-03-01'));
    assert.ok(old.issues.some(s => s.includes('未核版次'))); assert.ok(!old.link_ids.some(id => ed.link_ids.includes(id)));
    if (old.best_link_id) assert.notEqual(old.best_link_id, ed.best_link_id);
  });
  check('/status/22_repeal_and_new_unknown', () => {
    const old = standards.get('CECS-22-2005-FORMAL'), next = standards.get('CECS-22-2024-FORMAL');
    assert.ok(old.current_status.includes('已废止')); assert.equal(old.withdrawal_date, '2025-04-01'); assert.equal(old.replaced_by, next.standard_id);
    assert.ok(old.status_basis.includes('第5页') && old.status_basis.includes('PDF-CECS-2185-REPEAL-20261017'));
    const e = master.evidence.find(e => e.source_id === 'PDF-CECS-2185-REPEAL-20261017' && e.standard_id === old.standard_id);
    assert.ok(e && old.status_evidence_ids.includes(e.evidence_id)); assert.equal(e.pdf_page_one_based, 5); assert.equal(e.source_printed_page, null);
    assert.ok(next.current_status.startsWith('未知'));
  });
  check('/baseline/81_mapping_and_unnumbered_drafts', () => {
    const expectedIds = Array.from({ length: 81 }, (_, i) => 'S' + String(i + 1).padStart(3, '0'));
    assert.deepEqual(master.original_records.map(r => r.seed_id).sort(), expectedIds);
    for (const r of master.original_records) { assert.ok(standards.has(r.standard_id)); assert.ok(links.has(r.link_id)); }
    assert.equal(master.unresolved_drafts.length, 3);
    for (const d of master.unresolved_drafts) assert.ok(!standards.has(d.draft_id) && !master.standards.some(s => s.name === d.name));
  });
  report.counts = { standards: master.standards.length, links: master.links.length, audits: audits.length, selected_files: selected.length,
    original_records: master.original_records.length, formal_complete_links: full.length, formal_complete_versions: formalVersions.size,
    formal_complete_sha256: fullHashes.size, complete_drafts: drafts.length, directory_unique_source_rows: directoryRows.length,
    directory_observations: directoryRows.reduce((n, r) => n + observationCount(r), 0), round07_unique_identities: roundIds.size,
    directory_net_new_identities: [...roundIds].filter(id => !baselineIds.has(id)).length, total_net_new_identities: master.standards.filter(s => !baselineIds.has(s.standard_id)).length };
  const finalMasterHash = sha(await fs.readFile(path.join(out, 'cecs-master.json')));
  check('/snapshot/unchanged_during_validation', () => assert.equal(finalMasterHash, report.hashes.master_sha256));
} catch {
  failures.push({ path: activeReadPath });
}
report.transient_query_paths = [...transientPaths];
report.passed = failures.length === 0;
await fs.writeFile(outputPath, JSON.stringify(report, null, 2));
console.log(JSON.stringify({ passed: report.passed, output: 'catalog/freeze-1350-validation.json', hashes: report.hashes, counts: report.counts, failures: report.failures, transient_query_paths: report.transient_query_paths }));
if (!report.passed) process.exitCode = 1;
