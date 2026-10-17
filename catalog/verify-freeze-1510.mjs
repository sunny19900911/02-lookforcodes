import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';

// Independent frozen-input checks. Running this script writes only its receipt.
// It never follows URLs or opens raw responses, PDF/HTML/image files or Git.
const out = import.meta.dirname, root = path.resolve(out, '..');
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const clean = value => String(value).replaceAll('\\', '/');
const esc = value => String(value).replaceAll('~', '~0').replaceAll('/', '~1');
const cache = new Map(), failures = [], checks = [], transientPaths = new Set();
const report = { checkpoint: '1510', checked_at: new Date().toISOString(), hashes: {}, counts: {}, checks, failures };
const rawG2 = 'search/g2-public-routes/round02-candidates.json';
const altShare = 'pdf-audit/candidates-r11-alt31-share.json';
const altSha = '2aa5cd96cfcc3f9d3848c7046575bb72e53b7426fb602f8b58b191558b94a61d';
const oldWater = new Set([
  'search/round07-broad-attachments/water-mep/candidates-round07-water-mep-share-v2.json',
  'search/round07-broad-attachments/water-mep/query-ledger-r07-water-mep-share.json',
  'search/round07-broad-attachments/water-mep/addendum-r07-water-mep.json',
  'search/round07-broad-attachments/water-mep/share-review-v2.json',
  'search/round09-new-sources/water-mep/round09-water-mep-candidates.json',
]);
const forbidden = p => p === rawG2 || /(?:^|[/_.-])(?:r12|r13|round12|round13)(?:[/_.-]|$)/i.test(p)
  || p === 'search/round09-new-sources/candidates-r09-root.json'
  || /scope-transition|scope-excluded|freeze-inputs-1500/i.test(p)
  || (p.includes('/water-mep/') && !oldWater.has(p))
  || /audit-pending-round09-freeze-1450\.json$|candidates-r11-alt31\.json$/i.test(p)
  || /\.(?:pdf|html?|png|jpe?g|webp)$/i.test(p);
let activePath = '/runtime';
async function bytes(relative) {
  const rel = clean(relative); activePath = '/' + rel; assert.ok(!forbidden(rel));
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
const idOf = a => a.audit_id ?? a.candidate_id;
const auditUrls = a => [a.requested_url ?? a.download_url ?? a.direct_url].filter(Boolean);
const observations = r => 1 + (r.previous_observations ?? []).reduce((n, x) => n + observations(x), 0);
const ai = value => /^AI推断(?:[（(]|$)/.test(String(value ?? ''));
const sorted = values => [...values].sort();
function numberedId(raw, year) {
  const code = String(raw).normalize('NFKC').replace(/[∕／]/g, '/');
  const family = code.match(/CECS\s*-\s*(CREA|CBIMU)\b/i)?.[1]?.toUpperCase();
  const withoutJoint = code.replace(/CECS\s*-\s*(?:CREA|CBIMU)\b/i, 'CECS');
  const m = withoutJoint.match(/CECS(?:[\s_-]*T)?[\s_-]*(G\s*[:：]\s*[A-Z]\d+(?:-\d+)?|\d+)(?:\s*[-:：]\s*|\s+)(\d{2,4})(?!\d)/i);
  assert.ok(m); const y = Number(year ?? (m[2].length === 2 ? (Number(m[2]) >= 50 ? '19' : '20') + m[2] : m[2]));
  const number = /^\d+$/.test(m[1]) ? String(Number(m[1])) : m[1].replace(/\s+/g, '').toUpperCase().replaceAll(':', '_').replaceAll('：', '_');
  assert.ok(y >= 1900 && y <= 2099); return 'CECS' + (family ? '-' + family : '') + '-' + number + '-' + y + '-FORMAL';
}
function provisionalId(c) {
  const normalized = (String(c.standard_number ?? '') + ' ' + String(c.name ?? c.standard_name ?? '')).normalize('NFKC').trim().replace(/[∕／]/g, '/');
  return 'CECS-UNRESOLVED-' + sha(normalized).slice(0, 12);
}

try {
  const masterBytes = await bytes('catalog/cecs-master.json'), master = JSON.parse(masterBytes.toString('utf8'));
  const baseline = await json('catalog/history/master-before-1510.json');
  const standards = new Map(master.standards.map(s => [s.standard_id, s]));
  const links = new Map(master.links.map(l => [l.link_id, l]));
  const evidence = new Map(master.evidence.map(e => [e.evidence_id, e]));
  const baseStandards = new Map(baseline.standards.map(s => [s.standard_id, s]));
  const baselineIds = new Set(baseStandards.keys()), newIds = new Set(master.standards.filter(s => !baselineIds.has(s.standard_id)).map(s => s.standard_id));
  report.snapshot_generated_at = master.generated_at;
  report.hashes.master_sha256 = sha(masterBytes);
  report.hashes.xlsx_sha256 = sha(await bytes('catalog/CECS可下载PDF总表.xlsx'));
  for (const [arg, field] of [['master-sha256', 'master_sha256'], ['xlsx-sha256', 'xlsx_sha256']]) {
    const expectedHash = process.argv.find(a => a.startsWith('--' + arg + '='))?.split('=')[1];
    if (expectedHash) check('/snapshot/' + arg, () => assert.equal(report.hashes[field], expectedHash));
  }
  check('/identity/counts', () => {
    assert.equal(master.scope.checkpoint, '1510'); assert.equal(baseline.standards.length, 1008);
    assert.equal(master.standards.length, 1288); assert.equal(newIds.size, 280); assert.equal(standards.size, 1288);
    assert.equal(links.size, master.links.length); assert.equal(master.coverage.registered_standard_versions, 1288);
    assert.equal(master.coverage.registered_links, master.links.length); assert.equal(master.coverage.merge_net_new_identities, 280);
    for (const id of baselineIds) assert.ok(standards.has(id));
  });

  const manifestPaths = [
    'search/freeze-inputs-1320.json', 'search/freeze-inputs-1330.json', 'search/freeze-inputs-1340.json',
    'search/freeze-inputs-1340-water-mep-addendum-v2.json', 'search/freeze-inputs-g2-round02-share-1350.json',
    'search/freeze-inputs-1400.json', 'search/master-authority/freeze-ttbz-p1-1410.json',
    'search/freeze-inputs-1420.json', 'search/freeze-inputs-1430.json', 'search/freeze-inputs-1440.json',
  ];
  const expected = new Map();
  for (const file of manifestPaths) for (const e of (await json(file)).files) {
    const rel = clean(e.path);
    check('/manifests/duplicate/' + esc(rel), () => { if (expected.has(rel)) assert.deepEqual(expected.get(rel), e); });
    expected.set(rel, e);
  }
  expected.delete(rawG2); // Only the historical hash annotation is retained; never open it.
  const selected = master.external.search_manifest.files, selection = new Map(selected.map(e => [clean(e.path), e]));
  const receipts = new Map(master.external_inputs.map(e => [clean(e.path), e]));
  check('/selected_files/count_and_scope', () => {
    assert.equal(expected.size, 93); assert.equal(selected.length, 93); assert.equal(selection.size, 93);
    assert.equal(master.external.search_manifest.checkpoint, '1510'); assert.deepEqual(sorted(selection.keys()), sorted(expected.keys()));
    for (const rel of selection.keys()) assert.ok(!forbidden(rel)); assert.ok(!selection.has(altShare));
    assert.ok(!master.external.search.some(c => /(?:R12|R13)(?:-|_)/.test(String(c.candidate_id ?? ''))));
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
  const alternateBytes = await bytes(altShare), alternate = JSON.parse(alternateBytes.toString('utf8'));
  const publication = await json('pdf-audit/audit-round09-publication-selection-1450.json');
  check('/sharing/alternate_current_projection_only', () => {
    assert.equal(sha(alternateBytes), altSha); assert.equal(receipts.get(altShare)?.sha256, altSha);
    assert.equal(master.external_inputs.filter(e => clean(e.path) === altShare).length, 1);
    assert.deepEqual(master.external.current_alternate_share, alternate); assert.deepEqual(master.external.alternate_publication_selection, publication);
    assert.equal(publication.selected_audit_snapshot.path, 'audit-pending-round09-freeze-1450-v2.json');
    assert.equal(publication.current_alternate_share_projection.sha256, altSha);
    for (const c of master.external.search) if (c.candidate_id === 'R11-31-2017-GUANGYUXC') {
      assert.equal(c._catalog_source.path, altShare); assert.equal(c.web_pages_observed ?? null, null);
    }
  });
  scan(alternate, '/alternate_share'); scan(master, '/master');
  check('/sharing/transient_query', () => assert.equal(transientPaths.size, 0));

  const auditBytes = await bytes('pdf-audit/audit-results.json'), auditDocument = JSON.parse(auditBytes.toString('utf8')), audits = auditDocument.results;
  const freezeBytes = await bytes('pdf-audit/audit-results-freeze-1510.json'), freeze = await json('pdf-audit/freeze-1510-receipt.json');
  const oldAuditBytes = await bytes('pdf-audit/audit-results-freeze-1410.json'), oldAudits = JSON.parse(oldAuditBytes.toString('utf8')).results;
  const auditMap = new Map(audits.map(a => [idOf(a), a]));
  report.hashes.audit_sha256 = sha(auditBytes);
  check('/audit/frozen_63', () => {
    assert.equal(audits.length, 63); assert.equal(auditMap.size, 63); assert.equal(freeze.result_count, 63);
    assert.equal(sha(auditBytes), sha(freezeBytes)); assert.equal(freeze.sha256, sha(auditBytes));
    assert.equal(sha(auditBytes), '815565100ff8959e609b223af1c64e43451b98fbb4cb1dfc83ddcd5f778c4449');
    assert.equal(receipts.get('pdf-audit/audit-results.json')?.sha256, sha(auditBytes));
    assert.deepEqual(master.external.audit, audits); assert.equal(master.coverage.independent_audit_results, 63);
  });
  check('/audit/old_48_unchanged', () => {
    assert.equal(oldAudits.length, 48); assert.equal(sha(oldAuditBytes), freeze.before_sha256);
    assert.equal(sha(oldAuditBytes), 'a81a40dfff05c0bd437b99875baba5efc7f540c05ae9c59437aceb66d5aa65e2');
    for (const a of oldAudits) assert.deepEqual(auditMap.get(idOf(a)), a);
  });
  const pendingSpecs = [
    ['audit-pending-round07-freeze-1430.json', '1f75a6b1536d5265a2a8cb814e1c2d1c7630de38d9dd49ec707650a174aebe0f', 6],
    ['audit-pending-round08-fixed-r10.json', 'b85f429140403811b90b5215ca38ab9c45d420705073ccb55c93f072805843e5', 2],
    ['audit-pending-round09-freeze-1450-v2.json', '339a53ad776599ca4181a75633dd0479b1f040d293e9bf35d02dd762937196ef', 7],
  ];
  const seenIds = new Set(oldAudits.map(idOf)), seenUrls = new Set(oldAudits.flatMap(auditUrls));
  for (const [file, hash, count] of pendingSpecs) {
    const content = await bytes('pdf-audit/' + file), pending = JSON.parse(content.toString('utf8')).results;
    check('/audit/pending/' + file, () => {
      assert.equal(sha(content), hash); assert.equal(pending.length, count);
      const input = freeze.input_snapshots.find(e => e.file === file); assert.equal(input.sha256, hash); assert.equal(input.result_count, count);
      for (const a of pending) {
        assert.ok(!seenIds.has(idOf(a))); assert.ok(!auditUrls(a).some(u => seenUrls.has(u)));
        seenIds.add(idOf(a)); auditUrls(a).forEach(u => seenUrls.add(u));
        const canonical = auditMap.get(idOf(a)); assert.ok(canonical);
        const { audit_history: before = [], ...body } = a, { audit_history: after = [], ...current } = canonical;
        assert.deepEqual(current, body); assert.equal(after.length, before.length + 1); assert.deepEqual(after.slice(0, before.length), before);
        assert.deepEqual(after.at(-1), { checked_at: freeze.frozen_at, method: '主控明确批准15:10固定R09/R10/R11回灌', input_snapshot: file, outcome: '仅追加固定审查与证据字段；保留主评级、正文浏览范围、版本及完整性独立结论' });
      }
    });
  }
  check('/audit/ratings_and_body_fields', () => {
    const ratings = { B: 0, C: 0, D: 0 }; for (const a of audits) ratings[a.recommendation] = (ratings[a.recommendation] ?? 0) + 1;
    assert.deepEqual(ratings, { B: 19, C: 18, D: 26 });
    for (const a of audits) {
      const related = master.links.filter(l => l.audit_id === idOf(a)); assert.equal(related.length, 1);
      const l = related[0]; assert.deepEqual(l.audit_result, a); assert.equal(l.recommendation, a.recommendation);
      for (const key of ['body_reading_recommendation', 'body_searchable', 'body_text_layer', 'quality_anomalies']) assert.deepEqual(l[key], a[key] ?? null);
    }
    const body = auditMap.get('R11-1555-2024-FAIUSR'); assert.equal(body.recommendation, 'D'); assert.match(body.body_reading_recommendation, /^B/); assert.equal(body.complete_pdf, false);
    assert.equal(auditMap.get('R11-200-2006-DLSSYHT').body_reading_recommendation ?? null, null);
    assert.equal(auditMap.get('R11-197-2006-FAIUSR').body_searchable, false);
    const alt = auditMap.get('R11-31-2017-GUANGYUXC'), altLink = master.links.find(l => l.audit_id === idOf(alt));
    for (const value of [alt.pages, alt.web_pages_observed, altLink.pages, altLink.web_pages_observed]) assert.equal(value ?? null, null);
    assert.equal(alt.recommendation, 'D'); assert.equal(alt.complete_pdf, false);
  });

  const full = master.links.filter(l => l.complete_pdf), fullVersions = new Set(full.flatMap(l => l.verified_standard_ids ?? [])), fullHashes = new Set(full.map(l => l.sha256));
  const drafts = master.links.filter(l => l.draft_content_complete);
  check('/formal/counts_and_gate', () => {
    assert.equal(full.length, 14); assert.equal(fullVersions.size, 12); assert.equal(fullHashes.size, 12);
    assert.equal(master.coverage.verified_complete_pdf_links, 14); assert.equal(master.coverage.verified_complete_standard_versions, 12); assert.equal(master.coverage.verified_complete_unique_sha256, 12);
    for (const l of full) {
      assert.equal(l.active, true); assert.equal(l.version_verified, true); assert.equal(l.audit_result.complete_pdf, true); assert.equal(l.audit_result.version_verified, true);
      assert.notEqual(l.metadata_only, true); assert.notEqual(l.audit_result.metadata_only, true); assert.notEqual(l.draft_content_complete, true);
      assert.ok(!/报批|送审|征求意见|草案/.test(String(l.version_class ?? '') + ' ' + String(l.draft_stage ?? '')));
      assert.ok(l.sha256 && l.pages > 0 && l.pdf_bytes > 0 && l.final_url && l.audit_evidence_paths.length && l.verified_standard_ids.length);
    }
  });
  check('/relations/links_evidence_best', () => {
    const sourceIds = new Set([...master.evidence.map(e => e.evidence_id), ...master.evidence.map(e => e.source_id),
      ...master.original_records.map(r => r.seed_id), ...master.original_records.map(r => r.source_id)].filter(Boolean));
    for (const l of master.links) {
      assert.ok(l.standard_ids.length); for (const id of l.standard_ids) assert.ok(standards.get(id)?.link_ids.includes(l.link_id));
      for (const id of l.verified_standard_ids ?? []) assert.ok(l.standard_ids.includes(id) && standards.has(id));
      // Legacy seed links use external source IDs; E-* identifiers reference evidence objects.
      for (const id of l.source_ids ?? []) assert.ok(id.startsWith('E-') ? evidence.has(id) : sourceIds.has(id));
    }
    for (const s of master.standards) {
      for (const id of s.link_ids) assert.ok(links.get(id)?.standard_ids.includes(s.standard_id));
      for (const id of [...(s.metadata_evidence_ids ?? []), ...(s.status_evidence_ids ?? [])]) assert.ok(evidence.has(id));
      if (s.best_link_id) { const l = links.get(s.best_link_id); assert.ok(l?.active && l.complete_pdf && l.version_verified && l.verified_standard_ids.includes(s.standard_id)); }
    }
    for (const e of master.evidence) if (e.standard_id) assert.ok(standards.has(e.standard_id));
  });
  check('/draft/five_separate_from_formal', () => {
    assert.equal(drafts.length, 5); assert.equal(master.standards.filter(s => s.best_draft_link_id).length, 5);
    const classes = {}; for (const l of drafts) classes[l.version_class] = (classes[l.version_class] ?? 0) + 1;
    assert.deepEqual(classes, { '报批稿': 3, '送审稿': 1, '征求意见稿': 1 });
    for (const l of drafts) {
      assert.equal(l.complete_pdf, false); assert.equal(l.version_verified, true); assert.equal(l.active, true); assert.equal(l.http_status, 200); assert.equal(l.recommendation, 'B');
      assert.equal(l.audit_result.draft_content_complete, true); assert.equal(l.audit_result.complete_pdf, false); assert.equal(l.verified_standard_ids.length, 1);
      const s = standards.get(l.verified_standard_ids[0]); assert.equal(s.best_draft_link_id, l.link_id); assert.equal(s.best_link_id, null); assert.equal(s.version_class, l.version_class); assert.ok(!fullVersions.has(s.standard_id));
    }
    assert.ok(drafts.some(l => l.audit_id === 'R07-G5-DRAFT-ZERO-2025' && l.pages === 84));
    assert.ok(drafts.some(l => l.audit_id === 'R08-CNASS-DRAFT-INDUSTRIAL-CONVERSION' && l.pages === 63));
    const prefab = auditMap.get('R09-DRAFT-PREFAB-LOW-CARBON'); assert.notEqual(prefab.version_class, '报批稿'); assert.notEqual(prefab.draft_content_complete, true);
  });
  check('/evidence/quality_is_ai_inference', () => {
    const quality = master.evidence.filter(e => e.kind === 'PDF完整性与阅读质量判断'); assert.equal(quality.length, 63);
    for (const e of quality) assert.ok(ai(e.statement_type));
    for (const a of audits) { assert.ok(quality.some(e => e.source_id === idOf(a))); assert.ok(ai(master.links.find(l => l.audit_id === idOf(a)).quality_statement_type)); }
  });

  const directoryFiles = [
    'search/round09-new-sources/recent-directory/recent-directory-r09.json',
    'search/round10-public-sources/monthly-directory/monthly-directory-r10.json',
    'search/round11-public-sources/monthly-directory/monthly-directory-r11.json',
  ];
  const directoryInputs = await Promise.all(directoryFiles.map(json));
  const rows = directoryInputs.flatMap(b => b.records), resolved = rows.filter(r => r.number_year_key && r.year);
  const recentIds = new Set(resolved.map(r => numberedId(r.standard_number_as_published, r.year))), directoryNew = new Set([...recentIds].filter(id => !baselineIds.has(id)));
  const directoryBySource = new Map(master.external.directories.map(r => [r.source_id, r]));
  const allSources = directoryInputs.flatMap(b => b.sources);
  check('/directory/counts_and_frozen_inputs', () => {
    assert.equal(master.external.recent_directories.length, 3);
    for (let i = 0; i < 3; i++) { assert.equal(master.external.recent_directories[i].file, directoryFiles[i]); assert.deepEqual(master.external.recent_directories[i].data, directoryInputs[i]); }
    assert.equal(rows.length, 397); assert.equal(resolved.length, 394); assert.equal(recentIds.size, 381); assert.equal(directoryNew.size, 268);
    assert.equal(master.coverage.recent_directory_rows_including_gaps, 397); assert.equal(master.coverage.recent_directory_resolved_rows, 394);
    assert.equal(master.coverage.recent_directory_unique_identities, 381); assert.equal(master.coverage.recent_directory_new_identities_against_frozen_master, 268);
    assert.equal(master.external.directories.length, 1367); assert.equal(directoryBySource.size, 1367); assert.equal(master.coverage.authority_records, 1367);
    assert.equal(master.external.directories.reduce((n, r) => n + observations(r), 0), 1416); assert.equal(master.coverage.directory_observation_count, 1416);
    assert.equal(allSources.length, 13); assert.equal(allSources.filter(s => (s.source_category ?? 'government') === 'government').length, 7);
    assert.equal(allSources.filter(s => s.source_category === 'institute_public_information_platform').length, 6);
  });
  check('/directory/row_identity_parent_and_dates', () => {
    const baseSources = new Set(baseline.external.directories.map(r => r.source_id));
    for (const batch of directoryInputs) for (const r of batch.records.filter(x => x.number_year_key && x.year)) {
      assert.ok(!baseSources.has(r.record_id)); const mapped = directoryBySource.get(r.record_id); assert.ok(mapped);
      assert.equal(mapped.source_id, r.record_id); assert.equal(mapped.source_directory_id, r.source_id); assert.deepEqual(mapped.raw_cells, r.raw_cells);
      assert.deepEqual(mapped.source_location, r.source_location); assert.equal(mapped.webpage_published_date, r.webpage_published_date);
      assert.equal(mapped.standard_published_date, null);
      const s = standards.get(numberedId(r.standard_number_as_published, r.year)); assert.ok(s);
      const layer = s.metadata_date_layers.find(l => l.source_id === r.record_id); assert.ok(layer);
      assert.equal(layer.webpage_published_date, r.webpage_published_date); assert.equal(layer.standard_published_date, null);
      assert.equal(layer.effective_date_as_published, r.effective_date_as_published); assert.equal(layer.effective_date, r.effective_date);
      const parent = batch.sources.find(p => p.source_id === r.source_id); assert.equal(layer.title_as_published, parent.title_as_published);
      const e = master.evidence.find(e => e.source_id === r.record_id && e.standard_id === s.standard_id); assert.ok(e);
      assert.equal(e.publisher_source_id, r.source_id); assert.deepEqual(e.raw_record, r);
      const category = r.source_category ?? parent.source_category ?? 'government'; assert.equal(mapped.source_category, category); assert.equal(e.source_category, category);
      const prior = baseStandards.get(s.standard_id); if (!prior) assert.notEqual(s.published_date, r.webpage_published_date);
    }
    assert.equal(directoryInputs[0].conflicts.length, 33);
    for (const c of directoryInputs[0].conflicts) {
      const r = directoryInputs[0].records.find(r => r.record_id === c.record_id), s = standards.get(numberedId(r.standard_number_as_published, r.year));
      const layer = s.metadata_date_layers.find(l => l.source_id === r.record_id); assert.ok(layer.date_conflicts.some(x => JSON.stringify(x) === JSON.stringify(c)));
      assert.equal(s.effective_date ?? null, baseStandards.get(s.standard_id)?.effective_date ?? null);
    }
  });
  check('/directory/unresolved_and_in_progress_separate', () => {
    const gaps = master.unresolved_directory_entries; assert.equal(gaps.length, 21);
    assert.equal(gaps.filter(g => g.entry_class === '编号/四位年份未闭合').length, 15); assert.equal(master.coverage.unresolved_directory_version_gaps, 15);
    assert.equal(gaps.filter(g => g.entry_class === '图集编号/年份待核').length, 3); assert.equal(master.coverage.unresolved_recent_directory_gaps, 3);
    assert.equal(gaps.filter(g => !['编号/四位年份未闭合', '图集编号/年份待核'].includes(g.entry_class)).length, 3); assert.equal(master.coverage.directory_nonstandard_or_parse_gaps, 3);
    assert.deepEqual(gaps.filter(g => g.entry_class !== '图集编号/年份待核'), baseline.unresolved_directory_entries);
    for (const b of directoryInputs) for (const original of b.gaps) {
      const g = gaps.find(g => g.record_id === original.record_id); assert.ok(g); assert.deepEqual(g.raw_cells, original.raw_cells); assert.deepEqual(g.source_location, original.source_location);
      assert.ok(!standards.has(g.entry_id)); assert.equal(evidence.get(g.evidence_id)?.standard_id, null); assert.ok(!directoryBySource.has(g.record_id));
    }
    assert.equal(master.unresolved_drafts.length, 3); assert.deepEqual(master.unresolved_drafts, baseline.unresolved_drafts);
    for (const g of gaps) assert.ok(!master.standards.some(s => s.metadata_evidence_ids.includes(g.evidence_id)));
  });

  const primaryFiles = [
    'search/round09-new-sources/candidates-r09-root-share.json', 'search/round09-new-sources/water-mep/round09-water-mep-candidates.json',
    'search/round10-public-sources/candidates-r10-detection.json', 'search/round11-public-sources/candidates-r11-root.json',
    'search/round11-public-sources/instrument-pages/round11-instrument-pages.json',
  ];
  const candidateInputs = await Promise.all(primaryFiles.map(json)), candidates = candidateInputs.flatMap(b => b.candidates ?? []), candidateNew = new Set();
  check('/identity/pdf_candidate_net_six', () => {
    assert.equal(candidates.length, 14);
    for (const c of candidates) {
      const related = master.links.filter(l => l.candidate_id === c.candidate_id || l.candidate_ids?.includes(c.candidate_id) || l.audit_id === c.candidate_id); assert.ok(related.length);
      const ids = new Set(related.flatMap(l => l.standard_ids)); assert.equal(ids.size, 1);
      for (const id of ids) if (!baselineIds.has(id)) candidateNew.add(id);
    }
    assert.equal(candidateNew.size, 6); assert.ok(candidateNew.has('CECS-243-2008-FORMAL')); assert.ok(candidateNew.has('CECS-1555-2024-FORMAL'));
    assert.ok(!standards.has('CECS-243-2008-CONSULT-DRAFT')); assert.ok(!standards.has('CECS-1555-2024-CONSULT-DRAFT')); assert.ok(!standards.has('CECS-2-2005-CONSULT-DRAFT'));
    for (const c of candidates.filter(c => /^R09-(?:CNASS-DRAFT|DRAFT-)/.test(c.candidate_id))) {
      const related = master.links.filter(l => l.candidate_id === c.candidate_id || l.candidate_ids?.includes(c.candidate_id) || l.audit_id === c.candidate_id);
      const sids = new Set(related.flatMap(l => l.standard_ids)); assert.equal(sids.size, 1); assert.ok(standards.has([...sids][0]));
      assert.equal(master.external.search.filter(x => x.candidate_id === c.candidate_id).length, 1);
    }
  });
  const foundation = await json('search/round10-public-sources/foundation/round10-foundation-search.json');
  const metadataRows = [
    ...candidateInputs[0].metadata_only, ...candidateInputs[1].blocked_routes, ...candidateInputs[1].preview_routes,
    ...candidateInputs[2].metadata_only.filter(r => r.standard_number), ...foundation.blocked_routes,
    ...candidateInputs[3].short_pdf_routes, ...candidateInputs[4].non_pdf_metadata_routes,
  ];
  const metadataNew = new Set();
  check('/identity/metadata_six_extra_and_no_invented_gaps', () => {
    assert.equal(metadataRows.length, 13); // 16 routes minus three notice-only associations.
    for (const r of metadataRows) {
      const raw = r.standard_number, id = /CECS\s*\d+\s*[-:：]\s*\d/i.test(String(raw)) ? numberedId(raw, r.year) : provisionalId(r);
      assert.ok(standards.has(id)); const s = standards.get(id);
      if (!baselineIds.has(id) && !directoryNew.has(id) && !candidateNew.has(id)) metadataNew.add(id);
      if (!baselineIds.has(id)) { assert.equal(s.link_ids.length, 0); assert.equal(s.best_link_id, null); assert.equal(s.best_draft_link_id, null); }
    }
    assert.deepEqual(sorted(metadataNew), sorted([
      provisionalId(candidateInputs[0].metadata_only[0]), provisionalId(candidateInputs[0].metadata_only[1]),
      'CECS-838-2021-FORMAL', 'CECS-321-2012-FORMAL', 'CECS-218-2007-FORMAL', 'CECS-776-2020-FORMAL',
    ]));
    for (const r of foundation.notice_only_index_routes) {
      assert.ok(!standards.has(numberedId(r.standard_number))); const found = master.external.route_observations.filter(x => x.source_id === r.source_id); assert.equal(found.length, 1);
      assert.equal(found[0].standard_number, r.standard_number); assert.equal(found[0].observation, r.observation);
    }
    const generic = candidateInputs[2].metadata_only.filter(r => !r.standard_number); assert.equal(generic.length, 1);
    assert.ok(master.external.route_observations.some(r => r.source_id === generic[0].source_id));
    const union = new Set([...directoryNew, ...candidateNew, ...metadataNew]); assert.equal(union.size, 280); assert.deepEqual(sorted(newIds), sorted(union));
  });

  const policy = await json('catalog/scope-policy-20261017.json');
  check('/scope/engineering_all_and_history', () => {
    assert.equal(master.scope.active_instruction_id, 'USER-20261017-CECS-ENGINEERING-ALL'); assert.deepEqual(master.external.scope_policy, policy);
    assert.deepEqual(master.scope.instruction_history, policy.instruction_history); assert.equal(policy.instruction_history.length, 2);
    assert.equal(policy.instruction_history[0].source_id, 'USER-20261017-CECS-BUILDING-STRUCTURE-ONLY'); assert.equal(policy.instruction_history[0].status, 'superseded');
    assert.equal(policy.instruction_history[0].exclusions_applied_to_master, 0); assert.equal(policy.instruction_history[1].status, 'active');
    assert.equal(policy.instruction_history[1].source_id, 'USER-20261017-CECS-ENGINEERING-ALL');
    assert.ok(!master.links.some(l => l.active === false && /非房屋结构|BUILDING-STRUCTURE-ONLY/.test(String(l.inactive_reason ?? '') + String(l.exclusion_reason ?? ''))));
  });
  const registryPath = 'catalog/download-source-region-evidence-1510.json';
  const registryBytes = await bytes(registryPath), registry = JSON.parse(registryBytes.toString('utf8'));
  const regionInputs = [
    ['search/freeze-region-metadata-1530.json', 'a2f5754e0962f20204fd05fcd17cabaec077e16035fb9cc6d08ad6e7184c1772'],
    ['search/region-metadata-20261017/university-region-evidence-proposal.json', '6588447360ea54ad0aff23e2992d0811c9d295824289bf2a5a7fcff04245fc60'],
    ['search/region-metadata-20261017/universities/official-html-observations.json', 'e6c878d58e112bba28868e323512b0308cd60b41bcebbc8b48510837648e5801'],
    ['search/region-metadata-20261017/universities/platform-identity-observations-v2.json', 'f487ff087c66b1cfe698c0386a6dfd9a8ba947799bc67582a48c6d8940b540ec'],
  ];
  check('/regions/registry_and_supplemental_selection', () => {
    assert.equal(registry.source_id, 'USER-20261017-CECS-DOWNLOAD-SOURCE-REGION');
    assert.equal(sha(registryBytes), 'f02e52478e9d05287d6651cdc2a6db20d2289fd71b20204a5f7c85452def69dc');
    assert.equal(receipts.get(registryPath)?.sha256, sha(registryBytes));
    assert.deepEqual(master.external.download_source_region_registry, registry);
    assert.deepEqual(registry.supplemental_inputs, regionInputs.map(([path, sha256]) => ({ path, sha256 })));
  });
  for (const [rel, hash] of regionInputs) {
    const content = await bytes(rel);
    check('/regions/supplemental_sha/' + esc(rel), () => {
      assert.equal(sha(content), hash); assert.equal(receipts.get(rel)?.sha256, hash);
      assert.ok(!selection.has(rel));
    });
    scan(JSON.parse(content.toString('utf8').replace(/^\uFEFF/, '')), '/region_inputs/' + esc(rel));
  }
  const regionEvidence = new Map(registry.evidence.map(e => [e.region_evidence_id, e]));
  function sourceUrl(value) {
    try { const url = new URL(value); if (!['http:', 'https:'].includes(url.protocol)) return null; url.hash = ''; return url; }
    catch { return null; }
  }
  check('/regions/each_link_evidence_and_counts', () => {
    assert.equal(master.links.length, 163); assert.equal(master.evidence.length, 1854);
    for (const l of master.links) {
      const r = l.download_source_region; assert.ok(r && ['已核实', '部分核实', '待核'].includes(r.region_status));
      assert.ok(r.province === null || typeof r.province === 'string'); assert.ok(r.city === null || typeof r.city === 'string');
      assert.ok(Array.isArray(r.region_evidence_ids) && Array.isArray(r.region_basis));
      const actualUrls = [sourceUrl(l.requested_url), sourceUrl(l.final_url)].filter(Boolean);
      const matched = registry.evidence.filter(e => actualUrls.some(u =>
        e.match_hosts.some(h => h.toLowerCase() === u.host.toLowerCase()) || (e.download_urls ?? []).some(v => sourceUrl(v)?.href === u.href)));
      assert.deepEqual(sorted(r.region_evidence_ids), sorted(matched.map(e => e.region_evidence_id)));
      assert.deepEqual(sorted(r.region_basis.map(e => e.region_evidence_id)), sorted(r.region_evidence_ids));
      const provinces = new Set(matched.map(e => e.province).filter(Boolean)), cities = new Set(matched.map(e => e.city).filter(Boolean));
      if (provinces.size > 1 || cities.size > 1) {
        assert.equal(r.region_status, '待核'); assert.equal(r.province, null); assert.equal(r.city, null);
      } else {
        assert.equal(r.province, [...provinces][0] ?? null); assert.equal(r.city, [...cities][0] ?? null);
        assert.equal(r.region_status, r.province && r.city ? '已核实' : r.province || r.city ? '部分核实' : '待核');
      }
      for (const b of r.region_basis) {
        const original = regionEvidence.get(b.region_evidence_id); assert.ok(original);
        for (const key of ['proof_url', 'proof_excerpt', 'statement_type', 'checked_at']) assert.equal(b[key], original[key] ?? null);
      }
    }
    assert.deepEqual(master.coverage.download_source_region_counts, {
      total_links: 163, province_evidenced_links: 21, city_evidenced_links: 17, fully_identified_links: 17,
      partial_links: 4, pending_links: 142, standards_with_download_links: 121,
    });
    assert.equal(master.links.filter(l => l.download_source_region.province !== null).length, 21);
    assert.equal(master.links.filter(l => l.download_source_region.city !== null).length, 17);
    const partial = master.links.filter(l => l.download_source_region.region_status === '部分核实'); assert.equal(partial.length, 4);
    for (const l of partial) {
      assert.equal(l.download_source_region.province, '陕西省'); assert.equal(l.download_source_region.city, null);
      assert.ok([l.requested_url, l.final_url].some(u => sourceUrl(u)?.host === 'eol.nwafu.edu.cn'));
    }
    const nwafu = registry.evidence.find(e => e.region_evidence_id === 'REG-SOURCE-NWAFU-EOL-20261017'); assert.equal(nwafu.city, null); assert.equal(nwafu.locality_as_published, '杨凌'); assert.ok(nwafu.proof_excerpt.includes('陕西杨凌'));
    const hpu = master.links.find(l => l.audit_id === 'R09-HPU-69-2011'); assert.equal(hpu.download_source_region.province, '河南省'); assert.equal(hpu.download_source_region.city, '焦作市'); assert.equal(hpu.http_status, 404);
  });
  check('/regions/standards_aggregate_actual_link_regions', () => {
    for (const s of master.standards) {
      const groups = s.download_source_regions; assert.ok(Array.isArray(groups));
      assert.deepEqual(sorted(groups.flatMap(g => g.link_ids)), sorted(s.link_ids));
      if (!s.link_ids.length) { assert.equal(groups.length, 0); assert.equal(s.download_source_region_summary, '尚无下载来源'); continue; }
      assert.ok(s.download_source_region_summary && groups.length);
      for (const g of groups) {
        const observedEvidence = new Set(); assert.ok(g.link_ids.length);
        for (const lid of g.link_ids) {
          const r = links.get(lid).download_source_region; assert.equal(g.region_status, r.region_status); assert.equal(g.province, r.province); assert.equal(g.city, r.city);
          r.region_evidence_ids.forEach(id => observedEvidence.add(id));
        }
        assert.deepEqual(sorted(g.evidence_ids), sorted(observedEvidence));
      }
    }
    assert.equal(master.standards.filter(s => s.link_ids.length).length, 121);
  });
  check('/sharing/transient_query_in_region_inputs', () => assert.equal(transientPaths.size, 0));
  const repeal69Bytes = await bytes('pdf-audit/evidence-85-repeal-cecs69-94.json'), repeal69 = JSON.parse(repeal69Bytes.toString('utf8'));
  check('/regression/69_historical_repeal_and_old_pdfs', () => {
    assert.equal(sha(repeal69Bytes), '442e9485aae9fed84a118ebfdc0365e80bb2328ef05ba901958274a81178f95e');
    assert.equal(repeal69.announcement_date, '2011-06-22'); assert.equal(repeal69.repeal_effective_date, '2011-10-01'); assert.equal(repeal69.pdf_physical_page, 2); assert.equal(repeal69.page_side, '左半页'); assert.equal(repeal69.printed_page, null);
    const old = standards.get('CECS-69-1994-FORMAL'), next = standards.get('CECS-69-2011-FORMAL'); assert.ok(old.current_status.includes('已废止')); assert.equal(old.withdrawal_date, '2011-10-01'); assert.equal(old.replaced_by, next.standard_id);
    assert.ok(next.current_status.startsWith('未知')); assert.ok(old.link_ids.length);
    for (const lid of baseStandards.get(old.standard_id).link_ids) assert.ok(old.link_ids.includes(lid));
    const ev = master.evidence.filter(e => e.source_id === repeal69.source_id); assert.equal(ev.length, 2);
    for (const e of ev) { assert.equal(e.pdf_page_one_based, 2); assert.equal(e.source_printed_page, null); assert.deepEqual(e.raw_record, repeal69); }
    const hpu = master.links.find(l => l.audit_id === 'R09-HPU-69-2011'); assert.equal(hpu.http_status, 404); assert.equal(hpu.recommendation, 'D');
  });
  check('/regression/608_10065_10066', () => {
    const s = standards.get('CECS-608-2019-FORMAL'); assert.equal(s.name, '绿色建筑运营后评估标准'); assert.ok(s.name_variants.includes('绿色建筑运营后评价标准'));
    assert.ok(s.name_correction_events.some(e => e.old_name === '绿色建筑运营后评价标准' && e.new_name === s.name && evidence.has(e.evidence_id)));
    for (const id of ['CECS-10065-2019-FORMAL', 'CECS-10066-2019-FORMAL']) assert.equal(standards.get(id).name, baseStandards.get(id).name);
  });
  check('/regression/102_edition', () => {
    const old = standards.get('CECS-102-2002-FORMAL'), ed = standards.get('CECS-102-2002-FORMAL-E2012');
    assert.equal(ed.year, 2002); assert.equal(ed.edition_label, '2012年版'); assert.equal(ed.published_date, null); assert.equal(ed.effective_date, null);
    assert.ok(ed.metadata_date_layers.some(l => l.context.includes('网页') && l.effective_date === '2012-04-24')); assert.ok(ed.metadata_date_layers.some(l => l.context.includes('书内') && l.effective_date === '2003-03-01'));
    assert.ok(old.issues.some(s => s.includes('未核版次'))); assert.ok(!old.link_ids.some(id => ed.link_ids.includes(id))); if (old.best_link_id) assert.notEqual(old.best_link_id, ed.best_link_id);
  });
  check('/regression/22_status', () => {
    const old = standards.get('CECS-22-2005-FORMAL'), next = standards.get('CECS-22-2024-FORMAL'); assert.ok(old.current_status.includes('已废止')); assert.equal(old.withdrawal_date, '2025-04-01'); assert.equal(old.replaced_by, next.standard_id);
    const e = master.evidence.find(e => e.source_id === 'PDF-CECS-2185-REPEAL-20261017' && e.standard_id === old.standard_id); assert.ok(e && old.status_evidence_ids.includes(e.evidence_id)); assert.equal(e.pdf_page_one_based, 5); assert.equal(e.source_printed_page, null); assert.ok(next.current_status.startsWith('未知'));
  });
  check('/regression/796_announcement_and_name_conflicts', () => {
    for (const s of master.standards.filter(s => /^CECS-796-/.test(s.standard_id))) { assert.equal(s.name, '屋面结构雪荷载设计标准'); assert.equal(s.identity_confirmed, false); assert.equal(s.version_stage, '正式性/年份冲突待核'); }
    const l = master.links.find(l => l.audit_id === 'AUD-796-ANNOUNCEMENT-QIXIN'); assert.equal(l.metadata_only, true); assert.equal(l.complete_pdf, false); assert.equal(l.recommendation, 'D'); assert.equal(l.pages, 1);
    for (const id of ['CECS-1137-2022-FORMAL', 'CECS-22-2012-FORMAL']) {
      const s = standards.get(id), b = baseStandards.get(id); assert.equal(s.name, b.name); assert.equal(s.identity_confirmed, false); assert.equal(s.name_resolution_status, b.name_resolution_status);
      for (const name of b.name_variants) assert.ok(s.name_variants.includes(name)); assert.deepEqual(s.directory_name_conflicts, b.directory_name_conflicts);
    }
  });
  check('/regression/81_mapping_and_four_metadata_routes', () => {
    assert.deepEqual(sorted(master.original_records.map(r => r.seed_id)), Array.from({ length: 81 }, (_, i) => 'S' + String(i + 1).padStart(3, '0')));
    for (const r of master.original_records) { assert.ok(standards.has(r.standard_id)); assert.ok(links.has(r.link_id)); }
    for (const id of ['CECS-10267-2023-FORMAL', 'CECS-10309-2023-FORMAL', 'CECS-10222-2022-FORMAL', 'CECS-10403-2024-FORMAL']) { assert.ok(standards.has(id)); assert.equal(standards.get(id).link_ids.length, 0); }
  });
  report.counts = { standards: master.standards.length, links: master.links.length, audits: audits.length, selected_search_files: selected.length, auxiliary_share_files: 1,
    formal_complete_links: full.length, formal_complete_versions: fullVersions.size, formal_complete_sha256: fullHashes.size, complete_drafts: drafts.length,
    directory_source_rows: master.external.directories.length, directory_observations: master.external.directories.reduce((n, r) => n + observations(r), 0),
    recent_raw_rows: rows.length, recent_resolved_rows: resolved.length, recent_unique_versions: recentIds.size, directory_net_new: directoryNew.size,
    pdf_candidate_net_new: candidateNew.size, extra_metadata_net_new: metadataNew.size, unresolved_directory_entries: master.unresolved_directory_entries.length, total_net_new: newIds.size,
    region_counts: master.coverage.download_source_region_counts, region_supplemental_files: regionInputs.length };
  // Read directly at the end, bypassing the input cache, to detect a concurrent rebuild.
  const finalHash = sha(await fs.readFile(path.join(out, 'cecs-master.json')));
  check('/snapshot/unchanged_during_validation', () => assert.equal(finalHash, report.hashes.master_sha256));
} catch { failures.push({ path: activePath }); }
report.transient_query_paths = [...transientPaths]; report.passed = failures.length === 0;
await fs.writeFile(path.join(out, 'freeze-1510-validation.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify({ passed: report.passed, output: 'catalog/freeze-1510-validation.json', hashes: report.hashes, counts: report.counts, failures, transient_query_paths: report.transient_query_paths }));
if (!report.passed) process.exitCode = 1;
