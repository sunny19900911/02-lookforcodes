import copy,datetime,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
path=ROOT/'audit-results.json';before_bytes=path.read_bytes();before_sha=hashlib.sha256(before_bytes).hexdigest()
assert before_sha=='46147add21cc3ab5453f683ac816c8763fddc31a845baa2908adf2e902642f1d',before_sha
canonical=json.loads(before_bytes);pending=json.loads((ROOT/'audit-pending-round03.json').read_text(encoding='utf-8'))
deferred_id='R03-G1-22-2024-ZGB-202603'
entries=[r for r in pending['results'] if r['candidate_id']!=deferred_id]
deferred=[r for r in pending['results'] if r['candidate_id']==deferred_id]
assert len(entries)==10
NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
merged={r['candidate_id']:copy.deepcopy(r) for r in canonical['results']}
for record in entries:
    ident=record['candidate_id'];prior=merged.get(ident);replacement=copy.deepcopy(record)
    # Keep each historical event once, even if already copied into the pending replacement.
    history=(prior or {}).get('audit_history',[])+replacement.get('audit_history',[]);seen=set();combined=[]
    for event in history:
        key=json.dumps(event,ensure_ascii=False,sort_keys=True)
        if key not in seen:combined.append(event);seen.add(key)
    combined.append({'checked_at':NOW,'method':'主控13:20固定截点回灌；保留原GET与逐次审查history','outcome':'替换既有审查' if prior else '追加新候选实测'})
    replacement['audit_history']=combined
    if replacement.get('http_status')==403:replacement['download_status']='本次HTTP403访问受限，是否需登录未知'
    merged[ident]=replacement
canonical['results']=list(merged.values());canonical['updated_at']=NOW;canonical['handoff_state']='13:20冻结，待主控同步完成';canonical['checkpoint']='1320'
assert len(canonical['results'])==31
assert sum(bool(r.get('complete_pdf')) for r in canonical['results'])==8
assert len({r['standard_key'] for r in canonical['results'] if r.get('complete_pdf')})==6
after_bytes=json.dumps(canonical,ensure_ascii=False,indent=2).encode('utf-8');after_sha=hashlib.sha256(after_bytes).hexdigest()
path.write_bytes(after_bytes);(ROOT/'audit-results-freeze-1320.json').write_bytes(after_bytes)
receipt={'checkpoint':'2026-10-17T13:20:00+08:00','frozen_at':NOW,'before_sha256':before_sha,'sha256':after_sha,'updated_at':NOW,'result_count':31,'complete_link_count':8,'complete_version_count':6,'complete_hash_count':6,'merged_candidate_ids':[r['candidate_id'] for r in entries],'replacements':7,'additions':3,'deferred_candidate_ids':[r['candidate_id'] for r in deferred],'old_freeze':'audit-results-freeze-1310.json','current_freeze':'audit-results-freeze-1320.json','history_preserved':True}
(ROOT/'freeze-1320-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
if deferred:
    (ROOT/'audit-pending-round04.json').write_text(json.dumps({'schema_version':'1.0','producer':'audit','status':'pending_after_1320','updated_at':NOW,'results':deferred},ensure_ascii=False,indent=2),encoding='utf-8')
pending['merged_at']=NOW;pending['merged_candidate_ids']=receipt['merged_candidate_ids'];pending['unmerged_candidate_ids']=receipt['deferred_candidate_ids']
(ROOT/'audit-pending-round03.json').write_text(json.dumps(pending,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))
