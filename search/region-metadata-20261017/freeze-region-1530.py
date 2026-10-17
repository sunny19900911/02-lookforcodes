import pathlib,json,hashlib,datetime,re
B=pathlib.Path(r'C:\Users\mj528\Documents\004 工作\web-demo\outputs\cecs-master-20261017');S=B/'search';O=S/'region-metadata-20261017'
NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):
 assert not p.exists(),str(p);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
prior=[]
for p in sorted(S.glob('freeze-inputs*.json')):
 d=read(p);bad=[f['path'] for f in d.get('files',[]) if not (B/f['path']).exists() or sha(B/f['path'])!=f['sha256']]
 prior.append(dict(path=str(p.relative_to(B)).replace('\\','/'),sha256=sha(p),files=len(d.get('files',[])),unchanged=not bad,failures=bad))
assert len(prior)==13 and all(x['unchanged'] for x in prior),prior
p=read(O/'university-region-evidence-proposal.json');assert p['subject_count']==2 and p['auto_apply_to_master'] is False
assert len(p['evidence'][0]['download_urls'])==4 and p['evidence'][0]['city'] is None
assert p['evidence'][0]['province']=='陕西省' and p['evidence'][0]['locality_as_published']=='杨凌'
assert p['evidence'][1]['province']=='河南省' and p['evidence'][1]['city']=='焦作市'
assert all(not h.startswith('*.') for e in p['evidence'] for h in e['match_hosts'])
assert set(h for e in p['evidence'] for h in e['match_hosts'])=={'eol.nwafu.edu.cn','tmky.hpu.edu.cn'}
for f in p['evidence_files']:assert sha(B/f['path'])==f['sha256']
unknown=read(O/'tjad/tjad-identity-pending.json');assert unknown.get('auto_registry_mapping_allowed') is False
files=[O/'university-region-evidence-proposal.json',O/'universities/official-html-observations.json',
 O/'universities/platform-identity-observations-v2.json',O/'query-ledger-region.json',
 O/'ancillary-observations-selection.json',O/'tjad/tjad-identity-pending.json']
qa=O/'university-independent-qa.json'
assert qa.exists(),'Finish independent local QA before freeze'
files.append(qa)
for f in files:
 d=f.read_text(encoding='utf-8-sig');json.loads(d);assert '\ufffd' not in d
 assert not re.search(r'(?:fileUrl|uhash|access_token|api_key|authorization)\s*[=:]\s*[^\s"，；。]{8,}',d,re.I),str(f)
write(O/'validation-region-1530.json',dict(source_id='SEARCH-REGION-VALIDATION-1530-20261017',checked_at=NOW,
 previous_frozen_inputs=prior,structured_json_valid=True,official_identity_and_address_separate=True,
 match_only_two_specific_hosts=True,exact_url_mapping_targets=5,partial_city_not_guessed=True,
 unknown_identity_not_mapped=True,pdf_get=0,new_standards=0,master_or_excel_written=False,
 wrong_charset_observation_not_selected='universities/platform-identity-observations.json',
 ancillary_beijing_evidence_not_current_university_registry=True))
files.append(O/'validation-region-1530.json')
write(O/'state-region-1530.json',dict(source_id='SEARCH-REGION-STATE-1530-20261017',recorded_at=NOW,
 active_scope_source_id='USER-20261017-CECS-ENGINEERING-ALL',region_instruction_source_id='USER-20261017-CECS-DOWNLOAD-SOURCE-REGION',
 result='仅两个高校来源主体的地区metadata提案交catalog，未直接改主索引或Excel',
 mapping_targets=dict(existing_master_links=4,pending_hpu_route=1),
 region_proposals=[dict(entity='西北农林科技大学网络教学综合平台',province='陕西省',city=None,locality_as_published='杨凌'),
 dict(entity='河南理工大学tmky子站',province='河南省',city='焦作市',basis='大学主体官网公开地址；不推上传者校区')],
 known_unknown=dict(host='knowledge.tjad.cloud',existing_links=81,provider=None,province=None,city=None,reason='实际下载主体身份链未闭合，不由字母推同济设计/上海'),
 tianjin='本批无明确天津主体证据，不作全库无天津来源结论',
 original_freezes_unchanged=len(prior),pdf_get=0,new_standards=0,new_complete_claims=0,
 catalog_schema='link.download_source_region={region_status,province,city,source_entity,region_evidence_ids,region_basis}; standards.download_source_regions只聚合链接'))
files.append(O/'state-region-1530.json')
discussion=S/'discussion-1530-source-region.md';assert not discussion.exists()
discussion.write_text(f'''# 15:30 来源地区补证（固定于 {NOW}）

依据用户 `USER-20261017-CECS-DOWNLOAD-SOURCE-REGION`，地区仅指实际资料发布/下载来源主体省市。工程CECS范围不变；不扩北京/天津地方标准，不以适用地区、标准标题、目录地区、CDN或IP推主体省市。

与catalog对齐link.download_source_region字段后，仅补两个已登记高校子域：eol.nwafu.edu.cn的4条主索引链接，tmky.hpu.edu.cn的1条R09历史候选。平台/子站名称链与官网地址分开留source_id、实际proof_url和HTML行号。NWAFU官方地址陕西杨凌，保留杨凌原文，city为空；HPU大学官网地址河南省焦作市，提案仅校方公开地址，不推上传者所在地或具体校区，既有PDF404保持。

知识站81条链接仅能确认域名，实际主体身份未闭合，省市全留空，禁止直接registry映射。cnass/zbl在分工确认前已获的证据仅列交叉核对辅助，catalog已有独立角色负责，不作为本高校registry的新增输入；cnass需区分空间结构分会与总会。未取得本批明确天津主体证据，不据此断言全库无天津。

本附录只选university-region-evidence-proposal及其官方原文观察V2；EOL原声明gbk，已严格解码，初次UTF-8乱码观察不选。独立QA及结构检查通过后固定，13份此前冻结的全部输入未变；本轮无PDF GET、无新规范、无完整数、无Git、无主索引/Excel修改。所有映射由catalog决定。
''',encoding='utf-8');files.append(discussion)
manifest=S/'freeze-region-metadata-1530.json'
write(manifest,dict(producer='search',checkpoint='15:30 来源主体地区metadata addendum',checked_at=NOW,frozen=True,
 region_instruction_source_id='USER-20261017-CECS-DOWNLOAD-SOURCE-REGION',input_file_count=len(files),previous_freeze_integrity=prior,
 current_registry_proposal='search/region-metadata-20261017/university-region-evidence-proposal.json',
 files=[dict(path=str(f.relative_to(B)).replace('\\','/'),sha256=sha(f),bytes=f.stat().st_size) for f in files],
 new_standard_candidates=0,new_complete_claims=0,pdf_get_count=0))
print(json.dumps(dict(manifest=str(manifest),sha256=sha(manifest),file_count=len(files),previous_freezes_unchanged=len(prior)),ensure_ascii=False))
