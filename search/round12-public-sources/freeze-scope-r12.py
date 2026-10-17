import json, hashlib, pathlib, datetime, re

B=pathlib.Path(r'C:\Users\mj528\Documents\004 工作\web-demo\outputs\cecs-master-20261017')
S=B/'search'; O=S/'round12-public-sources'
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
def hashfile(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):
    assert not p.exists(), str(p)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

previous=[]
for p in sorted(S.glob('freeze-inputs*.json')):
    d=read(p); failures=[]
    for f in d.get('files',[]):
        q=B/f['path']
        if not q.exists() or hashfile(q)!=f['sha256']: failures.append(f['path'])
    previous.append(dict(manifest=str(p.relative_to(B)).replace('\\','/'),sha256=hashfile(p),files=len(d.get('files',[])),unchanged=not failures,failures=failures))
assert all(p['unchanged'] for p in previous), previous
q=read(O/'scope-queue-r12.json')
assert len(q['rows'])==13
assert q['counts']=={'excluded':5,'in_scope':5,'pending':3}
assert all(r['download_enabled'] is False for r in q['rows'])
prod=read(O/'material-products/round12-house-structure-scope.json')
assert prod['formal_candidate_count']==0
assert len(prod['retained_structural_draft_candidates'])==1
draft=prod['retained_structural_draft_candidates'][0]
assert draft['is_draft'] is True and draft['download_enabled'] is False
assert '10300' not in draft['standard_number']
tran=read(O/'transport/excluded-transport-closeout.json')
assert len(tran['records'])==5
assert all(r['scope_status']=='excluded' and r['eligible_for_current_candidates'] is False for r in tran['records'])

files=[O/'scope-transition-20261017.md',O/'scope-queue-r12.json',O/'query-ledger-r12-pre-scope.json',
       O/'receipt-audit-1450-selection-r12.json',O/'scope-closeout-receipt-r12.json',
       O/'material-products/round12-house-structure-scope.json',O/'transport/excluded-transport-closeout.json',
       O/'scope-normalized-subagents-r12.json']
normalized=read(O/'scope-normalized-subagents-r12.json')
assert len(normalized['rows'])==7
assert all(r['scope_status'] in ['excluded','pending'] and r['download_enabled'] is False for r in normalized['rows'])
for p in files:
    t=p.read_text(encoding='utf-8-sig')
    assert p.suffix.lower() in ['.json','.md']
    assert not re.search(r'(?:uhash|fileUrl|access_token|api_key|authorization)\s*[=:]\s*[^\s"，；。]{8,}',t,re.I),str(p)
    if p.suffix=='.json': json.loads(t)

validation=dict(source_id='SEARCH-R12-SCOPE-VALIDATION-20261017',checked_at=now,
    previous_freeze_integrity=previous,json_valid=True,share_files_only_structured=True,
    opaque_download_parameter_values=False,all_current_route_downloads_disabled=True,
    root_scope_projection_rows=13,root_scope_projection_counts=q['counts'],
    structural_draft_separate_from_formal=True,transport_isolated=True,
    subagent_current_machine_projection='search/round12-public-sources/scope-normalized-subagents-r12.json',
    global_scope_denominator=None,global_scope_complete_formal_count=None,
    qualification='只验证本轮分享投影；不代替全量catalog范围筛选或audit全文判断。')
write(O/'validation-scope-r12.json',validation)
files.append(O/'validation-scope-r12.json')
state=dict(source_id='SEARCH-R12-STATE-20261017',recorded_at=now,
    scope_rule_source_id='USER-20261017-CECS-BUILDING-STRUCTURE-ONLY',
    status='非房屋结构路线已停止；本轮仅范围切换、隔离和队列投影',
    stop=dict(transport=True,green_product_broad_search=True,post_stop_search=0,post_stop_get=0,post_stop_download=0),
    root_scope_projection=dict(rows=13,counts=q['counts'],download_enabled=False),
    subagent_products=dict(formal_pdf_candidates=0,pending_structural_draft=1,download_enabled=False),
    subagent_transport=dict(isolated_metadata=5,current_candidates=0),
    new_formal_complete_claims=0,new_global_scope_counts=None,
    global_count_owner='catalog/audit在新范围交集后重算；本角色不改主索引、Excel或质量评级',
    selected_audit='pdf-audit/audit-pending-round09-freeze-1450-v2.json',
    selected_alternate_projection='pdf-audit/candidates-r11-alt31-share.json',
    normalized_subagent_scope='search/round12-public-sources/scope-normalized-subagents-r12.json',
    unchanged_previous_freezes=len(previous),next=['等待主控统一范围筛选与catalog投影；旧广范围队列不直接恢复。','结构相关新路线须在范围明确后再推进；含糊条目先核适用范围。'])
write(O/'state-scope-r12.json',state);files.append(O/'state-scope-r12.json')

discussion=S/'discussion-1500-scope-transition.md'
assert not discussion.exists()
discussion.write_text(f'''# 15:00 范围切换回报（固定于 {now}）

已按用户 `USER-20261017-CECS-BUILDING-STRUCTURE-ONLY` 停止非房屋结构新检索、GET和下载。交通专线无在途工具，产品/绿色泛检索已停；停止后新网络操作均为0。

最近13条根角色路线投影：5条结构相关来源/问题线索，5条排除，3条待判，全部禁用当前下载。结构相关5条中含1条DOC和2条无可用PDF链接的元数据，不能把“纳入范围”当作5份已下载PDF。另有1份螺栓球节点产品草案待判，封面为五位占位2022征求意见稿，不改挂10300-2023正式号。交通子代理5条元数据隔离，其中含非CECS引用/项目/名单材料，均不入当前候选。

当前审查分享仍选1450-v2，SHA `339a53ad776599ca4181a75633dd0479b1f040d293e9bf35d02dd762937196ef`；备用31分享投影SHA `2aa5cd96cfcc3f9d3848c7046575bb72e53b7426fb602f8b58b191558b94a61d`，备用观察页数为空，不继承主web64页。旧广范围7条审查不直接进入新范围统计。

本轮只新增范围规则、投影和只读回执；11份旧冻结的全部输入哈希未变。无PDF/PNG/原HTML/不透明下载参数值进入分享。不改catalog、Excel、audit评级、master-authority或Git。

新范围总数、完整正式文本数和覆盖率尚未产生；由catalog/audit完成全量范围交集后重算，旧全CECS分母停用。

具体证据见本次 `freeze-inputs-1500-scope-transition.json`。本批不是全国CECS全集，也不是房屋结构规范全集。
''',encoding='utf-8')
files.append(discussion)
manifest=S/'freeze-inputs-1500-scope-transition.json'
write(manifest,dict(producer='search',checkpoint='15:00 范围切换',checked_at=now,frozen=True,
    scope_rule_source_id='USER-20261017-CECS-BUILDING-STRUCTURE-ONLY',input_file_count=len(files),
    previous_freeze_integrity=previous,note='只选结构化范围投影；旧记录历史保留，不直接进入当前专业范围分母。',
    files=[dict(path=str(p.relative_to(B)).replace('\\','/'),sha256=hashfile(p),bytes=p.stat().st_size) for p in files]))
print(json.dumps(dict(manifest=str(manifest),sha256=hashfile(manifest),files=len(files),previous_freezes_unchanged=len(previous)),ensure_ascii=False))
