from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,re

base=Path(r'C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017');search=base/'search';folder=search/'round11-public-sources'
now=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
instrument_files=list((folder/'instrument-pages').glob('*.json'));assert len(instrument_files)==1,'Wait for fixed instrument JSON'
ip=instrument_files[0];instrument=read(ip);assert len(instrument['candidates'])==1
names=['freeze-inputs-1320.json','freeze-inputs-round04.json','freeze-inputs-1330.json','freeze-inputs-1340.json','freeze-inputs-1340-water-mep-addendum.json','freeze-inputs-1340-water-mep-addendum-v2.json','freeze-inputs-g2-round02-share-1350.json','freeze-inputs-1400.json','freeze-inputs-1420.json','freeze-inputs-1430.json']
checks=[]
for n in names:
 m=read(search/n);bad=[x['path'] for x in m['files'] if sha(base/x['path']).lower()!=x['sha256'].lower()];checks.append({'manifest':'search/'+n,'files':len(m['files']),'unchanged':not bad,'failures':bad})
assert all(x['unchanged'] for x in checks)
root=read(folder/'candidates-r11-root.json');assert len(root['candidates'])==5
all_candidates=root['candidates']+instrument['candidates'];assert len({r['candidate_id'] for r in all_candidates})==6
dp=folder/'monthly-directory/monthly-directory-r11.json';assert sha(dp)=='141e8c0428f268cabb0bc9d4a4503f0b2c66739a74423e9c037af1444de18e45';d=read(dp);rows=d['records'];assert len(rows)==117
assert all(r['source_location'] and r['raw_cells'] for r in rows);assert len({r['record_id'] for r in rows})==117
keys={r['number_year_key'] for r in rows if r.get('number_year_key')};assert len(keys)==116
mb=(base/'catalog/cecs-master.json').read_bytes();master=json.loads(mb.decode('utf-8-sig'));rx=re.compile(r'CECS\s*(\d+)\s*[-:：－—]\s*(\d{4})',re.I)
mk={str(int(m.group(1)))+'/'+m.group(2) for r in master['standards'] if (m:=rx.search(r.get('standard_number','')))}
older=set()
for rel in ['round09-new-sources/recent-directory/recent-directory-r09.json','round10-public-sources/monthly-directory/monthly-directory-r10.json']:
 older.update(r['number_year_key'] for r in read(search/rel)['records'] if r.get('number_year_key'))
v={'source_id':'SEARCH-R11-INDEPENDENT-VALIDATION','recorded_at':now,'source_rows':117,'complete_unique_keys':116,'all_actual_locations':True,'master_count_at_read':len(master['standards']),'master_sha256_at_read':hashlib.sha256(mb).hexdigest(),'master_overlap':len(keys&mk),'prior_pending_overlap':len(keys&older),'new_keys_at_read':sorted(keys-mk-older),'merge_count':0,'boundary':'去重快照而非已合库净增；机构补充与政府分开，缺年份不猜。'}
vp=folder/'validation-r11-root.json';assert not vp.exists();vp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ep=base/'pdf-audit/evidence-85-repeal-cecs69-94.json';assert sha(ep)=='442e9485aae9fed84a118ebfdc0365e80bb2328ef05ba901958274a81178f95e';e=read(ep)
fields=['source_id','checked_at','candidate_id','source_url','pdf_sha256','pdf_physical_page','page_side','printed_page','position_note','announcement_issuer','announcement_number','announcement_date','implementation_date','repealed_standard_number','repealed_standard_title','repeal_effective_date','review_method','boundaries']
er={'source_id':'SEARCH-R11-RECEIPT-85-REPEAL','recorded_at':now,'statement_type':'原文事实（第三方托管出版物内协会公告的审查双目视回执；检索侧未重复核图）','source_path':'pdf-audit/evidence-85-repeal-cecs69-94.json','source_sha256':sha(ep),'evidence_received':{k:e.get(k) for k in fields},'boundary':'支持69:94自2011-10-01同时废止的历史事件；2011版2026现行性未知，原94历史副本与HPU404不覆盖。PDF/PNG均仅本地。'}
erp=folder/'receipt-85-repeal-r11.json';assert not erp.exists();erp.write_text(json.dumps(er,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
canon=(base/'pdf-audit/audit-results.json').read_bytes();a=json.loads(canon.decode('utf-8-sig'))
state={'source_id':'SEARCH-R11-CHECKPOINT-1440','recorded_at':now,'new_pdf_candidates':6,'root_candidates':5,'instrument_new_pdf_candidates':1,'non_pdf_doc_routes':1,'short_pdf_routes':1,'existing_41_alternate_routes':1,'new_directory_source_rows':117,'directory_complete_unique_number_years':116,'directory_unresolved':1,'government_rows':77,'institute_supplement_rows':40,'new_keys_vs_master_r09_r10':sorted(keys-mk-older),'actual_merge_count':0,'audit_canonical_at_read':{'results':len(a['results']),'sha256':hashlib.sha256(canon).hexdigest(),'updated_at':a.get('updated_at')},'pending_1430_boundary':'R09新增正式完整0、内容完整草案3；需主控批准，不先计54。R10两条固定C/D另批，不先计56。','search_added_complete_count':0,'historical_event_verified_by_audit':'69:94自2011-10-01同时废止，见receipt-85-repeal-r11.json；不推断2011版2026现行。','old_freeze_integrity':checks,'boundary':'所有新输入仅metadata与实际来源路由；无PDF/PNG/原HTML/瞬时参数值/Git/账户操作。'}
sp=folder/'state-r11.json';assert not sp.exists();sp.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
discussion='''# 14:40 检索检查点

source_id: SEARCH-DISCUSSION-1440-20261017；记录时间：%s（北京时间）。

原文事实（公开PDF）：6新PDF候选。根检索5条正式编号外观：31-2017（apextray，web64页，另guangyuxc未审备链）、1555-2024碳中和（web30页）、200:2006防火（重排web96页，不据其他书页数断缺）、197:2006孔内强夯（web34页0文字）、165:2004地下通信（web本次失败，只有公开索引）。仪器公开栏目另02:2005普通GET为PDF，不自评完整；21:2000实际为DOC，仅非PDF路线，不转换。Antpedia161:2004 web3页0文字只短文件路线，不以3页直接定正文缺失。41:2004另ysj未审备链属于已有版本，不重复新候选。所有具体父页不明确的保持未知，不以同名页/首页冒充。

原文事实（目录）：4来源117行＝政府77＋机构补充40，116个完整编号年份，1条50006J-25年份缺口不猜。全部有实际定位/rawcells；对主库、R09、R10独立去重结果见validation-r11-root.json，只有1861/1865/1867/1870四个2025编号未见三快照，均为机构补充。政府条目只增加独立来源证据，净新编号为0。发布/网页/实施日期分开，无标准发布日期就null，不据历史清单确认2026现行。

原文事实（审查回执）：1430独立冻结6项的正式完整新增0、完整草案3（索验收征求、格板/木涂报批），政府243因原图空限值与乱码仍C不补数。R10新69实得23物理双页扫描C，疑背页缺可靠空白证明、带大水印，不升级完整；另02证书错误D。两批仍独立pending，不能先称canonical54/56。当前canonical读取值在state-r11.json中锁定时刻记录。

原文事实（历史事件）：69厂家PDF内第85号公告已双审目视，PDF2左公告无印刷folio、右为前言；2011-06-22落款，自2011-10-01施行并69:94同时废止。收到原证据SHA442e9485aae9fed84a118ebfdc0365e80bb2328ef05ba901958274a81178f95e，已核。只支持旧版历史废止事件，不确认2011版于2026仍现行；保留旧94下载与HPU当次404，不追改旧冻结事实。

我的观点（方法）：带批准/施行/主编的封面词比泛CECS可降低论文引用噪声；第三方副本的重排、错OCR、正文限值空白要由PDF质量审查判定，不能因政府/厂家域名就升级。月度目录后续重叠变多，应优先未覆盖月份并保留来源补强价值，不把每条来源重复当新增标准。

仅分享manifest列结构化文件。旧10个manifest输入全部哈希未变；无原PDF、PNG、HTML、瞬时参数值、账号访问或Git。根的CCTC2017成果表只登记待结构化路线，未据标题把它当全文。
'''%now
mp=search/'discussion-1440.md';assert not mp.exists();mp.write_text(discussion,encoding='utf-8')
rels=['round11-public-sources/candidates-r11-root.json','round11-public-sources/alternate-route-41-r11.json','round11-public-sources/query-ledger-r11-root.json','round11-public-sources/quality-feedback-r11-audit-1430.json','round11-public-sources/receipt-85-repeal-r11.json','round11-public-sources/monthly-directory/monthly-directory-r11.json','round11-public-sources/monthly-directory/validation-r11.json',ip.relative_to(search).as_posix(),'round11-public-sources/validation-r11-root.json','round11-public-sources/state-r11.json','discussion-1440.md']
for rel in rels:
 p=search/rel
 if p.suffix=='.json':read(p)
 assert not re.search(r'(?i)[?&](?:uhash|access_token|token|signature|secret|password)=',p.read_text(encoding='utf-8-sig')),rel
mf=search/'freeze-inputs-1440.json';assert not mf.exists()
m={'producer':'search','checkpoint':'14:40','checked_at':now,'frozen':True,'input_file_count':len(rels),'previous_freeze_integrity':checks,'note':'候选/短PDF/DOC/已有版本备链/目录来源分开，不增加完整数；无PDF/PNG/原HTML/瞬时参数值。','files':[{'path':'search/'+rel,'sha256':sha(search/rel),'bytes':(search/rel).stat().st_size} for rel in rels]}
mf.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'manifest':str(mf),'sha256':sha(mf),'files':len(rels),'pdf_candidates':6,'source_rows':117,'new_directory_keys':sorted(keys-mk-older),'canonical_count_observed':len(a['results'])},ensure_ascii=False))
