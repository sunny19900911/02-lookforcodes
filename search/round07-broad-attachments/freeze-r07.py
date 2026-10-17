from pathlib import Path
from datetime import datetime, timezone, timedelta
import json, hashlib

base = Path(r'C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017')
search = base / 'search'
now = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
checks = []
for name in ['freeze-inputs-1320.json', 'freeze-inputs-round04.json', 'freeze-inputs-1330.json']:
    manifest = read(search / name)
    failures = []
    for item in manifest['files']:
        p = base / item['path']
        if not p.is_file() or digest(p).lower() != item['sha256'].lower():
            failures.append(item['path'])
    checks.append({'manifest': 'search/' + name, 'file_count': len(manifest['files']), 'unchanged': not failures, 'failures': failures})
assert all(c['unchanged'] for c in checks), checks
directory = read(search / 'round07-broad-attachments/directory/directory-round07.json')
records = directory['records']
assert len(records) == 137
assert all(isinstance(r['pdf_page_one_based'], int) and r['pdf_page_one_based'] > 0 and r['source_id'] and r['source_pdf'] for r in records)
assert len({(r['number'], r['year']) for r in records}) == 135
green = read(search / 'round07-broad-attachments/green/candidates-r07-green.json')
assert len(green['candidates']) == 3
assert len({r['candidate_id'] for r in green['candidates']}) == 3
assert all(r['source_id'] and r['download_url'].startswith('https://') for r in green['candidates'])
audit_evidence_path = base / 'pdf-audit/evidence-2185-repeal-cecs22-2005.json'
audit_evidence = read(audit_evidence_path)
receipt = {
    'source_id': 'SEARCH-R07-RECEIPT-2185-20261017',
    'statement_type': '原文事实（审查角色独立证据回执；检索侧未重复GET或独立目视）',
    'recorded_at': now,
    'evidence_path': 'pdf-audit/evidence-2185-repeal-cecs22-2005.json',
    'evidence_file_sha256': digest(audit_evidence_path),
    'source_id_received': audit_evidence['source_id'],
    'claim': audit_evidence['event']['claim'],
    'locator': audit_evidence['locator'],
    'pdf_sha256': audit_evidence['document']['sha256'],
    'source_url': audit_evidence['document']['final_url'],
    'boundary': '只登记历史废止事件；不据此确认2024版在2026仍现行。原PDF及PNG只留本地，不纳入冻结同步。'
}
receipt_path = search / 'round07-broad-attachments/receipt-2185.json'
receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
state = {
    'source_id': 'SEARCH-CHECKPOINT-1340-20261017', 'recorded_at': now,
    'new_pdf_candidates': 3, 'numbered_pdf_candidates': 2, 'placeholder_draft_pdf_candidates': 1,
    'new_metadata_only_records': 1, 'directory_source_records': 137,
    'directory_unique_number_years': 135, 'directory_rows_all_have_actual_pdf_physical_page': True,
    'not_in_old_round02_unique_count': directory['coverage']['not_in_round02_unique_count'],
    'not_in_old_round02_note': '仅相对该旧输入；不等于主控总库净新增数。',
    'actual_title_correction_count': 1,
    'title_correction': '608-2019 绿色建筑运营后评价标准 -> 绿色建筑运营后评估标准',
    'correction_to_early_verbal_report': '10065/10066旧冻结JSON原名称正确，本轮只重核，不是更正。',
    'standard_complete_pdf_count_added_by_search': 0,
    'audit_latest_received_checkpoint': '13:30: 9条完整链接/7版本/7哈希，具体以审查冻结为准。R07候选未包含在该数。',
    'pending_separate_batch': 'water-mep',
    'previous_freeze_integrity': checks,
    'boundary': '不穷尽；目录不是全文，历史目录状态不是2026现行性；未执行Git、外部账户访问或上传PDF原件。'
}
state_path = search / 'round07-broad-attachments/state-r07.json'
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
discussion = '''# 13:40 检索检查点

source_id: SEARCH-DISCUSSION-1340-20261017；记录时间：%s。

本轮将方法从反复追查661缺页与102扫描本转为公开机构附件及目录逐页取证。已固定3条新PDF候选（10025-2019、727-2020、编号占位的零碳工业建筑草案）、1条10026-2025平台元数据。候选未独立审查，不增加完整PDF数。10026发布日网页字段冲突保留；公告点击跳登录后停止。T/WJX004-2024仅引用CECS，已排除为CECS全文。

目录批次137条来源记录、135个唯一编号年份，全部有实际PDF物理页。相比旧round02有85个未见编号年份，不能当作主库净新增数。湖北118条、新疆19条；保留1075-2022与1145-2022两项跨源重复证据。新疆1031未标年份不猜；新疆尚未全目录审完，不宣称无漏项。

实际名称更正只有608-2019“后评价”→“后评估”，湖北PDF物理22/印刷21。早先口头将10065/10066也称更正，已回查并纠正：旧JSON名称本来正确，均在物理38/印刷37重核。不改任何旧冻结输入。

已接收审查角色的第2185号公告PDF内证据：22-2024 PDF顺序第5页（无印刷页码），22:2005自2025-04-01同时废止；仅为历史废止事件，不确认新版2026现行性。审查最近固定数为9条完整链接/7个版本/7个哈希，检索侧不自行升级质量。

给排水/机电批次仍在收尾，将另建追加冻结。下一步由目录角色合并、审查角色GET和完整性检查，主控单独串行GitHub；本角色不执行Git，不复制原PDF/页面图片进同步批次。
''' % now
discussion_path = search / 'discussion-1340.md'
discussion_path.write_text(discussion, encoding='utf-8')
paths = [
    'round07-broad-attachments/directory/directory-round07.json',
    'round07-broad-attachments/directory/corrections-round02.json',
    'round07-broad-attachments/green/candidates-r07-green.json',
    *['round07-broad-attachments/green/web-r%d.json' % n for n in range(34,40)],
    'round07-broad-attachments/receipt-2185.json',
    'round07-broad-attachments/state-r07.json',
    'discussion-1340.md'
]
files = [{'path': 'search/' + rel, 'sha256': digest(search / rel), 'bytes': (search / rel).stat().st_size} for rel in paths]
manifest = {'producer': 'search', 'checkpoint': '13:40', 'checked_at': now, 'frozen': True,
    'input_file_count': len(files), 'previous_freeze_integrity': checks,
    'note': '固定后不再改。本批仅元数据/查询响应/定位/回执，无PDF、PNG、HTML或凭据。water-mep另批；目录非全文；候选未审。', 'files': files}
manifest_path = search / 'freeze-inputs-1340.json'
assert not manifest_path.exists(), 'Never overwrite a frozen manifest'
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'manifest': str(manifest_path), 'sha256': digest(manifest_path), 'files': len(files), 'state': state}, ensure_ascii=False, indent=2))
