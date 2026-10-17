import pathlib,json,hashlib,datetime
B=pathlib.Path(r'C:\Users\mj528\Documents\004 工作\web-demo\outputs\cecs-master-20261017')
O=B/'search/round12-public-sources'
ts='search/round12-public-sources/transport/excluded-transport-closeout.json'
ps='search/round12-public-sources/material-products/round12-house-structure-scope.json'
tr=json.loads((B/ts).read_text(encoding='utf-8'))
pr=json.loads((B/ps).read_text(encoding='utf-8'))
reasons={1:'公路CECS，非房屋结构',2:'地方公路标准，非CECS',3:'地方标准草案，非CECS；不以正文引用证明属于CECS全文',4:'桥梁检查项目文件，非CECS标准正文',5:'科技奖名单，非CECS标准正文'}
rows=[]
for i,r in enumerate(tr['records'],1):
 rows.append(dict(source_id='SEARCH-R12-TRANSPORT-EXCLUDED-%03d'%i,
  original_record_id=r['record_id'],original_file=ts,
  standard_number=r.get('standard_number'),name=r.get('name',r.get('name_as_search')),
  entity_kind='CECS路线' if i==1 else '非CECS正文排除证据',
  scope_status='excluded',scope_reason=reasons[i],download_enabled=False,
  eligible_for_current_structure_queue=False,eligible_for_coverage_denominator=False,
  download_url=r.get('download_url'),source_page=r.get('source_page')))
for r in pr['retained_structural_draft_candidates']:
 rows.append(dict(source_id=r['source_id'],original_record_id=r['candidate_id'],original_file=ps,
  standard_number=r['standard_number'],name=r['standard_name'],entity_kind='占位草案',is_draft=True,
  related_formal_hint_only=r['related_formal_standard_hint'],scope_status='pending',
  scope_reason='承重网格结构节点直接连接构件；房屋适用边界待判，未审全文',
  download_enabled=False,eligible_for_current_structure_queue=False,eligible_for_coverage_denominator=False,
  download_url=r['download_url'],source_page=r['source_page']))
for r in pr['excluded_routes']:
 rows.append(dict(source_id=r['source_id'],original_record_id=r['source_id'],original_file=ps,
  standard_number=r['standard_number'],name=r['standard_name'],entity_kind='CECS路线',
  scope_status='excluded',scope_reason=r['scope_reason'],download_enabled=False,
  eligible_for_current_structure_queue=False,eligible_for_coverage_denominator=False,
  download_url=r['download_url'],source_page=r['source_page']))
p=O/'scope-normalized-subagents-r12.json';assert not p.exists()
p.write_text(json.dumps(dict(source_id='SEARCH-R12-NORMALIZED-SUBAGENTS-20261017',
 recorded_at=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds'),
 statement_type='AI整理（已有观察的范围字段投影，未增加网络操作或质量判断）',
 current_machine_consumption=True,originals_are_evidence_not_uniform_queue=True,
 scope_rule_source_id='USER-20261017-CECS-BUILDING-STRUCTURE-ONLY',
 input_hashes=[dict(path=f,sha256=hashlib.sha256((B/f).read_bytes()).hexdigest()) for f in [ts,ps]],
 independent_qa=dict(status='范围语义检查通过；两处机器字段缺口已由本文件规范化',
  fixes=['transport逐条补download_enabled=false并明确record_id/source_id映射',
         '材料草案scope_status说明句统一映射pending，正式10300仅线索',
         'transport003排除理由明确非CECS，不沿用笼统交通适用结论']),
 rows=rows,counts=dict(excluded=6,pending=1,in_scope=0),
 notes=['本文件是子代理路线当前机器范围投影，原文件仅作观察证据。','不得把4条非CECS正文记录计入CECS版本总数。']),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(str(p))
