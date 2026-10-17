import json,pathlib,hashlib,datetime,re
B=pathlib.Path(r'C:\Users\mj528\Documents\004 工作\web-demo\outputs\cecs-master-20261017');S=B/'search';O=S/'round13-engineering-restored'
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):
 assert not p.exists(),str(p);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
prior=[]
for p in sorted(S.glob('freeze-inputs*.json')):
 d=rd(p);bad=[f['path'] for f in d.get('files',[]) if not (B/f['path']).exists() or sha(B/f['path'])!=f['sha256']]
 prior.append(dict(path=str(p.relative_to(B)).replace('\\','/'),sha256=sha(p),files=len(d.get('files',[])),unchanged=not bad,failures=bad))
assert len(prior)==12 and all(p['unchanged'] for p in prior),prior
selection=rd(O/'receipt-current-selection-r09-r11-1510.json')
for m in selection['selected_manifests']:
 assert sha(B/m['path'])==m['sha256']
 for f in m['files']:assert sha(B/f['path'])==f['sha256']
for f in selection['selected_audit_and_backup']:assert sha(B/f['path'])==f['sha256']
net=rd(O/'directory-net-crosscheck-1510.json');assert net['union_absent_from_master']==268
drafts=rd(O/'new-drafts-r12-r13-share.json');assert drafts['candidate_count']==2 and all(c['is_draft'] for c in drafts['candidates'])
assert len({c['download_url'] for c in drafts['candidates']})==2
assert not any(re.fullmatch(r'T/CECS\s+\d+[-:]\d{4}',c['standard_number']) for c in drafts['candidates'])
restored=rd(O/'queue-engineering-restored-r12.json');assert restored['route_counts']=={'in_scope':16,'excluded':4}
assert all(r['entity_kind']=='非CECS正文排除证据' for r in restored['rows'] if r['scope_status']=='excluded')

write(O/'independent-qa-receipt-1510.json',dict(source_id='SEARCH-INDEPENDENT-QA-R13-20261017',recorded_at=now,
 statement_type='AI独立只读复核回执',reviewer='/root/baseline_external_routes',
 results=dict(hash_checks_passed=40,manifests=3,source_files=32,audit_or_backup_files=5,
  master_snapshot_standards=1008,master_snapshot_links=146,directory_union_keys=381,already_in_master=113,absent_master=268,
  sequential_net=[137,127,4],g_professional_keys_included=8,
  short_161_not_complete=True,doc_21_not_pdf=True,alternate_41_not_new_version=True,
  qingdao_33_title_effective_date_conflicts_preserved=True),
 scope_current='USER-20261017-CECS-ENGINEERING-ALL',
 boundaries=['268是目录key差集，不是主索引已验收净新增或完整PDF数','未联网、未改文件、未操作Git；复核不增加全文完整性结论']))

write(O/'state-r13.json',dict(source_id='SEARCH-R13-STATE-20261017',recorded_at=now,
 active_rule='USER-20261017-CECS-ENGINEERING-ALL',superseded_rule='USER-20261017-CECS-BUILDING-STRUCTURE-ONLY',
 scope='工程相关CECS均可收集下载，房屋结构优先；保留专业和适用范围分类',
 scope_restoration=dict(in_scope_route_records=16,non_cecs_excluded_records=4,master_or_excel_changed=False),
 current_main_batch=dict(search_manifests=['search/freeze-inputs-1420.json','search/freeze-inputs-1430.json','search/freeze-inputs-1440.json'],
  source_selection_receipt='search/round13-engineering-restored/receipt-current-selection-r09-r11-1510.json',
  directory_difference=268,difference_is_final_catalog_net=False),
 new_pending=dict(candidate_file='search/round13-engineering-restored/new-drafts-r12-r13-share.json',drafts=2,formal_usable_pdf_candidates=0,complete_pdf_claims=0,
  separate_from_R09_R11=True),
 primary_source_experiments=dict(target_numbers=['28:2012','1009-2022','325:2012'],primary_pages_get_200=3,document_href_found=0,new_pdf=0,
  failed_routes_not_retried=['CECS28济南403','CECS325个人站404','CECS291和80的web403']),
 traffic=dict(query_count=20,pdf_get=0,new_pdf_candidates=0),
 ownership='search未操作主索引、Excel、audit评级、master-authority、Git或原件',
 next='主控按本批冻结接R09/R10/R11；R12/R13两份草案独立待审，不能计完整。'))

files=sorted([p for p in O.rglob('*') if p.is_file() and p.suffix.lower() in ['.json','.md']],key=str)
files.append(S/'scope-instruction-timeline-20261017.json')
for p in files:
 t=p.read_text(encoding='utf-8-sig')
 if p.suffix=='.json':json.loads(t)
 assert not re.search(r'(?:fileUrl|uhash|access_token|api_key|authorization)\s*[=:]\s*[^\s"，；。]{8,}',t,re.I),str(p)
 assert 'master-authority' not in str(p.relative_to(O)) if p.is_relative_to(O) else True
validation=O/'validation-r13.json'
write(validation,dict(source_id='SEARCH-R13-VALIDATION-20261017',checked_at=now,
 old_freezes=prior,structured_json_valid=True,secret_or_opaque_parameter_values_shared=False,
 new_candidate_ids_and_urls_unique=True,drafts_not_formal=True,new_complete_claims=0,
 independent_old_batch_hash_checks=40,new_global_coverage_claim=False,
 current_scope_policy='search/round13-engineering-restored/scope-engineering-all-20261017.json',
 mutable_convenience_pointer_not_frozen='search/active-cecs-scope.json'))
files.append(validation)
discussion=S/'discussion-1510-engineering-restored.md';assert not discussion.exists()
discussion.write_text(f'''# 15:10 交流与工程范围恢复（固定于 {now}）

当前生效 `USER-20261017-CECS-ENGINEERING-ALL`：工程相关CECS均可先收集和下载，房屋结构优先。旧结构限定规则已被覆盖，scope-transition冻结仅保留历史。最近20条路线投影恢复16条工程CECS/草案，4条因非CECS正文继续排除；主索引、Excel和质量从未按旧范围修改，无数据回滚。

本次主控旧批次仍只选1420/1430/1440，选择回执逐项列出全SHA。R09用root-share，R11用1450-v2及alt31-share，不把主web64页复制给备用。独立QA共40项哈希一致；161三页短文件、21 DOC及41同版本备链不混入完整PDF。青岛33行标题2024年9月、实施2025-09-01、网页2025-08-21的冲突保留，标准发布日期不猜。

目录重算在c78cabf0快照1008标准/146链接上，381个四位年键中113已有、268尚未入库，分批137/127/4，含8个G专业键。此为目录集合差集，不是catalog最终净新增或完整PDF数。

结构优先的三个编号28、1009、325完成一组独立主编/参编来源试验：三页普通GET200，无文件附件属性，新增PDF0。28济南403、325个人站404、291/80 web403均留证并停止，不绕过。1009协会页仅元数据，没有实测PDF。

新R12/R13与旧批次隔离：两份产品征求意见稿候选（2022五位占位节点产品、2025四位占位管路连接件）已做普通GET前16字节签名检查，全文未审，正式可用PDF新增0、完整新增0；不能改挂正式号。仅选new-drafts-r12-r13-share.json交后续独立审查。交通本轮20查询无新PDF。

12份此前冻结全部输入哈希未变。分享仅结构化JSON/MD，不含PDF/PNG/原HTML/不透明参数值。本角色未操作Git、主索引、Excel或audit评级。本批不声称工程CECS全集。
''',encoding='utf-8');files.append(discussion)
manifest=S/'freeze-inputs-1510-engineering-restored.json'
write(manifest,dict(producer='search',checkpoint='15:10 工程范围恢复/旧批次交叉核对/新草案隔离',checked_at=now,frozen=True,
 active_scope_source_id='USER-20261017-CECS-ENGINEERING-ALL',input_file_count=len(files),previous_freeze_integrity=prior,
 files=[dict(path=str(p.relative_to(B)).replace('\\','/'),sha256=sha(p),bytes=p.stat().st_size) for p in files],
 pending_audit_candidate_selection='search/round13-engineering-restored/new-drafts-r12-r13-share.json',
 main_current_batch_unchanged=['search/freeze-inputs-1420.json','search/freeze-inputs-1430.json','search/freeze-inputs-1440.json']))
print(json.dumps(dict(manifest=str(manifest),sha256=sha(manifest),file_count=len(files),unchanged_previous_freezes=len(prior)),ensure_ascii=False))
