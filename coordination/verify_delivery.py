"""Read-only independent verification of the catalog delivery snapshot."""
import collections
import datetime
import hashlib
import json
from pathlib import Path
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
assert len(complete_drafts) == master['coverage'].get('verified_complete_draft_pdf_links', 0)
assert len(complete) == master['coverage']['verified_complete_pdf_links']
for link in links.values():
    assert set(link['standard_ids']).issubset(ids), 'Orphan link'
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
assert native == receipt['native_hyperlinks'] and errors == 0
result = {'checked_at': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
    'xlsx_sha256': sha, 'bytes': len(raw), 'sheets': sheet_counts,
    'coverage': master['coverage'], 'native_hyperlinks': native, 'error_cells': errors,
    'complete_draft_links': len(complete_drafts),
    'grade_counts_for_complete': dict(collections.Counter(l['recommendation'] for l in complete)),
    'checks': ['ZIP integrity', 'catalog SHA256 receipt', 'readable worksheets match build receipt', '81 original mappings',
               'stable IDs unique', 'link IDs unique and no orphan', 'only verified complete links recommended',
               'required PDF evidence fields', 'draft content completeness separate from formal status',
               'standard title excludes announcement document names',
               'all sheet counts reconcile', 'native hyperlinks', 'no Excel errors'],
    'scope_limit': 'Output data consistency only. Independent PDF conclusions remain attributable to pdf-audit evidence; not proof of all-web coverage or current standard applicability.'}
(REPO / 'coordination' / 'delivery-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'ok': True, 'sha256': sha, 'links': len(links), 'complete': len(complete), 'native_hyperlinks': native}))
