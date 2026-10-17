from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,re,copy

base=Path(r'C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017')
search=base/'search';folder=search/'round09-new-sources'
now=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
manifests=['freeze-inputs-1320.json','freeze-inputs-round04.json','freeze-inputs-1330.json','freeze-inputs-1340.json','freeze-inputs-1340-water-mep-addendum.json','freeze-inputs-1340-water-mep-addendum-v2.json','freeze-inputs-g2-round02-share-1350.json','freeze-inputs-1400.json']
checks=[]
for name in manifests:
    m=read(search/name);bad=[x['path'] for x in m['files'] if sha(base/x['path']).lower()!=x['sha256'].lower()]
    checks.append({'manifest':'search/'+name,'files':len(m['files']),'unchanged':not bad,'failures':bad})
assert all(x['unchanged'] for x in checks),checks
original=folder/'candidates-r09-root.json'; root=read(original)
share=copy.deepcopy(root)
for r in share['metadata_only']:
    r['standard_number']='T/CECS XXX-2025' if r['name']=='建筑光伏系统检测标准' else 'T/CECS XXXX-2025'
share['share_projection']={'recorded_at':now,'original_path':'search/round09-new-sources/candidates-r09-root.json','original_sha256':sha(original),'note':'仅将两条metadata占位编号按各自索引原文分别显示XXX/XXXX，未改5候选的ID/URL/身份/计数。原文件本地不改；当前分享选本投影。'}
root_share=folder/'candidates-r09-root-share.json';assert not root_share.exists();root_share.write_text(json.dumps(share,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
wp=folder/'water-mep/round09-water-mep-candidates.json'
assert sha(wp)=='172817225816b9cfcfbb52a591ef87ea15e4a551bd360a2e22a42dbe50beaadd'
water=read(wp);assert len(water['candidates'])==1
all_candidates=share['candidates']+water['candidates'];assert len(all_candidates)==6
assert len({r['candidate_id'] for r in all_candidates})==6
dp=folder/'recent-directory/recent-directory-r09.json'
assert sha(dp)=='91436f5d85fa8df1861994d71566f38a72e3a126a3b6c84ac3f02a5ef470436d'
directory=read(dp);rows=directory['records'];assert len(rows)==138
assert all(r['source_location'].get('html_source_line_start') and r['source_location'].get('html_source_line_end') and r['raw_cells'] for r in rows)
assert len({r['record_id'] for r in rows})==138
resolved={r['number_year_key'] for r in rows if r.get('number_year_key')};assert len(resolved)==137
master_path=base/'catalog/cecs-master.json';master_raw=master_path.read_bytes();master=json.loads(master_raw.decode('utf-8-sig'))
pattern=re.compile(r'CECS\s*(\d+)\s*[-:：－—]\s*(\d{4})',re.I)
master_keys={str(int(m.group(1)))+'/'+m.group(2) for r in master['standards'] if (m:=pattern.search(r.get('standard_number','')))}
root_validate={'source_id':'SEARCH-R09-INDEPENDENT-VALIDATION-20261017','recorded_at':now,
 'directory_rows':138,'directory_resolved_unique_keys':137,'directory_unresolved':1,'all_actual_html_locations':True,
 'master_identity_count_at_read':len(master['standards']),'master_sha256_at_read':hashlib.sha256(master_raw).hexdigest(),
 'normalized_numeric_master_keys':len(master_keys),'matching_number_years':sorted(resolved&master_keys),'not_in_master_at_read':len(resolved-master_keys),
 'dedupe_boundary':'独立按master.standard_number统一编号与4位年检查；不是已合库数，非数字G/图集号不猜。',
 'pdf_candidate_count':6,'root_candidates_unchanged':[r['candidate_id'] for r in share['candidates']],
 'metadata_projection_note':'2条平台占位号按各自索引分别保留XXX/XXXX，不用组合占位显示；5候选本体不变。'}
vp=folder/'validation-r09-root.json';assert not vp.exists();vp.write_text(json.dumps(root_validate,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
pending=base/'pdf-audit/audit-pending-round07.json'
pending_raw=pending.read_bytes();a=json.loads(pending_raw.decode('utf-8-sig'));r=next(r for r in a['results'] if r['candidate_id']=='R09-HPU-69-2011')
assert r.get('http_status')==404
obs69={'source_id':'SEARCH-R09-69-GET-NEGATIVE-RECEIPT-20261017','recorded_at':now,
 'statement_type':'原文事实（审查角色实际GET负结果回执；检索侧不重复GET）',
 'source_file':'pdf-audit/audit-pending-round07.json','source_file_sha256_at_read':hashlib.sha256(pending_raw).hexdigest(),'source_mutability':'仍pending；哈希只锁定读取时刻，不称已冻结。',
 'candidate_id':r['candidate_id'],'requested_url':r.get('requested_url'),'checked_at':r.get('checked_at'),'http_status':404,
 'observation':'web能解析23页不替代本次独立实际GET；本次404未得本地PDF，不说永久失效。',
 'historical_event_boundary':'第85号公告尚未核图，不据本候选确认69:94废止事件。',
 'complete_pdf':False}
op=folder/'audit-observation-69-r09.json';assert not op.exists();op.write_text(json.dumps(obs69,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
canon_path=base/'pdf-audit/audit-results.json';canon_raw=canon_path.read_bytes();canon=json.loads(canon_raw.decode('utf-8-sig'))
state={'source_id':'SEARCH-R09-CHECKPOINT-1420-20261017','recorded_at':now,
 'pdf_candidates':6,'formal_historical_candidates':2,'placeholder_draft_candidates':4,
 'preview_routes_separate':len(water['preview_routes']),'blocked_platform_metadata_routes':2,
 'government_source_records':138,'government_complete_unique_number_years':137,'unresolved_year_code':1,
 'government_records_with_actual_html_locations':138,'page_title_effective_date_conflict_rows':33,
 'not_in_master_at_read':len(resolved-master_keys),'not_in_master_boundary':'只是当前读取快照比对；正式合库净增由catalog决定。',
 'source_reported_new_water_403_routes':5,'water_query_count':water['query_count'],
 'canonical_audit_observed_at_read':{'result_count':len(canon['results']),'sha256':hashlib.sha256(canon_raw).hexdigest(),'updated_at':canon.get('updated_at')},
 'last_independent_review_batch':'1410 pending8，SHA455b212b19fd80b644aa82c64e5592d07e35fc27fd462c99571dbd6fdebb4b57：正式完整B4、完整送审草案B1另列；合并须主控批准。',
 'new_r09_complete_pdf_count_by_search':0,
 'old_freeze_integrity':checks,'boundary':'只新来源元数据。候选/预览/正式完整/草案完整分开，历史清单不确认2026现行。无Git、账号登录、PDF上传或原始HTML共享。'}
sp=folder/'state-r09.json';assert not sp.exists();sp.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
discussion='''# 14:20 检索检查点

source_id: SEARCH-DISCUSSION-1420-20261017；记录时间：%s（北京时间）。

原文事实（新公开来源）：本轮6条PDF候选，2个正式历史候选（69:2011、243:2008）与4份占位编号草稿（索结构工程施工质量验收征求稿、装配式建筑低碳评价、检查井防坠落格板、木结构防火涂料及阻燃处理剂）。243为深圳光明政府公开附件，普通GET200/PDF，具体父页未知；69大学web解析23页，但审查角色精确URL实际GET404，未得本地PDF。69的旧版废止事件仍待公告图像验证，不据缓存确认。另1份3页短预览及2条平台403草稿路线分开，不计本轮6PDF候选或正式完整。5条新水/机电URL实际403均停止，不重试绕过；水协旧站证书过期也停止。

原文事实（新目录）：3个青岛政府实际网页，138条来源，137个唯一完整编号年份，1条50004J-24年份不猜。全部附真实HTML原<tr>行起止、表行序号与原cells，43行另有web行号。独立读取当前master标准编号统一为数字编号/4位年，137项未见于该快照；这里只登记候选，catalog合入数仍为0。网页发布日期、标准发布日期、实施日期分列；标准发布日期没有原文即null。2025-08-21网页题称2024年9月，但33行均写2025-09-01实施，保留冲突不改题，不据历史实施清单确认2026现行。

原文事实（已收审查反馈）：1410独立冻结8项，正式完整B新增212:2006、235:2008、122:2001、17:2000；63页工业改造送审完整B另列。122/17只说本件数字排版闭合，不冒称出版社原页式；333/287仍C，287出版身份待核不直接定草案。48条/正式14链12版12哈希仍须以主控批准后的canonical冻结为准，本检索文件不先合并。

我的观点（方法）：以主编/施行等封面词检索比泛CECS+论文关键词更易命中文本；但公开索引、web缓存解析、实际GET各自独立，404也要保留当次工具差异。政府新实施清单能补2024编号，但日期冲突和非数字图集号必须原样留下。已有候选不反复同403，转公开独立源；不把目录扩展或预览数量当全文成果。

分享仅取本批manifest列文件，根候选使用share投影（两条metadata占位号按各自原文分XXX/XXXX显示，5候选ID/URL不变）。原始固定文件、旧8个manifest输入均保持哈希；无PDF、PNG、HTML原始响应或瞬时下载参数值；主控单独负责GitHub。
'''%now
discussion_path=search/'discussion-1420.md';assert not discussion_path.exists();discussion_path.write_text(discussion,encoding='utf-8')
rels=[
 'round09-new-sources/candidates-r09-root-share.json','round09-new-sources/query-ledger-r09-root.json',
 'round09-new-sources/public-route-observations-r09.json','round09-new-sources/quality-feedback-r09-audit-1410.json',
 'round09-new-sources/audit-observation-69-r09.json','round09-new-sources/validation-r09-root.json',
 'round09-new-sources/water-mep/round09-water-mep-candidates.json',
 'round09-new-sources/recent-directory/recent-directory-r09.json','round09-new-sources/recent-directory/validation-r09.json',
 'round09-new-sources/state-r09.json','discussion-1420.md']
for rel in rels:
    p=search/rel;assert p.is_file(),rel
    if p.suffix=='.json':read(p)
    assert not re.search(r'(?i)[?&](?:uhash|access_token|token|signature|secret|password)=',p.read_text(encoding='utf-8-sig')),rel
mf=search/'freeze-inputs-1420.json';assert not mf.exists()
m={'producer':'search','checkpoint':'14:20','checked_at':now,'frozen':True,'input_file_count':len(rels),
   'previous_freeze_integrity':checks,'note':'仅结构化分享。根候选选share，不复制原文件；6候选不增加完整数，预览/403元数据/138目录行分开。原PDF/PNG/HTML/瞬时下载参数值不入manifest。',
   'files':[{'path':'search/'+rel,'sha256':sha(search/rel),'bytes':(search/rel).stat().st_size} for rel in rels]}
mf.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'manifest':str(mf),'sha256':sha(mf),'files':len(rels),'candidates':6,'government_source_records':138,'resolved_number_years':137,'canonical_audit_count_observed':len(canon['results'])},ensure_ascii=False))
