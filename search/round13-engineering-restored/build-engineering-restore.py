import pathlib,json,datetime,hashlib,collections
B=pathlib.Path(r'C:\Users\mj528\Documents\004 工作\web-demo\outputs\cecs-master-20261017');S=B/'search';O=S/'round13-engineering-restored';O.mkdir(parents=True,exist_ok=True)
NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
RULE='USER-20261017-CECS-ENGINEERING-ALL';OLD='USER-20261017-CECS-BUILDING-STRUCTURE-ONLY'
def read(p):return json.loads((B/p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256((B/p).read_bytes()).hexdigest()
def write(p,d):
 q=B/p;assert not q.exists(),str(q);q.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

policy='search/round13-engineering-restored/scope-engineering-all-20261017.json'
write(policy,dict(source_id=RULE,recorded_at=NOW,statement_type='原文事实（主控转达用户最新直接澄清）',
 active=True,supersedes=OLD,scope='工程相关CECS均可先收集和下载，房屋结构设计相关优先',
 include=['房屋结构与岩土地基','给排水','暖通电气与消防','公路桥梁铁路隧道与市政','工程绿色建材、节能、碳评价和工程综合'],
 exclude=['其他标准体系的标准正文不作为CECS条目','只有CECS引用的论文、项目文件、目录、奖项名单不作为CECS标准全文','无法辨明工程关联的资料先待判'],
 classification=['主专业','交叉标签','适用对象与范围','版本阶段','访问状态','完整性与质量'],
 restored_prior_batches=['R09','R10','R11','R12工程相关路线'],
 cancel_only_due_to_nonbuilding_structure=True,quality_and_access_findings_unchanged=True,
 safeguards=['不把下载或目录发现当作现行或完整','草案、历史版、正式编号文本分别保存','不绕过账号、付费、验证码或挑战；失败路线不因范围恢复重复请求'],
 historical_scope_manifest=dict(path='search/freeze-inputs-1500-scope-transition.json',sha256=sha('search/freeze-inputs-1500-scope-transition.json'),current_scope_policy=False),
 ownership=dict(catalog='唯一Excel与主索引写入',audit='独立全文审查',search='检索及队列',main='唯一Git写入')))
write('search/scope-instruction-timeline-20261017.json',dict(source_id='SEARCH-SCOPE-TIMELINE-20261017',recorded_at=NOW,
 events=[dict(source_id=OLD,acknowledged_at='2026-10-17T15:00:39+08:00',active=False,superseded_by=RULE,
  effect='仅search新增停止与范围投影，未改主索引/Excel/原件/质量；原冻结保留历史'),
 dict(source_id=RULE,acknowledged_at='2026-10-17T15:07:12+08:00',active=True,
  effect='工程CECS队列立即恢复；只因非房屋结构的停用/排除/待判撤销')],
 no_master_or_excel_scope_changes_to_rollback=True))
write('search/active-cecs-scope.json',dict(source_id='SEARCH-ACTIVE-SCOPE-20261017',updated_at=NOW,
 active_scope_source_id=RULE,path=policy,sha256=sha(policy),superseded_scope_source_id=OLD,
 superseded_manifest='search/freeze-inputs-1500-scope-transition.json',
 note='当前范围只选ENGINEERING-ALL；原结构-only冻结保留历史，不作当前队列筛除依据。'))

old=read('search/round12-public-sources/scope-queue-r12.json')
categories={'R11-31-2017-APEXTRAY':'电气/电缆桥架','R11-31-2017-ALTERNATE':'电气/电缆桥架',
 'R11-1555-2024-FAIUSR':'工程绿色与综合/碳评价','R11-200-2006-DLSSYHT':'房屋结构/钢结构抗火',
 'R11-197-2006-FAIUSR':'岩土地基/地基处理','R11-165-2004-YSJIANZHAN':'市政通信/管道',
 'R11-INST-PDF-001':'结构检测/混凝土强度','R11-INST-DOC-001':'结构检测/混凝土缺陷',
 'R11-ALT-41-2004':'给排水/建筑给水','R12-28-2012-INDEX':'房屋结构/钢管混凝土',
 'R12-1009-2022-PAGE':'结构检测/钢结构','R12-291-2011-INDEX':'钢结构/波纹腹板',
 'R12-80-2006-INDEX':'构筑物结构/塔桅'}
rows=[]
for r in old['rows']:
 x={k:r.get(k) for k in ['candidate_id','standard_number','name','original_source_id','download_url','source_page','route_kind','quality_observation']}
 x.update(source_id='RESTORED-'+r['source_id'],previous_scope_status=r['scope_status'],scope_status='in_scope',
  scope_rule_source_id=RULE,scope_allows_download=True,professional_category=categories[r['candidate_id']],
  building_structure_priority=r['candidate_id'] in ['R11-200-2006-DLSSYHT','R11-197-2006-FAIUSR','R11-INST-PDF-001','R11-INST-DOC-001','R12-28-2012-INDEX','R12-1009-2022-PAGE'],
  quality_unchanged=True,complete_pdf_claim_added=False,
  next_action='恢复工程范围来源/问题队列；依已有访问与质量结论逐批推进，不因恢复范围重复失败GET。')
 if r['candidate_id'] in ['R12-291-2011-INDEX','R12-80-2006-INDEX']:
  x.update(latest_access_observation='恢复后web open实际403；停止该URL',new_get_allowed=False)
 if r['candidate_id']=='R12-28-2012-INDEX':
  x.update(latest_access_observation='恢复后定位真实公开索引无不透明参数的downfile.jsp路线，普通GET403；原metadata保留',new_get_allowed=False,
   additional_route='https://jncc.jinan.gov.cn/module/download/downfile.jsp?classid=0&filename=6f531b872d124585b888c4bcfde0616b.pdf')
 if r['candidate_id']=='R12-1009-2022-PAGE':
  x.update(latest_access_observation='匿名GET200，未见相关PDF/DOC/download属性；仍为页面元数据，不计PDF',new_get_allowed=False)
 rows.append(x)
sub=read('search/round12-public-sources/scope-normalized-subagents-r12.json')
for r in sub['rows']:
 x=dict(r);x['source_id']='RESTORED-'+r['source_id'];x['previous_scope_status']=r['scope_status'];x['scope_rule_source_id']=RULE
 if r['entity_kind']=='非CECS正文排除证据':
  x.update(scope_status='excluded',scope_allows_download=False,download_enabled=False,
   scope_reason='身份不是CECS标准正文；最新范围仍不扩其他体系或引用性材料。')
 else:
  x.update(scope_status='in_scope',scope_allows_download=True,
   scope_reason='工程相关CECS/其草案，最新范围允许收集；非房屋结构不再是排除理由。',
   professional_category='交通/公路混凝土' if 'TRANSPORT' in r['source_id'] else ('结构材料产品/网格节点' if r['entity_kind']=='占位草案' else '工程绿色材料/空气净化'),
   quality_unchanged=True,complete_pdf_claim_added=False,
   next_action='原路线失败/已审则不重复GET；草案保持占位号与征求意见阶段，后续独立审查。')
  x.pop('download_enabled',None)
  x.pop('eligible_for_coverage_denominator',None)
  x['eligible_for_current_structure_queue']=False
 rows.append(x)
write('search/round13-engineering-restored/queue-engineering-restored-r12.json',dict(source_id='SEARCH-ENGINEERING-RESTORED-QUEUE-20261017',recorded_at=NOW,
 scope_rule_source_id=RULE,scope_statement_type='AI整理（工程关联/专业分类；用户范围以规则source_id为准）',
 projection_scope='最近根角色及子代理20条路线记录，不是标准版本数或PDF数',rows=rows,
 route_counts=dict(collections.Counter(r['scope_status'] for r in rows)),
 old_scope_counts_not_current=True,new_complete_claims=0,
 caveat='scope_allows_download只描述专业范围授权；不抹除403/404/证书/挑战/缺页等访问和质量结论。'))
print(json.dumps(dict(active_rule=RULE,restored_route_records=sum(r['scope_status']=='in_scope' for r in rows),non_cecs_excluded_records=sum(r['scope_status']=='excluded' for r in rows),master_or_excel_modified=False),ensure_ascii=False))
