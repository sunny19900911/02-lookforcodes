import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';

// Independent, read-only semantic checks. Only the validation receipt is written
// when this file is run. Raw G2/water-MEP sources and R09 are never opened.
const out = import.meta.dirname, root = path.resolve(out, '..');
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const cleanPath = value => String(value).replaceAll('\\', '/');
const esc = value => String(value).replaceAll('~', '~0').replaceAll('/', '~1');
const cache = new Map(), checks = [], failures = [], transientPaths = new Set();
const report = { checkpoint: '1410', checked_at: new Date().toISOString(), hashes: {}, counts: {}, checks, failures };
const rawG2 = 'search/g2-public-routes/round02-candidates.json';
const waterAllow = new Set([
  'search/round07-broad-attachments/water-mep/candidates-round07-water-mep-share-v2.json',
  'search/round07-broad-attachments/water-mep/query-ledger-r07-water-mep-share.json',
  'search/round07-broad-attachments/water-mep/addendum-r07-water-mep.json',
  'search/round07-broad-attachments/water-mep/share-review-v2.json',
]);
const forbidden = p => p === rawG2 || /(?:^|[/_.-])(?:r09|round09)(?:[/_.-]|$)/i.test(p)
  || (p.includes('/water-mep/') && !waterAllow.has(p));
let activeReadPath = '/runtime';
async function bytes(relative) {
  const rel = cleanPath(relative); activeReadPath = '/' + rel; assert.ok(!forbidden(rel));
  const absolute = path.resolve(root, rel), within = path.relative(root, absolute);
  assert.ok(within && !within.startsWith('..') && !path.isAbsolute(within));
  if (!cache.has(rel)) cache.set(rel, await fs.readFile(absolute));
  return cache.get(rel);
}
async function json(relative) { return JSON.parse((await bytes(relative)).toString('utf8').replace(/^\uFEFF/, '')); }
function check(pointer, fn) {
  try { fn(); checks.push({ path: pointer, passed: true }); }
  catch { checks.push({ path: pointer, passed: false }); failures.push({ path: pointer }); }
}
const temporaryQuery = /[?&](?:amp;)?(?:uhash|access_token|auth_token|session_token|jsessionid|phpsessid|token|signature|sign|expires|ossaccesskeyid|awsaccesskeyid|x-amz-[^=&\s]+|x-oss-[^=&\s]+)=/i;
function scan(value, pointer) {
  if (typeof value === 'string') {
    let decoded = value;
    for (let i = 0; i < 3; i++) {
      if (temporaryQuery.test(decoded)) transientPaths.add(pointer);
      try { const next = decodeURIComponent(decoded); if (next === decoded) break; decoded = next; } catch { break; }
    }
  } else if (Array.isArray(value)) value.forEach((v, i) => scan(v, pointer + '/' + i));
  else if (value && typeof value === 'object') for (const [k, v] of Object.entries(value)) scan(v, pointer + '/' + esc(k));
}
function standardId(row) {
  const raw = String(row.standard_number ?? '').normalize('NFKC');
  const family = /CECS-CREA/i.test(raw) ? 'CECS-CREA' : /CECS-CBIMU/i.test(raw) ? 'CECS-CBIMU' : 'CECS';
  assert.match(String(row.number), /^\d+$/); assert.match(String(row.year), /^(19|20)\d{2}$/);
  return family + '-' + Number(row.number) + '-' + row.year + '-FORMAL';
}
function observations(row) { return 1 + (row.previous_observations ?? []).reduce((n, r) => n + observations(r), 0); }
const auditId = a => a.audit_id ?? a.candidate_id;
const auditUrls = a => [a.requested_url, a.download_url, a.final_url].filter(Boolean);
const ai = value => /^AI推断(?:[（(]|$)/.test(String(value ?? ''));
const draftPattern = /报批|送审|征求意见|草案/;

try {
  const masterBytes = await bytes('catalog/cecs-master.json'), master = JSON.parse(masterBytes.toString('utf8'));
  const baseline = await json('catalog/history/master-before-1410.json');
  const standards = new Map(master.standards.map(s => [s.standard_id, s]));
  const links = new Map(master.links.map(l => [l.link_id, l]));
  const evidence = new Map(master.evidence.map(e => [e.evidence_id, e]));
  const baselineIds = new Set(baseline.standards.map(s => s.standard_id));
  const baselineSources = new Set(baseline.external.directories.map(r => r.source_id));
  const newIds = new Set(master.standards.filter(s => !baselineIds.has(s.standard_id)).map(s => s.standard_id));
  report.snapshot_generated_at = master.generated_at;
  report.hashes.master_sha256 = sha(masterBytes);
  report.hashes.xlsx_sha256 = sha(await bytes('catalog/CECS可下载PDF总表.xlsx'));
  check('/scope/checkpoint', () => assert.equal(master.scope.checkpoint, '1410'));
  check('/identity/counts', () => {
    assert.equal(baseline.standards.length, 889); assert.equal(master.standards.length, 1008); assert.equal(newIds.size, 119);
    assert.equal(standards.size, master.standards.length); assert.equal(links.size, master.links.length);
    assert.equal(master.coverage.registered_standard_versions, master.standards.length);
    assert.equal(master.coverage.registered_links, master.links.length); assert.equal(master.coverage.merge_net_new_identities, 119);
  });

  const manifestPaths = [
    'search/freeze-inputs-1320.json', 'search/freeze-inputs-1330.json', 'search/freeze-inputs-1340.json',
    'search/freeze-inputs-1340-water-mep-addendum-v2.json', 'search/freeze-inputs-g2-round02-share-1350.json',
    'search/freeze-inputs-1400.json', 'search/master-authority/freeze-ttbz-p1-1410.json',
  ];
  const expected = new Map();
  for (const file of manifestPaths) for (const e of (await json(file)).files) {
    const rel = cleanPath(e.path);
    check('/manifests/duplicate/' + esc(rel), () => { if (expected.has(rel)) assert.equal(expected.get(rel).sha256, e.sha256); });
    expected.set(rel, e);
  }
  expected.delete(rawG2); // annotation remains in the manifest; its raw file is never read.
  const selected = master.external.search_manifest.files;
  const selection = new Map(selected.map(e => [cleanPath(e.path), e]));
  const receipts = new Map(master.external_inputs.map(e => [cleanPath(e.path), e]));
  check('/selected_files/count_and_scope', () => {
    assert.equal(expected.size, 61); assert.equal(selected.length, 61); assert.equal(selection.size, 61);
    assert.equal(master.external.search_manifest.checkpoint, '1410');
    assert.deepEqual([...selection.keys()].sort(), [...expected.keys()].sort());
    for (const rel of selection.keys()) assert.ok(!forbidden(rel));
  });
  for (const [rel, entry] of selection) {
    if (forbidden(rel)) { failures.push({ path: '/selected_files/' + esc(rel) }); continue; }
    const content = await bytes(rel);
    check('/selected_files/receipt/' + esc(rel), () => {
      assert.equal(sha(content), entry.sha256); assert.equal(content.length, entry.bytes);
      assert.equal(entry.sha256, expected.get(rel)?.sha256); assert.equal(entry.bytes, expected.get(rel)?.bytes);
      assert.equal(receipts.get(rel)?.sha256, entry.sha256);
    });
    scan(rel.endsWith('.json') ? JSON.parse(content.toString('utf8').replace(/^\uFEFF/, '')) : content.toString('utf8'), '/selected_files/' + esc(rel));
  }
  scan(master, '/master');
  check('/sharing/transient_query', () => assert.equal(transientPaths.size, 0));

  const auditBytes = await bytes('pdf-audit/audit-results.json'), audits = JSON.parse(auditBytes.toString('utf8')).results;
  const freeze = await json('pdf-audit/freeze-1410-receipt.json');
  const oldBytes = await bytes('pdf-audit/audit-results-freeze-1350.json'), oldAudits = JSON.parse(oldBytes.toString('utf8')).results;
  const pendingBytes = await bytes('pdf-audit/audit-pending-round06-freeze-1410.json'), pending = JSON.parse(pendingBytes.toString('utf8')).results;
  const pendingReceipt = await json('pdf-audit/audit-round06-receipt-1410.json');
  const auditMap = new Map(audits.map(a => [auditId(a), a]));
  report.hashes.audit_sha256 = sha(auditBytes); report.hashes.pending_audit_sha256 = sha(pendingBytes);
  check('/audit/frozen_48', () => {
    assert.equal(audits.length, 48); assert.equal(auditMap.size, 48); assert.equal(freeze.result_count, 48);
    assert.equal(freeze.sha256, sha(auditBytes)); assert.equal(receipts.get('pdf-audit/audit-results.json')?.sha256, sha(auditBytes));
    assert.deepEqual(master.external.audit, audits); assert.equal(master.coverage.independent_audit_results, 48);
  });
  check('/audit/old_40_unchanged', () => {
    assert.equal(oldAudits.length, 40); assert.equal(freeze.before_sha256, sha(oldBytes));
    for (const a of oldAudits) assert.deepEqual(auditMap.get(auditId(a)), a);
  });
  check('/audit/new_eight_history_only', () => {
    assert.equal(pending.length, 8); assert.equal(new Set(pending.map(auditId)).size, 8);
    assert.equal(sha(pendingBytes), '455b212b19fd80b644aa82c64e5592d07e35fc27fd462c99571dbd6fdebb4b57');
    assert.equal(pendingReceipt.sha256, sha(pendingBytes)); assert.equal(freeze.input_sha256, sha(pendingBytes));
    assert.equal(freeze.frozen_at, '2026-10-17T14:24:41+08:00');
    const oldIds = new Set(oldAudits.map(auditId)), oldUrls = new Set(oldAudits.flatMap(auditUrls));
    for (const a of pending) {
      assert.ok(!oldIds.has(auditId(a))); assert.ok(!auditUrls(a).some(u => oldUrls.has(u)));
      const canonical = auditMap.get(auditId(a)); assert.ok(canonical);
      const { audit_history: before = [], ...body } = a, { audit_history: after = [], ...canonicalBody } = canonical;
      assert.deepEqual(canonicalBody, body); assert.equal(after.length, before.length + 1); assert.deepEqual(after.slice(0, before.length), before);
      assert.deepEqual(after.at(-1), { checked_at: freeze.frozen_at, method: '主控明确批准14:10固定八GET回灌', outcome: '追加原始审查与证据字段；报批/送审草案内容完整单列，287稿型未定仍C' });
    }
  });
  check('/audit/ratings_and_caution', () => {
    const counts = { B: 0, C: 0, D: 0 }; for (const a of audits) counts[a.recommendation] = (counts[a.recommendation] ?? 0) + 1;
    assert.deepEqual(counts, { B: 16, C: 15, D: 17 });
    for (const id of ['R08-CNASS-333-2012', 'R08-WH-003']) { const a = auditMap.get(id); assert.equal(a.recommendation, 'C'); assert.equal(a.complete_pdf, false); assert.notEqual(a.draft_content_complete, true); }
    const tls = auditMap.get('R08-DRAFT-GREEN-RESIDENTIAL-LEJU'); assert.equal(tls.download_status, '本次网络失败未验证'); assert.equal(tls.version_verified, false); assert.equal(tls.complete_pdf, false);
  });

  const full = master.links.filter(l => l.complete_pdf), fullVersions = new Set(full.flatMap(l => l.verified_standard_ids ?? [])), fullHashes = new Set(full.map(l => l.sha256));
  const drafts = master.links.filter(l => l.draft_content_complete);
  check('/formal/counts', () => {
    assert.equal(full.length, 14); assert.equal(fullVersions.size, 12); assert.equal(fullHashes.size, 12);
    assert.equal(master.coverage.verified_complete_pdf_links, 14); assert.equal(master.coverage.verified_complete_standard_versions, 12); assert.equal(master.coverage.verified_complete_unique_sha256, 12);
  });
  check('/formal/gates_and_relations', () => {
    for (const l of master.links) {
      assert.ok(l.standard_ids.length); for (const sid of l.standard_ids) assert.ok(standards.get(sid)?.link_ids.includes(l.link_id));
      if (!l.complete_pdf) continue;
      assert.equal(l.active, true); assert.equal(l.version_verified, true); assert.equal(l.audit_result?.complete_pdf, true); assert.equal(l.audit_result?.version_verified, true);
      assert.notEqual(l.metadata_only, true); assert.notEqual(l.audit_result?.metadata_only, true); assert.ok(!draftPattern.test(String(l.version_class ?? '') + ' ' + String(l.draft_stage ?? '')));
      assert.ok(l.sha256 && l.pages > 0 && l.pdf_bytes > 0 && l.final_url && l.audit_evidence_paths.length && l.verified_standard_ids.length);
      for (const sid of l.verified_standard_ids) assert.ok(standards.has(sid) && l.standard_ids.includes(sid));
    }
    for (const s of master.standards) {
      for (const lid of s.link_ids) assert.ok(links.get(lid)?.standard_ids.includes(s.standard_id));
      if (s.best_link_id) { const l = links.get(s.best_link_id); assert.ok(l?.active && l.complete_pdf && l.version_verified && l.verified_standard_ids.includes(s.standard_id)); }
    }
  });
  check('/draft/two_classes_separate', () => {
    assert.equal(drafts.length, 2); assert.deepEqual(drafts.map(l => [l.version_class, l.pages]).sort((a, b) => a[1] - b[1]), [['送审稿', 63], ['报批稿', 84]]);
    for (const l of drafts) {
      assert.equal(l.complete_pdf, false); assert.equal(l.version_verified, true); assert.equal(l.active, true); assert.equal(l.http_status, 200); assert.equal(l.recommendation, 'B');
      assert.equal(l.audit_result.draft_content_complete, true); assert.equal(l.audit_result.complete_pdf, false); assert.equal(l.verified_standard_ids.length, 1);
      const s = standards.get(l.verified_standard_ids[0]); assert.equal(s.best_draft_link_id, l.link_id); assert.equal(s.best_link_id, null); assert.equal(s.version_class, l.version_class); assert.ok(!fullVersions.has(s.standard_id));
    }
    assert.equal(master.standards.filter(s => s.best_draft_link_id).length, 2);
  });
  check('/evidence/quality_is_ai_inference', () => {
    const quality = master.evidence.filter(e => e.kind === 'PDF完整性与阅读质量判断'); assert.equal(quality.length, 48);
    for (const e of quality) assert.ok(ai(e.statement_type)); for (const l of master.links.filter(l => l.audit_id)) assert.ok(ai(l.quality_statement_type));
    for (const a of audits) assert.ok(quality.some(e => e.source_id === auditId(a)));
  });

  const round08 = master.external.directory_round08, ttbz = master.external.ttbz_public_dom;
  const sourceRound08 = await json('search/round08-public-expansion/directory2/directory-round08.json');
  const sourceTtbz = await json('search/master-authority/ttbz-ui-observed-20261017-p1.json');
  const roundIds = new Set(round08.records.map(standardId)), directoryNew = new Set([...roundIds].filter(id => !baselineIds.has(id)));
  const ttbzNew = new Set(ttbz.standards.map(standardId).filter(id => !baselineIds.has(id)));
  check('/directory/counts', () => {
    assert.deepEqual(round08, sourceRound08); assert.equal(round08.records.length, 165); assert.equal(roundIds.size, 156); assert.equal(directoryNew.size, 112);
    assert.equal(master.coverage.round08_directory_unique_identities, 156); assert.equal(master.coverage.round08_directory_new_identities_against_frozen_master, 112);
    assert.equal(master.external.directories.length, 973); assert.equal(new Set(master.external.directories.map(r => r.source_id)).size, 973);
    assert.equal(master.external.directories.reduce((n, r) => n + observations(r), 0), 1022);
    assert.equal(master.coverage.authority_records, 973); assert.equal(master.coverage.directory_observation_count, 1022);
    assert.equal(round08.records.filter(r => !baselineSources.has(r.source_id)).length, 165);
    assert.equal(round08.round07_reverified_links.length, 19); for (const r of round08.round07_reverified_links) assert.ok(baselineSources.has(r.source_id));
  });
  check('/ttbz/ten_observed_rows', () => {
    assert.deepEqual(ttbz, sourceTtbz); assert.equal(ttbz.standards.length, 10); assert.equal(new Set(ttbz.standards.map(standardId)).size, 10); assert.equal(ttbzNew.size, 1);
    assert.equal(master.coverage.ttbz_observed_records, 10); assert.equal(master.coverage.ttbz_new_identities_against_frozen_master, 1);
    assert.equal(ttbz.coverage.observed_rows, 10); assert.equal(ttbz.coverage.pages_observed, 1);
    for (const row of ttbz.standards) {
      const s = standards.get(standardId(row)); assert.ok(s); assert.equal(s.link_ids.length, 0); assert.equal(s.best_link_id, null);
      assert.equal(row.metadata_only, true); assert.equal(s.current_status, '现行（全国团体平台标注）'); assert.equal(s.status_checked_at, '2026-10-17T14:12:00+08:00');
      for (const key of ['public_announcement_date', 'published_date', 'effective_date']) assert.equal(s[key], row[key]);
      assert.ok(s.metadata_date_layers.some(l => l.source_id === row.source_id && ['public_announcement_date', 'published_date', 'effective_date'].every(k => l[k] === row[k])));
      assert.ok(s.status_evidence_ids.some(id => evidence.get(id)?.source_id === row.source_id));
    }
  });
  check('/directory/unresolved_entries', () => {
    const gaps = master.unresolved_directory_entries; assert.equal(gaps.length, 18);
    assert.equal(gaps.filter(g => g.entry_class === '编号/四位年份未闭合').length, 15); assert.equal(master.coverage.unresolved_directory_version_gaps, 15);
    assert.equal(gaps.filter(g => g.entry_class !== '编号/四位年份未闭合').length, 3);
    const originals = [...round08.gaps, ...round08.parse_issues]; assert.equal(originals.length, 18);
    for (const g of gaps) {
      assert.ok(!standards.has(g.entry_id)); assert.equal(evidence.get(g.evidence_id)?.standard_id, null);
      assert.ok(!master.standards.some(s => s.metadata_evidence_ids.includes(g.evidence_id)));
      assert.ok(originals.some(o => o.pdf_page_one_based === g.pdf_page_one_based && o.row_index_in_table === g.row_index_in_table && JSON.stringify(o.raw_cells) === JSON.stringify(g.raw_cells)));
    }
    assert.equal(master.unresolved_drafts.length, 3); for (const d of master.unresolved_drafts) assert.ok(!standards.has(d.draft_id));
  });
  check('/directory/same_number_title_conflicts', () => {
    for (const [id, names] of [['CECS-1137-2022-FORMAL', ['建筑信息模型设计应用标准', '模块应急传染病医院建筑技术规程']], ['CECS-22-2012-FORMAL', ['叠压供水技术规程', '小区集中生活热水设计应用规程']]]) {
      const s = standards.get(id); assert.ok(s); assert.equal(s.identity_confirmed, false); assert.ok(s.name_resolution_status && s.directory_name_conflicts.length >= 2);
      for (const name of names) { assert.ok(s.name_variants.includes(name)); assert.ok(s.directory_name_conflicts.some(c => c.name === name)); }
      assert.equal(s.name, id.includes('1137') ? baseline.standards.find(b => b.standard_id === id).name : '题名冲突待核');
    }
  });

  const association = await json('search/round08-public-expansion/candidates-r08-association.json');
  const water = await json('search/round08-public-expansion/water-historical/round08-water-historical-candidates.json');
  const industrialId = 'R08-CNASS-DRAFT-INDUSTRIAL-CONVERSION';
  check('/draft/industrial_identity_is_unique', () => {
    const candidate = association.candidates.find(c => c.candidate_id === industrialId), audited = auditMap.get(industrialId);
    const related = master.links.filter(l => l.audit_id === industrialId || l.candidate_id === industrialId || l.candidate_ids?.includes(industrialId));
    const auditedLinks = related.filter(l => l.audit_id === industrialId); assert.equal(auditedLinks.length, 1);
    const l = auditedLinks[0]; assert.equal(l.standard_ids.length, 1); assert.deepEqual(l.verified_standard_ids, l.standard_ids);
    for (const route of related) assert.deepEqual([...new Set(route.standard_ids)].sort(), [...new Set(l.standard_ids)].sort());
    const normalized = (String(candidate.standard_number ?? '') + ' ' + String(candidate.name ?? '')).normalize('NFKC').trim().replace(/[∕／]/g, '/');
    const expectedId = 'CECS-UNRESOLVED-' + sha(normalized).slice(0, 12); assert.equal(l.standard_ids[0], expectedId);
    const s = standards.get(expectedId); assert.equal(master.standards.filter(x => x.name === audited.name).length, 1);
    assert.equal(master.external.search.filter(c => c.candidate_id === industrialId).length, 1); assert.equal(master.external.audit.filter(a => a.candidate_id === industrialId).length, 1);
    assert.ok(s.placeholder_code_observations.some(o => o.standard_number === candidate.standard_number)); assert.ok(s.placeholder_code_observations.some(o => o.standard_number === audited.standard_number));
    assert.equal(s.best_draft_link_id, l.link_id); assert.equal(s.best_link_id, null);
  });
  const nonPdfNew = new Set();
  check('/non_pdf/two_metadata_only_routes', () => {
    assert.equal(association.metadata_only_non_pdf_routes.length, 2);
    for (const r of association.metadata_only_non_pdf_routes) {
      const matched = master.standards.filter(s => s.non_pdf_routes?.some(n => n.source_id === r.source_id)); assert.equal(matched.length, 1);
      const s = matched[0]; assert.equal(s.name, r.name_raw.match(/《([^》]+)》/)[1]); assert.equal(s.link_ids.length, 0); assert.equal(s.best_link_id, null); assert.equal(s.best_draft_link_id, null);
      assert.ok(s.non_pdf_routes.some(n => n.document_url === r.document_url && n.original_name === r.name_raw && n.format === r.format));
      if (!baselineIds.has(s.standard_id)) nonPdfNew.add(s.standard_id);
    }
    assert.equal(nonPdfNew.size, 2);
  });
  check('/identity/net_addition_categories', () => {
    const candidateNew = new Set();
    for (const c of [...association.candidates, ...water.candidates]) {
      const matched = master.links.filter(l => l.audit_id === c.candidate_id || l.candidate_id === c.candidate_id || l.candidate_ids?.includes(c.candidate_id)); assert.ok(matched.length >= 1);
      const ids = new Set(matched.flatMap(l => l.standard_ids)); assert.equal(ids.size, 1);
      for (const route of matched) assert.deepEqual([...new Set(route.standard_ids)].sort(), [...ids].sort());
      for (const id of ids) if (!baselineIds.has(id)) candidateNew.add(id);
    }
    assert.equal(candidateNew.size, 4);
    const union = new Set([...directoryNew, ...ttbzNew, ...candidateNew, ...nonPdfNew]); assert.equal(union.size, 119); assert.deepEqual([...newIds].sort(), [...union].sort());
  });

  check('/regression/608_and_10065_10066', () => {
    const s = standards.get('CECS-608-2019-FORMAL'); assert.equal(s.name, '绿色建筑运营后评估标准'); assert.ok(s.name_variants.includes('绿色建筑运营后评价标准'));
    assert.ok(s.name_correction_events.some(e => e.old_name === '绿色建筑运营后评价标准' && e.new_name === s.name && evidence.has(e.evidence_id)));
    for (const id of ['CECS-10065-2019-FORMAL', 'CECS-10066-2019-FORMAL']) assert.equal(standards.get(id).name, baseline.standards.find(s => s.standard_id === id).name);
  });
  check('/regression/102_edition', () => {
    const old = standards.get('CECS-102-2002-FORMAL'), ed = standards.get('CECS-102-2002-FORMAL-E2012');
    assert.equal(ed.year, 2002); assert.equal(ed.edition_label, '2012年版'); assert.equal(ed.published_date, null); assert.equal(ed.effective_date, null);
    assert.ok(ed.metadata_date_layers.some(l => l.context.includes('网页') && l.effective_date === '2012-04-24')); assert.ok(ed.metadata_date_layers.some(l => l.context.includes('书内') && l.effective_date === '2003-03-01'));
    assert.ok(old.issues.some(s => s.includes('未核版次'))); assert.ok(!old.link_ids.some(id => ed.link_ids.includes(id))); if (old.best_link_id) assert.notEqual(old.best_link_id, ed.best_link_id);
  });
  check('/regression/22_status', () => {
    const old = standards.get('CECS-22-2005-FORMAL'), next = standards.get('CECS-22-2024-FORMAL'); assert.ok(old.current_status.includes('已废止')); assert.equal(old.withdrawal_date, '2025-04-01'); assert.equal(old.replaced_by, next.standard_id);
    assert.ok(old.status_basis.includes('第5页')); const e = master.evidence.find(e => e.source_id === 'PDF-CECS-2185-REPEAL-20261017' && e.standard_id === old.standard_id); assert.ok(e && old.status_evidence_ids.includes(e.evidence_id)); assert.equal(e.pdf_page_one_based, 5); assert.equal(e.source_printed_page, null); assert.ok(next.current_status.startsWith('未知'));
  });
  check('/regression/796_announcement', () => {
    for (const s of master.standards.filter(s => /^CECS-796-/.test(s.standard_id))) { assert.equal(s.name, '屋面结构雪荷载设计标准'); assert.equal(s.identity_confirmed, false); assert.equal(s.version_stage, '正式性/年份冲突待核'); }
    const l = master.links.find(l => l.audit_id === 'AUD-796-ANNOUNCEMENT-QIXIN'); assert.equal(l.metadata_only, true); assert.equal(l.complete_pdf, false); assert.equal(l.recommendation, 'D'); assert.equal(l.pages, 1);
  });
  check('/regression/81_mapping_and_four_metadata_routes', () => {
    assert.deepEqual(master.original_records.map(r => r.seed_id).sort(), Array.from({ length: 81 }, (_, i) => 'S' + String(i + 1).padStart(3, '0')));
    for (const r of master.original_records) { assert.ok(standards.has(r.standard_id)); assert.ok(links.has(r.link_id)); }
    for (const id of ['CECS-10267-2023-FORMAL', 'CECS-10309-2023-FORMAL', 'CECS-10222-2022-FORMAL', 'CECS-10403-2024-FORMAL']) { assert.ok(standards.has(id)); assert.equal(standards.get(id).link_ids.length, 0); }
  });
  report.counts = { standards: master.standards.length, links: master.links.length, audits: audits.length, selected_files: selected.length, original_records: master.original_records.length,
    formal_complete_links: full.length, formal_complete_versions: fullVersions.size, formal_complete_sha256: fullHashes.size, complete_drafts: drafts.length,
    directory_unique_source_rows: master.external.directories.length, directory_observations: master.external.directories.reduce((n, r) => n + observations(r), 0),
    round08_rows: round08.records.length, round08_unique_identities: roundIds.size, directory_net_new_identities: directoryNew.size, ttbz_rows: ttbz.standards.length,
    ttbz_net_new_identities: ttbzNew.size, unresolved_directory_entries: master.unresolved_directory_entries.length, non_pdf_new_identities: nonPdfNew.size, total_net_new_identities: newIds.size };
  const finalMasterHash = sha(await fs.readFile(path.join(out, 'cecs-master.json')));
  check('/snapshot/unchanged_during_validation', () => assert.equal(finalMasterHash, report.hashes.master_sha256));
} catch { failures.push({ path: activeReadPath }); }
report.transient_query_paths = [...transientPaths]; report.passed = failures.length === 0;
await fs.writeFile(path.join(out, 'freeze-1410-validation.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify({ passed: report.passed, output: 'catalog/freeze-1410-validation.json', hashes: report.hashes, counts: report.counts, failures, transient_query_paths: report.transient_query_paths }));
if (!report.passed) process.exitCode = 1;
