"""Read-only independent verification of the catalog delivery snapshot."""
import collections
import datetime
import hashlib
import json
from pathlib import Path
import re
import zipfile
import openpyxl

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parent
catalog = ROOT / 'catalog'
book = next(catalog.glob('*.xlsx'))
raw = book.read_bytes()
assert zipfile.ZipFile(book).testzip() is None
master = json.loads((catalog / 'cecs-master.json').read_text(encoding='utf-8-sig'))
receipt = json.loads((catalog / 'workbook-validation.json').read_text(encoding='utf-8-sig'))
build = json.loads((catalog / 'workbook-build-receipt.json').read_text(encoding='utf-8-sig'))
sha = hashlib.sha256(raw).hexdigest()
assert sha == receipt['xlsx_sha256'], 'Workbook changed after catalog validation'
workbook = openpyxl.load_workbook(book, read_only=False, data_only=False)
assert workbook.sheetnames == [s['name'] for s in build['sheets']]
assert len(workbook.sheetnames) >= 9
originals = master['original_records']
assert len(originals) == 81
ids = {s['standard_id'] for s in master['standards']}
assert len(ids) == len(master['standards']), 'Duplicate stable identity'
links = {l['link_id']: l for l in master['links']}
assert len(links) == len(master['links']), 'Duplicate link identity'
complete = [l for l in links.values() if l.get('complete_pdf')]
complete_drafts = [l for l in links.values() if l.get('draft_content_complete')]
audits = master.get('external', {}).get('audit', [])
audit_ids = [a.get('audit_id') or a.get('candidate_id') for a in audits]
assert len(audits) == master['coverage']['independent_audit_results']
assert all(audit_ids) and len(set(audit_ids)) == len(audit_ids), 'Duplicate or missing audit identity'
temporary_query = re.compile(r'[?&](?:uhash|access_token|auth_token|api_key|signature|x-amz-signature)=[^&\s"<>]+', re.I)
assert not temporary_query.search(json.dumps(master, ensure_ascii=False)), 'Temporary download parameter in delivery data'
body_quality_checks = []
region_counts = None
registry = master.get('external', {}).get('download_source_region_registry')
if registry is not None:
    registry_ids = {row['region_evidence_id'] for row in registry.get('evidence', [])}
    assert len(registry_ids) == len(registry.get('evidence', [])), 'Duplicate source-region evidence identity'
    regions = []
    for link in links.values():
        region = link.get('download_source_region')
        assert isinstance(region, dict), 'Missing download-source region annotation'
        assert set(region.get('region_evidence_ids', [])).issubset(registry_ids), 'Unresolved source-region evidence'
        basis = region.get('region_basis', [])
        if region.get('province') or region.get('city'):
            assert region.get('region_evidence_ids') and basis, 'Assigned region without evidence'
            assert any(item.get('proof_url') and item.get('proof_excerpt') for item in basis), 'Assigned region lacks quoted source proof'
        else:
            assert region.get('region_status') == '待核', 'Unknown source region presented as verified'
        regions.append(region)
    for standard in master['standards']:
        grouped = [lid for group in standard.get('download_source_regions', []) for lid in group['link_ids']]
        assert len(grouped) == len(set(grouped))
        assert set(grouped) == set(standard.get('link_ids', [])), 'Standard region summary borrows or loses download links'
        if not standard.get('link_ids'):
            assert not standard.get('download_source_regions'), 'Directory region assigned without any download source'
    region_counts = master['coverage']['download_source_region_counts']
    assert region_counts['total_links'] == len(links)
    assert region_counts['province_evidenced_links'] == sum(bool(r.get('province')) for r in regions)
    assert region_counts['city_evidenced_links'] == sum(bool(r.get('city')) for r in regions)
    for key, value in (('fully_identified_links', '已核实'), ('partial_links', '部分核实'), ('pending_links', '待核')):
        assert region_counts[key] == sum(r.get('region_status') == value for r in regions)
assert len(complete_drafts) == master['coverage'].get('verified_complete_draft_pdf_links', 0)
assert len(complete) == master['coverage']['verified_complete_pdf_links']
for link in links.values():
    assert set(link['standard_ids']).issubset(ids), 'Orphan link'
    observed = link.get('audit_result') or {}
    if str(observed.get('audit_id', '')).startswith('R11-'):
        for field in ('body_reading_recommendation', 'body_searchable', 'body_text_layer', 'quality_anomalies'):
            if observed.get(field) is not None:
                assert link.get(field) == observed[field], f'Lost independent audit field: {field}'
        if observed.get('audit_id') == 'R11-1555-2024-FAIUSR':
            assert link.get('recommendation') == 'D' and not link.get('complete_pdf')
            assert str(link.get('body_reading_recommendation', '')).startswith('B')
        if observed.get('audit_id') == 'R11-200-2006-DLSSYHT':
            assert link.get('recommendation') == 'D' and not link.get('complete_pdf')
            assert link.get('body_reading_recommendation') is None, 'Invented body recommendation'
        if observed.get('audit_id') == 'R11-31-2017-GUANGYUXC':
            assert link.get('pages') is None and not link.get('complete_pdf'), 'Main-link pages inherited by failed alternate'
        body_quality_checks.append(observed['audit_id'])
    if observed.get('audit_id') in ('R11-1555-2024-FAIUSR', 'R09-WM-001'):
        assert all('DRAFT' not in sid for sid in link['standard_ids']), 'Negated draft observation misclassified as draft identity'
for link in complete:
    assert link['recommendation'] in ('A', 'B')
    assert link['pages'] > 3 and link['pdf_bytes'] > 0 and len(link['sha256']) == 64
    assert link['final_url'].startswith(('https://', 'http://'))
    assert link['completeness'] and link['checked_at'] and link['version_match']
for link in complete_drafts:
    assert not link.get('complete_pdf'), 'Draft incorrectly included in formal complete collection'
    assert link.get('version_class') or link.get('draft_stage'), 'Complete draft missing version class'
    assert link['recommendation'] in ('A', 'B')
    assert link['pages'] > 3 and link['pdf_bytes'] > 0 and len(link['sha256']) == 64
for standard in master['standards']:
    name = (standard.get('name') or '').strip()
    if standard.get('standard_number'):
        assert not (name.startswith('关于发布') or name.endswith('公告')), 'Announcement document title used as standard title'
    best = standard.get('best_link_id')
    if best:
        assert best in links, 'Best link missing'
        if not links[best].get('complete_pdf'):
            assert links[best].get('draft_content_complete') and any(
                word in str(standard.get('version_stage', '')) for word in ('草案', '报批', '送审', '征求', 'DRAFT')
            ), 'Unverified or unclassified draft link recommended'
sheet_counts = {}
native = errors = 0
for sheet in workbook:
    expected = sheet['B5'].value
    table = next(iter(sheet.tables.values()))
    table_rows = openpyxl.utils.cell.range_boundaries(table.ref)[3] - 8
    assert expected == table_rows, f'Count mismatch: {sheet.title}'
    sheet_counts[sheet.title] = expected
    for row in sheet:
        for cell in row:
            native += bool(cell.hyperlink)
            errors += cell.data_type == 'e'
            if isinstance(cell.value, str):
                assert '[object Object]' not in cell.value, f'Unformatted evidence object in worksheet: {sheet.title}'
            if cell.hyperlink and cell.hyperlink.target:
                assert not temporary_query.search(cell.hyperlink.target), 'Temporary download parameter in workbook hyperlink'
assert native == receipt['native_hyperlinks'] and errors == 0
if registry is not None:
    assert sheet_counts.get('地区下载索引') == len(links), 'Regional index does not contain one row per download link'
result = {'checked_at': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
    'xlsx_sha256': sha, 'bytes': len(raw), 'sheets': sheet_counts,
    'coverage': master['coverage'], 'native_hyperlinks': native, 'error_cells': errors,
    'complete_draft_links': len(complete_drafts),
    'body_quality_checks': body_quality_checks,
    'download_source_region_counts': region_counts,
    'grade_counts_for_complete': dict(collections.Counter(l['recommendation'] for l in complete)),
    'checks': ['ZIP integrity', 'catalog SHA256 receipt', 'readable worksheets match build receipt', '81 original mappings',
               'stable IDs unique', 'link IDs unique and no orphan', 'only verified complete links recommended',
               'required PDF evidence fields', 'draft content completeness separate from formal status',
               'standard title excludes announcement document names',
               'unique independent audits', 'body reading quality separate from full-document completeness',
               'negative draft observations do not create draft identities',
               'delivery metadata and workbook links exclude temporary download parameters',
               'download-source regions have resolvable evidence and one index row per link',
               'all sheet counts reconcile', 'native hyperlinks', 'no Excel errors'],
    'scope_limit': 'Output data consistency only. Independent PDF conclusions remain attributable to pdf-audit evidence; not proof of all-web coverage or current standard applicability.'}
(REPO / 'coordination' / 'delivery-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'ok': True, 'sha256': sha, 'links': len(links), 'complete': len(complete), 'native_hyperlinks': native}))
