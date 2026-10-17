import test from 'node:test';
import assert from 'node:assert/strict';
import { applyDownloadSourceRegions } from './download-source-regions.mjs';

const sourceId = 'USER-20261017-CECS-DOWNLOAD-SOURCE-REGION';
const evidence = (id, host, province, city, extra = {}) => ({
  region_evidence_id: id, match_hosts: host ? [host] : [], province, city,
  source_entity: id + '机构', proof_url: 'https://proof.example/' + id,
  proof_excerpt: '机构公开地址原文', statement_type: '原文事实', checked_at: '2026-10-17T15:10:00+08:00', ...extra,
});
const model = links => ({
  standards: [{ standard_id: 'S1', link_ids: links.map(l => l.link_id) }, { standard_id: 'S2', link_ids: [] }],
  links, coverage: { registered_standard_versions: 2, registered_links: links.length, verified_complete_pdf_links: 1, verified_complete_standard_versions: 1 },
  external: { existing: true },
});
const apply = (m, rows) => applyDownloadSourceRegions(m, { source_id: sourceId, evidence: rows });

test('one standard keeps independently evidenced Beijing and Tianjin sources', () => {
  const m = model([{ link_id: 'BJ', requested_url: 'https://bj.example/a.pdf' }, { link_id: 'TJ', final_url: 'https://tj.example/b.pdf' }]);
  apply(m, [evidence('E-BJ', 'bj.example', '北京市', '北京市'), evidence('E-TJ', 'tj.example', '天津市', '天津市')]);
  assert.deepEqual(m.links.map(l => l.download_source_region.region_status), ['已核实', '已核实']);
  assert.deepEqual(m.standards[0].download_source_regions.map(g => [g.province, g.link_ids, g.evidence_ids]), [
    ['北京市', ['BJ'], ['E-BJ']], ['天津市', ['TJ'], ['E-TJ']],
  ]);
  assert.match(m.standards[0].download_source_region_summary, /北京市.*天津市/);
  assert.deepEqual(m.standards[1].download_source_regions, []);
  assert.equal(m.standards[1].download_source_region_summary, '尚无下载来源');
  assert.equal(m.external.download_source_region_registry.source_id, sourceId);
});

test('a CDN or raw IP never inherits the region of a parent directory or source page', () => {
  const m = model([
    { link_id: 'CDN', requested_url: 'https://files.cdn.example/a.pdf', source_page: 'https://bj.example/directory' },
    { link_id: 'IP', requested_url: 'https://192.0.2.1/a.pdf', source_page: 'https://bj.example/' },
    { link_id: 'DISCOVERY', discovery_url: 'https://bj.example/a.pdf' },
  ]);
  apply(m, [evidence('E-BJ', 'bj.example', '北京市', '北京市')]);
  for (const l of m.links) assert.deepEqual(l.download_source_region, {
    region_status: '待核', province: null, city: null, source_entity: null, region_evidence_ids: [], region_basis: [],
  });
  assert.equal(m.standards[0].download_source_regions.length, 1);
  assert.deepEqual(m.standards[0].download_source_regions[0].link_ids, ['CDN', 'IP', 'DISCOVERY']);
});

test('an explicit attachment URL proves only that URL, preserving its resource query', () => {
  const m = model([
    { link_id: 'MATCH', requested_url: 'https://shared.example/file?id=first#page=2' },
    { link_id: 'OTHER', requested_url: 'https://shared.example/file?id=other' },
  ]);
  apply(m, [evidence('E-APPENDIX', null, '浙江省', '杭州市', { download_urls: ['https://shared.example/file?id=first'] })]);
  assert.equal(m.links[0].download_source_region.city, '杭州市');
  assert.equal(m.links[0].download_source_region.region_basis[0].matches[0].match_type, 'explicit_download_url');
  assert.equal(m.links[1].download_source_region.region_status, '待核');
});

test('host matching is exact, case insensitive, and checks requested and final hosts', () => {
  const m = model([
    { link_id: 'UPPER', requested_url: 'https://BJ.EXAMPLE/a.pdf', final_url: 'https://cdn.example/a.pdf' },
    { link_id: 'SUBDOMAIN', requested_url: 'https://sub.bj.example/a.pdf' },
    { link_id: 'SUFFIX', requested_url: 'https://bj.example.attacker.example/a.pdf' },
    { link_id: 'FINAL', requested_url: 'https://cdn.example/b.pdf', final_url: 'https://bj.example/b.pdf' },
  ]);
  apply(m, [evidence('E-BJ', 'BJ.EXAMPLE', '北京市', '北京市')]);
  assert.deepEqual(m.links.map(l => l.download_source_region.region_status), ['已核实', '待核', '待核', '已核实']);
});

test('partial province and wholly unknown sources stay distinct in counts and groups', () => {
  const m = model([
    { link_id: 'PROVINCE', requested_url: 'https://hb.example/a.pdf' },
    { link_id: 'CITY', requested_url: 'https://city.example/a.pdf' },
    { link_id: 'UNKNOWN', requested_url: 'not a URL' },
  ]);
  apply(m, [evidence('E-HB', 'hb.example', '河北省', null), evidence('E-CITY', 'city.example', null, '石家庄市')]);
  assert.equal(m.links[0].download_source_region.city, null);
  assert.equal(m.links[1].download_source_region.province, null);
  assert.deepEqual(m.coverage.download_source_region_counts, {
    total_links: 3, province_evidenced_links: 1, city_evidenced_links: 1, fully_identified_links: 0,
    partial_links: 2, pending_links: 1, standards_with_download_links: 1,
  });
  assert.equal(m.standards[0].download_source_regions.length, 3);
});

test('regional conflict clears chosen values and retains every conflicting evidence', () => {
  const m = model([{ link_id: 'CONFLICT', requested_url: 'https://bj.example/a.pdf', final_url: 'https://tj.example/a.pdf' }]);
  apply(m, [evidence('E-BJ', 'bj.example', '北京市', '北京市'), evidence('E-TJ', 'tj.example', '天津市', '天津市')]);
  const r = m.links[0].download_source_region;
  assert.equal(r.region_status, '待核'); assert.equal(r.province, null); assert.equal(r.city, null); assert.equal(r.source_entity, null);
  assert.deepEqual(r.region_evidence_ids, ['E-BJ', 'E-TJ']); assert.equal(r.region_basis.length, 2);
  assert.deepEqual(m.standards[0].download_source_regions[0].evidence_ids, ['E-BJ', 'E-TJ']);
});

test('same region and compatible partial evidence do not create a conflict', () => {
  const m = model([{ link_id: 'SAME', requested_url: 'https://one.example/a.pdf', final_url: 'https://two.example/a.pdf' }]);
  apply(m, [evidence('E1', 'one.example', '浙江省', '杭州市'), evidence('E2', 'two.example', '浙江省', null), evidence('E3', 'one.example', '浙江省', '杭州市')]);
  const r = m.links[0].download_source_region;
  assert.equal(r.region_status, '已核实'); assert.equal(r.province, '浙江省'); assert.equal(r.city, '杭州市');
  assert.deepEqual(r.region_evidence_ids, ['E1', 'E2', 'E3']);
  assert.deepEqual(m.standards[0].download_source_regions[0].source_entities, ['E1机构', 'E2机构', 'E3机构']);
});

test('region annotation is idempotent and preserves quality, active state and coverage totals', () => {
  const m = model([{
    link_id: 'A', requested_url: 'https://bj.example/a.pdf', active: false, complete_pdf: false,
    version_verified: true, recommendation: 'D', body_reading_recommendation: 'B', body_searchable: false,
    quality_anomalies: [{ kind: 'missing_explanation', page: 30 }], audit_result: { recommendation: 'D' },
  }]);
  const before = structuredClone(m), registry = { source_id: sourceId, evidence: [evidence('E', 'bj.example', '北京市', '北京市')] }, originalRegistry = structuredClone(registry);
  assert.equal(applyDownloadSourceRegions(m, registry), m);
  const once = structuredClone(m); applyDownloadSourceRegions(m, registry); assert.deepEqual(m, once); assert.deepEqual(registry, originalRegistry);
  const restored = structuredClone(m); delete restored.links[0].download_source_region;
  for (const s of restored.standards) { delete s.download_source_regions; delete s.download_source_region_summary; }
  delete restored.coverage.download_source_region_counts; delete restored.external.download_source_region_registry;
  assert.deepEqual(restored, before);
});
