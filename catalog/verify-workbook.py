"""Read-only saved-XLSX validation using the bundled Python runtime."""
import collections
import hashlib
import json
import pathlib
import sys
import zipfile
import openpyxl
sys.stdout.reconfigure(encoding='utf-8')

root = pathlib.Path(__file__).resolve().parent
book = root / 'CECS可下载PDF总表.xlsx'
master = json.loads((root / 'cecs-master.json').read_text(encoding='utf-8'))
with zipfile.ZipFile(book) as archive:
    assert archive.testzip() is None
workbook = openpyxl.load_workbook(book, data_only=False)
assert len(workbook.worksheets) == 9
expected = {'规范总表':len(master['standards']), '已验完整PDF':master['coverage']['verified_complete_pdf_links'], '链接明细':len(master['links']), '原始映射':81, '待查与问题':len(master['issues']), '状态与来源依据':len(master['evidence']), '变更记录':len(master['change_log'])}
for name, count in expected.items():
    sheet=workbook[name]
    assert sheet['B5'].value == count, (name, sheet['B5'].value, count)
    if count:
        assert sum(sheet.cell(r,1).value is not None for r in range(9, sheet.max_row+1)) == count, name
    assert sheet.freeze_panes, name
assert [workbook['原始映射'].cell(r,1).value for r in range(9,90)] == [f'S{i:03}' for i in range(1,82)]
hyperlinks=[]
errors=[]
for sheet in workbook:
    for row in sheet:
        for cell in row:
            if cell.hyperlink:
                assert cell.hyperlink.target.startswith(('https://','http://'))
                hyperlinks.append((sheet.title,cell.coordinate,cell.hyperlink.target))
            if cell.data_type == 'e' or (isinstance(cell.value,str) and 'HYPERLINK is not implemented' in cell.value):
                errors.append((sheet.title,cell.coordinate,cell.value))
assert not errors, errors
native=json.loads((root/'native-hyperlinks.json').read_text(encoding='utf-8'))
assert len(hyperlinks)==len(native)
assert master['coverage']['verified_complete_pdf_links']==sum(l.get('complete_pdf') is True for l in master['links'])
complete_links=[link for link in master['links'] if link.get('complete_pdf')]
assert master['coverage'].get('verified_complete_unique_sha256')==len({link['sha256'] for link in complete_links})
complete_sheet=workbook['已验完整PDF']
assert collections.Counter(complete_sheet.cell(r,3).hyperlink.target for r in range(9,9+len(complete_links)))==collections.Counter(link['final_url'] for link in complete_links)
assert collections.Counter(complete_sheet.cell(r,17).value for r in range(9,9+len(complete_links)))==collections.Counter(link['sha256'] for link in complete_links)
for link in master['links']:
    if link.get('complete_pdf'):
        assert not link.get('metadata_only')
        assert link.get('version_verified') and link.get('final_url') and link.get('sha256') and link.get('pages') and link.get('pdf_bytes') and link.get('audit_id') and link.get('audit_evidence_paths'), link['link_id']
standards={s['standard_id']:s for s in master['standards']}
if 'CECS-102-2002-FORMAL-E2012' in standards:
    edition=standards['CECS-102-2002-FORMAL-E2012']
    assert edition['year']==2002 and edition['edition_label']=='2012年版'
    assert not set(edition['link_ids']) & set(standards['CECS-102-2002-FORMAL']['link_ids'])
    assert edition['published_date'] is None and edition['effective_date'] is None
if 'CECS-796-2021-FORMAL' in standards:
    assert standards['CECS-796-2021-FORMAL']['name']=='屋面结构雪荷载设计标准'
receipt={'checked_at_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'xlsx_sha256':hashlib.sha256(book.read_bytes()).hexdigest(),'bytes':book.stat().st_size,'sheets':[{ 'name':s.title,'rows':s.max_row,'columns':s.max_column,'freeze_panes':s.freeze_panes} for s in workbook], 'native_hyperlinks':len(hyperlinks),'error_cells':len(errors),'all_81_original_mappings':True,'counts_reconciled':True,'complete_pdf_required_fields':True}
(root/'workbook-validation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))
