"""Authorized 14:10 checkpoint; eight immutable R08 records, R09 stays pending."""
import copy
import datetime
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
PATH = ROOT/'audit-results.json'
INPUT = ROOT/'audit-pending-round06-freeze-1410.json'
FREEZE = ROOT/'audit-results-freeze-1410.json'
RECEIPT = ROOT/'freeze-1410-receipt.json'
OLD_SHA = '400cf857fd7d1a084bb44cb4f0b387cda220f679e88370784296314f96386d33'
INPUT_SHA = '455b212b19fd80b644aa82c64e5592d07e35fc27fd462c99571dbd6fdebb4b57'
before = PATH.read_bytes()
input_bytes = INPUT.read_bytes()
assert hashlib.sha256(before).hexdigest() == OLD_SHA
assert hashlib.sha256(input_bytes).hexdigest() == INPUT_SHA
assert (ROOT/'audit-results-freeze-1350.json').read_bytes() == before
assert not FREEZE.exists() and not RECEIPT.exists()
base = json.loads(before)
pending = json.loads(input_bytes)
assert len(base['results']) == 40 and len(pending['results']) == 8
assert not {x['candidate_id'] for x in base['results']}.intersection(x['candidate_id'] for x in pending['results'])
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
for row in pending['results']:
    r = copy.deepcopy(row)
    r.setdefault('audit_history',[]).append({'checked_at':NOW,'method':'主控明确批准14:10固定八GET回灌','outcome':'追加原始审查与证据字段；报批/送审草案内容完整单列，287稿型未定仍C'})
    base['results'].append(r)
base.update(updated_at=NOW,checkpoint='1410',handoff_state='14:10冻结，待主控本轮本地封版；后续R09独立pending')
base['counting_rules']['complete_draft'] = 'draft_content_complete=true单列并保留实际报批稿/送审稿阶段；complete_pdf=false不表示草案内容不完整'
base['counting_rules']['reading_quality'] = 'A/B/C/D推荐与稿型、完整性分别保存；B16含完整报批稿与完整送审稿阅读质量各1，不计正式完整集合'
complete = [r for r in base['results'] if r.get('complete_pdf') is True]
drafts = [r for r in base['results'] if r.get('draft_content_complete') is True]
ratings = {k:sum(r.get('recommendation')==k for r in base['results']) for k in ['A','B','C','D']}
assert len(base['results']) == len({r['candidate_id'] for r in base['results']}) == 48
assert len(complete) == 14 and all(r.get('version_verified') is True for r in complete)
assert len({r['standard_key'] for r in complete}) == len({r['sha256'] for r in complete}) == 12
assert ratings == {'A':0,'B':16,'C':15,'D':17}
assert len(drafts) == 2 and {r['version_class'] for r in drafts} == {'报批稿','送审稿'}
assert all(r['complete_pdf'] is False for r in drafts)
assert next(r for r in base['results'] if r['candidate_id']=='R08-WH-003')['recommendation']=='C'
assert not next(r for r in base['results'] if r['candidate_id']=='R08-WH-003').get('draft_content_complete')
assert json.loads(before)['results'] == base['results'][:40]
out = json.dumps(base,ensure_ascii=False,indent=2).encode('utf-8')
sha = hashlib.sha256(out).hexdigest()
receipt = {
    'checkpoint':'2026-10-17T14:10:00+08:00','frozen_at':NOW,'updated_at':NOW,
    'before_sha256':OLD_SHA,'sha256':sha,'input_snapshot':INPUT.name,'input_sha256':INPUT_SHA,
    'result_count':48,'complete_link_count':14,'complete_version_count':12,'complete_hash_count':12,
    'complete_draft_count':2,'complete_drafts':[{'candidate_id':r['candidate_id'],'version_class':r['version_class']} for r in drafts],
    'rating_counts':ratings,'rating_scope_note':'B16包括14正式完整链接及2件完整草案阅读质量（报批/送审各1）',
    'metadata_only_count':sum(bool(r.get('metadata_only')) for r in base['results']),
    'additions':8,'replacements':0,'merged_candidate_ids':[r['candidate_id'] for r in pending['results']],
    'old_freeze':'audit-results-freeze-1350.json','current_freeze':FREEZE.name,
    'old40_records_unchanged':True,'history_preserved':True,
    'new_complete_candidates':['R08-CNASS-212-2006','R08-CNASS-235-2008','R08-WH-001','R08-WH-002'],
    'quality_limits':'数字重排本仅按所述本件目录范围闭合；122页脚裁字限制保留；333/287仍C，287不能仅凭占位号判草案；送审稿原稿问题保留。',
    'canonical_frozen_until':'主控本轮本地封版；后续新GET另存独立pending',
    'publication_status':'本角色未操作Git或远端；此1410快照发布状态由主控另登记',
}
PATH.write_bytes(out)
FREEZE.write_bytes(out)
RECEIPT.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
assert PATH.read_bytes() == FREEZE.read_bytes()
assert hashlib.sha256(INPUT.read_bytes()).hexdigest() == INPUT_SHA
assert hashlib.sha256((ROOT/'audit-results-freeze-1350.json').read_bytes()).hexdigest() == OLD_SHA
print(json.dumps(receipt,ensure_ascii=False))
