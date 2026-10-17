from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,re

base=Path(r'C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017');search=base/'search';folder=search/'round10-public-sources'
now=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
names=['freeze-inputs-1320.json','freeze-inputs-round04.json','freeze-inputs-1330.json','freeze-inputs-1340.json','freeze-inputs-1340-water-mep-addendum.json','freeze-inputs-1340-water-mep-addendum-v2.json','freeze-inputs-g2-round02-share-1350.json','freeze-inputs-1400.json','freeze-inputs-1420.json']
checks=[]
for n in names:
 m=read(search/n);bad=[x['path'] for x in m['files'] if sha(base/x['path']).lower()!=x['sha256'].lower()];checks.append({'manifest':'search/'+n,'files':len(m['files']),'unchanged':not bad,'failures':bad})
assert all(x['unchanged'] for x in checks)
cp=folder/'candidates-r10-detection.json';c=read(cp);assert len(c['candidates'])==2
fp=folder/'foundation/round10-foundation-search.json';assert sha(fp)=='3a713fae13242298124a9dd7c3ec79e4641448a69c02cb5af09de2c843fb43fd';foundation=read(fp)
dp=folder/'monthly-directory/monthly-directory-r10.json';assert sha(dp)=='d457d36600059e68a7c30377bfa2b73091ce1f42b8bd6de41f9417a8be32911c';d=read(dp);rows=d['records'];assert len(rows)==142
assert all(r['source_location'] and r['raw_cells'] for r in rows)
assert len({r['record_id'] for r in rows})==142
keys={r['number_year_key'] for r in rows if r.get('number_year_key')};assert len(keys)==128
master_path=base/'catalog/cecs-master.json';master_bytes=master_path.read_bytes();master=json.loads(master_bytes.decode('utf-8-sig'))
rx=re.compile(r'CECS\s*(\d+)\s*[-:：－—]\s*(\d{4})',re.I)
master_keys={str(int(m.group(1)))+'/'+m.group(2) for r in master['standards'] if (m:=rx.search(r.get('standard_number','')))}
r09=read(search/'round09-new-sources/recent-directory/recent-directory-r09.json');r09keys={r['number_year_key'] for r in r09['records'] if r.get('number_year_key')}
v={'source_id':'SEARCH-R10-INDEPENDENT-VALIDATION-20261017','recorded_at':now,'source_rows':142,'unique_complete_number_years':128,
 'master_identity_count_at_read':len(master['standards']),'master_sha256_at_read':hashlib.sha256(master_bytes).hexdigest(),
 'overlap_master_keys':sorted(keys&master_keys),'overlap_r09_keys':sorted(keys&r09keys),'absent_both_snapshots':len(keys-master_keys-r09keys),
 'merge_count':0,'boundary':'只去重比较，不写master；机构补充不称政府/协会，日期各自分列。'}
vp=folder/'validation-r10-root.json';assert not vp.exists();vp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audit=base/'pdf-audit/audit-results-freeze-1410.json';assert sha(audit)=='a81a40dfff05c0bd437b99875baba5efc7f540c05ae9c59437aceb66d5aa65e2';a=read(audit);assert len(a['results'])==48
audit_receipt=read(base/'pdf-audit/freeze-1410-receipt.json')
receipt={'source_id':'SEARCH-R10-AUDIT-CANONICAL-1410-RECEIPT','recorded_at':now,'statement_type':'原文事实（审查冻结及其回执读取）',
 'source_path':'pdf-audit/audit-results-freeze-1410.json','sha256':sha(audit),'result_count':48,
 'source_receipt_path':'pdf-audit/freeze-1410-receipt.json','source_receipt_sha256':sha(base/'pdf-audit/freeze-1410-receipt.json'),
 'audit_reported_counts':{'formal_complete_links':14,'formal_complete_versions':12,'formal_complete_hashes':12,'complete_drafts_separate':2},
 'boundary':'此为14:24:41审查canonical；不是本R10新候选已审，也不代表该canonical已发布GitHub。R09/R10继续独立pending。'}
rp=folder/'audit-canonical-1410-receipt-r10.json';assert not rp.exists();rp.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
state={'source_id':'SEARCH-R10-CHECKPOINT-1430-20261017','recorded_at':now,'new_pdf_candidate_routes':2,'new_foundation_candidates':0,
 'detection_get_200_pdf_prefix':1,'detection_tls_hostname_failure':1,'foundation_query_count':40,
 'source_rows':142,'government_rows':13,'institute_supplement_rows':129,'resolved_unique_number_years':128,'unresolved_code_rows':1,
 'cross_source_repeated_records':13,'number_years_absent_master_and_r09':len(keys-master_keys-r09keys),'merge_count':0,
 'root_candidate_header_time_resolution':'候选文件14:28:00为分钟级记录时间；实际访问14:26:40见instrument-observations。',
 'audit_canonical_count':48,'audit_formal_complete_links':14,'audit_formal_versions':12,'audit_complete_drafts_separate':2,
 'search_added_complete_count':0,'old_freeze_integrity':checks,
 'boundary':'历史状态不确认2026现行，公开可取不证明转载授权；无Git、账户访问、原PDF/PNG/HTML共享或瞬时参数值。'}
sp=folder/'state-r10.json';assert not sp.exists();sp.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
discussion='''# 14:30 检索检查点

source_id: SEARCH-DISCUSSION-1430-20261017；记录时间：%s（北京时间）。

原文事实（检测新路线）：69:2011新独立北京海创高科公开托管PDF普通GET200/application/pdf且签名正确，本轮只读前64bytes，完整性及85公告交audit；HPU旧404和69:94历史本保留。企业html/61可读同名下载项，但未定位到该PDF的明确href，因此该页只作同名相关页，不冒充具体父页。另02:2005第三方公开索引附件普通GET证书域名不匹配停止，不认定更完整替代。ysjianzhan69新索引只作未审备链，不作为已验证备用。仪器信息网21-2024只元数据/预览、无直接PDF；需要APP登录/活力值的03-2007不继续操作。

原文事实（基础检索）：40条实际查询后0新正式/草案候选。776/147两个新PDF索引首次普通GET均403即停；22-2024为既有重复且变HTML首页，排除。公告索引不当规范全文；没有因零成果去凑候选，也不重复旧失败URL。

原文事实（目录补充）：6个实际公开来源，142来源记录＝政府13＋机构平台补充129，128个唯一完整编号年份及1条60003JTG-24年份缺口，13条跨源重复保留关联。机构平台页脚称中国建筑标准设计研究院版权，分类为机构公开信息平台，不称政府或协会。政府淄博7月清单由web L16–28实际可读，直接GET403已停；机构原表有实际HTML源行/表序/rawcells。网页日期、标准发布日期及实施日分列，没有标准发布日期即null。与读取的master及R09去重结果见validation-r10-root.json，未合库；子任务一条口头消息曾误称master1166，已核文件为889，文件及本批记录未改，不传播口头错误。

原文事实（审查冻结）：1410 canonical于14:24:41合为48条，正式完整14链接/12版本/12哈希，完整报批及送审各1另列，共2。源SHAa81a40dfff05c0bd437b99875baba5efc7f540c05ae9c59437aceb66d5aa65e2已复核。R09/R10仍只独立pending，检索不自行升级完整；发布状态单独由主控维护。

我的观点（方法）：一次对标准封面词与厂家公开附件域名检索，可补对失效大学链接的独立来源；同名下载项不能未经链接映射就充当父页。元数据扩展要区分政府和机构平台、不同来源重复、图集非四位年；基础方向无收益的查询也应留可复查负记录，以便下一轮换源而非重复消耗。

旧9个manifest输入全部校验未变。分享仅取本manifest结构化文件，无原PDF、PNG、HTML、瞬时下载参数值。未访问主控TTBZ浏览器或追隐藏API，未操作Git/外部账户。
'''%now
mp=search/'discussion-1430.md';assert not mp.exists();mp.write_text(discussion,encoding='utf-8')
rels=['round10-public-sources/candidates-r10-detection.json','round10-public-sources/instrument-observations-r10.json','round10-public-sources/query-ledger-r10-root.json','round10-public-sources/foundation/round10-foundation-search.json','round10-public-sources/monthly-directory/monthly-directory-r10.json','round10-public-sources/monthly-directory/validation-r10.json','round10-public-sources/validation-r10-root.json','round10-public-sources/audit-canonical-1410-receipt-r10.json','round10-public-sources/state-r10.json','discussion-1430.md']
for rel in rels:
 p=search/rel
 if p.suffix=='.json':read(p)
 assert not re.search(r'(?i)[?&](?:uhash|token|access_token|signature|secret|password)=',p.read_text(encoding='utf-8-sig')),rel
mf=search/'freeze-inputs-1430.json';assert not mf.exists()
manifest={'producer':'search','checkpoint':'14:30','checked_at':now,'frozen':True,'input_file_count':len(rels),'previous_freeze_integrity':checks,
 'note':'仅结构化候选/来源/负结果/回执。PDF签名不等于完整，目录不计全文；0成果如实登记。无PDF/PNG/原HTML/瞬时参数值。',
 'files':[{'path':'search/'+rel,'sha256':sha(search/rel),'bytes':(search/rel).stat().st_size} for rel in rels]}
mf.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'manifest':str(mf),'sha256':sha(mf),'files':len(rels),'new_candidate_routes':2,'foundation_candidates':0,'directory_source_rows':142,'directory_unique_complete_number_years':128,'not_in_master_and_r09':len(keys-master_keys-r09keys)},ensure_ascii=False))
