"""Authorized 13:50 checkpoint merge from immutable seven-GET snapshot."""
import collections
import copy
import datetime
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
CANONICAL = ROOT / 'audit-results.json'
INPUT = ROOT / 'audit-pending-round05-freeze-1350.json'
FREEZE = ROOT / 'audit-results-freeze-1350.json'
RECEIPT = ROOT / 'freeze-1350-receipt.json'
OLD_SHA = '84e4361fbbcdee054efb3ac89e5610001df33e049db3271ba2f2fd1616686629'
INPUT_SHA = '90081712aea2c2ddb78202101d3e31753828ed6e663af87a139ec9e007e7dcf8'

before_bytes = CANONICAL.read_bytes()
input_bytes = INPUT.read_bytes()
assert hashlib.sha256(before_bytes).hexdigest() == OLD_SHA
assert hashlib.sha256(input_bytes).hexdigest() == INPUT_SHA
assert (ROOT / 'audit-results-freeze-1330.json').read_bytes() == before_bytes
assert not FREEZE.exists() and not RECEIPT.exists()
canonical = json.loads(before_bytes)
pending = json.loads(input_bytes)
assert len(canonical['results']) == 33 and len(pending['results']) == 7
ids = {x['candidate_id'] for x in canonical['results']}
assert not ids.intersection(x['candidate_id'] for x in pending['results'])
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
for record in pending['results']:
    row = copy.deepcopy(record)
    row.setdefault('audit_history', []).append({
        'checked_at': NOW,
        'method': '主控明确批准13:50固定七条GET回灌；原始审查及证据字段全部保留',
        'outcome': '新增候选实测；草案内容完整与正式完整计数分开',
    })
    canonical['results'].append(row)

canonical.update(updated_at=NOW, checkpoint='1350', handoff_state='13:50冻结，待主控本轮本地封版；后续增量另存')
canonical['counting_rules'] = {
    'formal_complete_pdf': 'complete_pdf=true且version_verified=true；正式标准全文集合，不含报批稿/占位编号',
    'complete_draft': 'draft_content_complete=true单列；complete_pdf=false不表示草案内容不完整',
    'draft_version_verified': '仅核对文件草案身份，不指正式批准、编号或现行性',
    'reading_quality': 'A/B/C/D阅读推荐与稿型、完整性分别保存；本轮零碳报批稿B仅指草案阅读质量',
}
complete = [x for x in canonical['results'] if x.get('complete_pdf') is True]
drafts = [x for x in canonical['results'] if x.get('draft_content_complete') is True]
ratings = {k: sum(x.get('recommendation') == k for x in canonical['results']) for k in ['A','B','C','D']}
assert len(canonical['results']) == len({x['candidate_id'] for x in canonical['results']}) == 40
assert len(complete) == 10
assert all(x.get('version_verified') is True for x in complete)
assert len({x['standard_key'] for x in complete}) == 8
assert len({x['sha256'] for x in complete}) == 8
assert ratings == {'A':0,'B':11,'C':13,'D':16}
assert len(drafts) == 1 and drafts[0]['version_class'] == '报批稿'
assert drafts[0]['draft_stage'] == '报批稿' and drafts[0]['complete_pdf'] is False
assert '非正式标准全文' in drafts[0]['completeness']
assert all(a == b for a,b in zip(json.loads(before_bytes)['results'],canonical['results'][:33]))

after_bytes = json.dumps(canonical,ensure_ascii=False,indent=2).encode('utf-8')
after_sha = hashlib.sha256(after_bytes).hexdigest()
receipt = {
    'checkpoint':'2026-10-17T13:50:00+08:00','frozen_at':NOW,'updated_at':NOW,
    'before_sha256':OLD_SHA,'sha256':after_sha,
    'input_snapshot':INPUT.name,'input_sha256':INPUT_SHA,
    'result_count':40,'complete_link_count':10,'complete_version_count':8,'complete_hash_count':8,
    'complete_draft_count':1,'complete_draft_candidate_ids':[x['candidate_id'] for x in drafts],
    'rating_counts':ratings,'rating_scope_note':'B11包含正式标准10条及完整报批稿阅读质量1条；草案不计正式完整集合',
    'metadata_only_count':sum(bool(x.get('metadata_only')) for x in canonical['results']),
    'additions':7,'replacements':0,'merged_candidate_ids':[x['candidate_id'] for x in pending['results']],
    'old_freeze':'audit-results-freeze-1330.json','current_freeze':FREEZE.name,
    'history_preserved':True,'old33_records_unchanged':True,
    'new_complete_candidate':'R07-G4-10025-2019-DLSSYHT',
    'quality_limits':'10025水印备用；完整报批单列、导航及原稿小错保留；41/164空白页未证维持C；3次403不推断登录或永久失效。',
    'canonical_frozen_until':'主控本轮本地封版；新审查另存后续增量文件',
    'publication_status':'本角色未操作Git或远端，发布状态由主控单独登记',
}
CANONICAL.write_bytes(after_bytes)
FREEZE.write_bytes(after_bytes)
RECEIPT.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
assert hashlib.sha256(INPUT.read_bytes()).hexdigest() == INPUT_SHA
assert hashlib.sha256((ROOT/'audit-results-freeze-1330.json').read_bytes()).hexdigest() == OLD_SHA
assert CANONICAL.read_bytes() == FREEZE.read_bytes()
print(json.dumps(receipt,ensure_ascii=False))
