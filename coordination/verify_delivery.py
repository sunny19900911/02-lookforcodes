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
sha = hashlib.sha256(raw).hexdigest()
assert sha == receipt['xlsx_sha256'], 'Workbook changed after catalog validation'
workbook = openpyxl.load_workbook(book, read_only=False, data_only=False)
assert len(workbook.sheetnames) == 9
originals = master['original_records']
assert len(originals) == 81
ids = {s['standard_id'] for s in master['standards']}
assert len(ids) == len(master['standards']), 'Duplicate stable identity'
links = {l['link_id']: l for l in master['links']}
assert len(links) == len(master['links']), 'Duplicate link identity'
complete = [l for l in links.values() if l.get('complete_pdf')]
assert len(complete) == master['coverage']['verified_complete_pdf_links']
for link in links.values():
    assert set(link['standard_ids']).issubset(ids), 'Orphan link'
for link in complete:
    assert link['recommendation'] in ('A', 'B')
    assert link['pages'] > 3 and link['pdf_bytes'] > 0 and len(link['sha256']) == 64
    assert link['final_url'].startswith(('https://', 'http://'))
    assert link['completeness'] and link['checked_at'] and link['version_match']
for standard in master['standards']:
    name = (standard.get('name') or '').strip()
    if standard.get('standard_number'):
        assert not (name.startswith('关于发布') or name.endswith('公告')), 'Announcement document title used as standard title'
    best = standard.get('best_link_id')
    if best:
        assert best in links and links[best].get('complete_pdf'), 'Unverified link recommended'
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
    'grade_counts_for_complete': dict(collections.Counter(l['recommendation'] for l in complete)),
    'checks': ['ZIP integrity', 'catalog SHA256 receipt', '9 readable worksheets', '81 original mappings',
               'stable IDs unique', 'link IDs unique and no orphan', 'only verified complete links recommended',
               'required PDF evidence fields', 'standard title excludes announcement document names',
               'all sheet counts reconcile', 'native hyperlinks', 'no Excel errors'],
    'scope_limit': 'Output data consistency only. Independent PDF conclusions remain attributable to pdf-audit evidence; not proof of all-web coverage or current standard applicability.'}
(REPO / 'coordination' / 'delivery-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'ok': True, 'sha256': sha, 'links': len(links), 'complete': len(complete), 'native_hyperlinks': native}))
