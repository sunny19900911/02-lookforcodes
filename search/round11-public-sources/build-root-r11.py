from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import urlsplit
import json,hashlib

base=Path(r'C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017');folder=base/'search/round11-public-sources'
now=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
specs=[
 ('R11-31-2017-APEXTRAY','T/CECS 31-2017','2017','钢制电缆桥架工程技术规程','G5','https://apextray.com/wp-content/uploads/2024/11/TCECS31-2017-Technical-Specification-for-Steel-Cable-Tray-Engineering.pdf',64,'web解析PDF；数字/字词提取错误明显，不代替原图。'),
 ('R11-1555-2024-FAIUSR','T/CECS 1555-2024','2024','碳中和建筑评价标准','G5','https://25978851.s21i.faiusr.com/61/ABUIABA9GAAgldCDsAYonZeS2gY.pdf',30,'web解析PDF；正式编号外观，出版身份/全书闭合待审。'),
 ('R11-200-2006-DLSSYHT','CECS 200:2006','2006','建筑钢结构防火技术规范','G3','https://aimg8.dlssyht.cn/u/1746078/ueditor/file/874/1746078/1637213419201475.pdf',96,'web解析PDF，重排外观及条文说明字样不能证明说明正文齐全；不按其他介绍页数判缺。'),
 ('R11-197-2006-FAIUSR','CECS 197:2006','2006','孔内深层强夯法技术规程','G1','https://12889079.s21i.faiusr.com/61/ABUIABA9GAAgp4vS0gUojLf40QQ.pdf',34,'web报34页，提取行数0；封面名称来自公开索引，须独立核图。'),
 ('R11-165-2004-YSJIANZHAN','CECS 165:2004','2004','城市地下通信塑料管道工程设计规范','G5','https://pro5323b5d3-pic11.ysjianzhan.cn/upload/94CECS165-2004CSDXTXSLGDGCSJGF.pdf',None,'公开索引PDF，web open本次Internal Error；同host其他件403不预断本URL。')
]
master_path=base/'catalog/cecs-master.json';mb=master_path.read_bytes();master=json.loads(mb.decode('utf-8-sig'))
seen=set()
def norm(u):s=urlsplit(u);return s.netloc.lower()+s.path
def walk(x):
 if isinstance(x,dict):
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
 elif isinstance(x,str) and x.startswith(('http://','https://')):seen.add(norm(x))
walk(master)
rows=[]
for cid,std,year,name,group,url,pages,ob in specs:
 row={'candidate_id':cid,'source_id':'SEARCH-'+cid,'seed_ids':[],'standard_number':std,'year':year,'name':name,'topic_group':group,
  'source_page':url,'parent_page_status':'具体附件父页未定位；source_page为实际公开索引PDF，不以首页或同名页冒充父页。',
  'download_url':url,'final_url':None,'alternative_urls':[],'draft_stage':'正式编号的历史/发布版候选；封面、版本身份和完整性待独立审查。',
  'permission_status':'公开索引/托管路线，无账号操作，转载授权未核。',
  'recorded_at':now,'web_pages_observed':pages,'web_observation':ob,'download_check_status':'候选未独立GET/全文审查','complete_pdf':None,
  'duplicate_master_host_path':norm(url) in seen,'evidence_type':'原文事实（本轮公开索引与web解析观察，非独立质量结论）'}
 if cid=='R11-31-2017-APEXTRAY':
  row['alternative_urls']=['https://guangyuxc.com/app/3/16%E9%92%A2%E5%88%B6%E7%94%B5%E7%BC%86%E6%A1%A5%E6%9E%B6%E5%B7%A5%E7%A8%8B%E6%8A%80%E6%9C%AF%E8%A7%84%E7%A8%8BT_CECS31-2017.pdf']
  row['alternative_status']='另一真实公开索引PDF，web open本次失败；尚未实测GET，不称已审备件。'
 rows.append(row)
assert len(rows)==5 and not any(r['duplicate_master_host_path'] for r in rows)
d={'schema_version':1,'source_id':'SEARCH-R11-ROOT-ATTACHMENTS-20261017','recorded_at':now,'candidates':rows,
 'counts':{'pdf_candidates':5,'numbered_publication_or_historical_candidates':5,'placeholder_drafts':0,'short_pdf_routes_separate':1},
 'short_pdf_routes':[{'source_id':'SEARCH-R11-161-2004-ANTPEDIA-SHORT','standard_number':'CECS 161:2004','name':'喷射混凝土加固技术规程','source_page':'https://img.antpedia.com/standard/files/pdfs_ora/CN-CECS/762/CECS%20161-2004.pdf','preview_url':'https://img.antpedia.com/standard/files/pdfs_ora/CN-CECS/762/CECS%20161-2004.pdf','download_url':None,'web_pages':3,'web_text_lines':0,'statement_type':'原文事实（web报告页数）；AI推断（疑似短预览，正文范围尚未独立核图）','boundary':'另列短PDF路线，不计本批5全文候选或正式完整，不能仅按3页断定原标准正文缺失。'}],
 'metadata_routes':[{'source_id':'SEARCH-R11-CCTC-2017-TABLE','source_page':'https://www.cctc.cn/ttbz/bzgf/kjcg/kjcx/2017n/index.shtml','observation':'集团公开2017团体标准编制成果表，字段含标准名/号/发布时间/实施/主编；本轮只登记路线，未逐项结构化，不作全文。'}],
 'dedupe_snapshot':{'master_sha256':hashlib.sha256(mb).hexdigest(),'master_identity_count':len(master['standards']),'method':'host+path忽略HTTP/HTTPS/查询，仅证明URL未见，不证明编号不存在。'}}
p=folder/'candidates-r11-root.json';assert not p.exists();p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
add={'source_id':'SEARCH-R11-41-ALTERNATE-20261017','recorded_at':now,'existing_candidate_id':'R07-WATER-MEP-41-2004','standard_number':'CECS 41:2004','additional_indexed_pdf_url':'https://pro5323b5d3-pic11.ysjianzhan.cn/upload/34CECS41-2004JZGSYJLYXGGDGCJSGC.pdf','source_page':'https://pro5323b5d3-pic11.ysjianzhan.cn/upload/34CECS41-2004JZGSYJLYXGGDGCJSGC.pdf','access_status':'公开搜索索引，未GET；不是已审备份','counting_boundary':'已有同版本的新URL路线，不新增标准/版本/本批5候选数；是否同hash待独立GET。'}
ap=folder/'alternate-route-41-r11.json';assert not ap.exists();ap.write_text(json.dumps(add,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audit=base/'pdf-audit/audit-pending-round07-freeze-1430.json';assert sha(audit)=='1f75a6b1536d5265a2a8cb814e1c2d1c7630de38d9dd49ec707650a174aebe0f';a=read(audit)
fields=['candidate_id','standard_key','recommendation','recommendation_reason','complete_pdf','draft_content_complete','version_class','completeness','pages','sha256','requested_url','final_url']
receipt={'source_id':'SEARCH-R11-AUDIT-1430-RECEIPT','recorded_at':now,'source_path':'pdf-audit/audit-pending-round07-freeze-1430.json','sha256':sha(audit),'statement_type':'原文事实（审查独立冻结回执）','results':[{k:r.get(k) for k in fields} for r in a['results']],'new_formal_complete':0,'new_complete_drafts':3,'canonical_boundary':'尚待主控批准；当前已收到canonical48冻结，不能先称54。','method':'政府243原图空限值/乱码维持C不补数；来源级别与文本质量分开。3完整草案不混正式完整。69新厂家另批不覆盖HPU404。'}
rp=folder/'quality-feedback-r11-audit-1430.json';assert not rp.exists();rp.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'candidates':5,'path':str(p),'sha256':sha(p),'audit_receipt_sha256':sha(rp)},ensure_ascii=False))
