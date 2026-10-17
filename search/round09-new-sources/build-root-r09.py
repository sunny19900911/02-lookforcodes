from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import urlsplit
import json,hashlib

base=Path(r'C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017')
folder=base/'search/round09-new-sources'
now=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
observations=read(folder/'public-route-observations-r09.json')['observations']
specs=[
 ('R09-HPU-69-2011','CECS 69:2011','69','2011','拔出法检测混凝土强度技术规程','G4','https://tmky.hpu.edu.cn/__local/C/50/C1/BC5CAAF66018396E9CD63FC4EDE_B2D81413_DFC9E.pdf?e=.pdf','正式历史版候选，封面及完整性待独立审查。',23,'河南理工大学域名公开附件；web解析为23页PDF，未独立完整GET。'),
 ('R09-CNASS-DRAFT-CABLE-ACCEPT','T/CECS XXX-202X',None,None,'建筑索结构工程施工质量验收标准','G3','https://www.cnass.cn/upload/gjgfenhui/file/20220815/1660537195190242.pdf','征求意见稿，封面明确；占位编号，不混正式版。',41,'协会分会域名公开PDF；web解析为41页并见封面征求意见稿。'),
 ('R09-DRAFT-PREFAB-LOW-CARBON','T/CECS XXX-202X',None,None,'装配式建筑低碳性能评价标准','G5','https://www.uibim.com/wp-content/uploads/2025/02/8e20c59990bd0f2.pdf','占位编号草稿，具体征求/送审/报批阶段未核。',None,'公开搜索索引PDF；web open失败、普通匿名GET握手超时，未绕过TLS。'),
 ('R09-DRAFT-DRAIN-MANHOLE-GRATING','T/CECS xxx-202X',None,None,'排水管道检查井悬挂式防坠落格板应用技术规程','G5','https://static1.tianyancha.com/czd_file/standard/30d8c78389ad4736c5f36a3b8365f980.pdf','占位编号草稿；索引外层标XXX-2020、内文标xxx-202X，年份不猜，具体阶段未核。',None,'第三方公开托管；普通匿名GET200/application/pdf且签名为PDF，仅读64bytes，不是全文审查。'),
 ('R09-DRAFT-WOOD-FIRE-COATINGS','T/CECS XXX-202X',None,None,'建筑木结构用防火涂料及阻燃处理剂应用技术规程','G3','https://static1.tianyancha.com/czd_file/standard/84734d2f62cf9e1bf8f8f41415e285b7.pdf','占位编号草稿，具体编制阶段待独立原稿核。',36,'第三方公开托管；web解析报36页PDF，封面编号与施行日占位。')
]
master_path=base/'catalog/cecs-master.json';master_raw=master_path.read_bytes();master=json.loads(master_raw.decode('utf-8-sig'))
urls=set()
def norm(s):
 u=urlsplit(s);return u.netloc.lower()+u.path
def walk(x):
 if isinstance(x,dict):
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
 elif isinstance(x,str) and x.startswith(('http://','https://')):urls.add(norm(x))
walk(master)
candidates=[]
for cid,std,number,year,name,group,url,stage,pages,access in specs:
    row={'candidate_id':cid,'source_id':'SEARCH-'+cid,'seed_ids':[],'topic_group':group,'standard_number':std,'number':number,'year':year,'name':name,
       'source_page':url,'parent_page_status':'未定位具体附件父页；source_page为实际公开索引PDF，不以域名首页冒充。',
       'download_url':url,'alternative_urls':[],'final_url':None,'draft_stage':stage,
       'permission_status':'公开索引/托管路线，无账号或付费操作；上传/转载授权未核。',
       'access_observation':access,'web_pages_observed':pages,
       'download_check_status':'候选待独立PDF版本/全文质量审查','complete_pdf':None,
       'recorded_at':now,'evidence_type':'原文事实（公开搜索索引/本轮工具解析或普通GET观察，非全文审查）',
       'duplicate_master_host_path':norm(url) in urls}
    ob=next((o for o in observations if o['requested_url']==url),None)
    if ob:
        row['access_checked_at']=ob['checked_at'];row['access_probe']=ob
        if ob.get('final_url'):row['final_url']=ob['final_url']
    if number=='69':
        row['unverified_historical_event']={'source_id':'HPU-69-2011-INDEX-NOTICE85','claim':'web解析第85号公告称69:2011自2011-10-01施行、69:94同时废止；2011-06-22落款。','boundary':'此为待审PDF的web文本观察，须审查角色核对原公告图像；不确认2011版于2026仍现行，继续保留94历史版。'}
    candidates.append(row)
assert len(candidates)==5 and not any(r['duplicate_master_host_path'] for r in candidates)
metadata=[]
for name,route in [
 ('建筑光伏系统检测标准','https://www.ttbz.org.cn/Home/PdfFileStreamGet/c3RuLDE1MTIxNA%28eq%29%28eq%29'),
 ('建筑施工企业碳排放核算标准','https://www.ttbz.org.cn/Home/PdfFileStreamGet/c3QsMTUxMDQ5')]:
    ob=next(o for o in observations if o['requested_url']==route)
    metadata.append({'source_id':'SEARCH-R09-TTBZ-DRAFT-ROUTE-'+route.rsplit('/',1)[-1],
       'name':name,'standard_number':'T/CECS XXX/XXXX-2025（占位编号）','number':None,'year':'2025','draft_stage':'公开索引的占位草稿；具体阶段未核。',
       'source_page':route,'download_url':None,'public_route_without_extra_query':route,
       'access_probe':ob,'boundary':'无额外查询参数的普通GET本次403，web为Internal Error或系统错误HTML；不作为已取得PDF候选。只保留元数据/失败路线，不推断登录要求或永久失效。'})
data={'schema_version':1,'source_id':'SEARCH-R09-ROOT-PUBLIC-ATTACHMENTS-20261017','recorded_at':now,
      'counts':{'pdf_candidates':5,'historical_formal_candidates':1,'placeholder_draft_pdf_candidates':4,'metadata_only_blocked_draft_routes':2},
      'candidates':candidates,'metadata_only':metadata,
      'dedupe_basis':{'master_path':'catalog/cecs-master.json','master_sha256_at_read':hashlib.sha256(master_raw).hexdigest(),'method':'host+path比较HTTP/HTTPS并忽略查询参数；5实际附件URL在此快照未见，不等于5编号主库净新增。'},
      'method_revision':'封面词主编单位/施行日期可减少学术论文引用噪声；占位号必须单列。TTBZ公开索引流地址若实际GET403，不把目录/索引文字升级成可用PDF。'}
p=folder/'candidates-r09-root.json';assert not p.exists();p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audit=base/'pdf-audit/audit-pending-round06-freeze-1410.json'
assert sha(audit)=='455b212b19fd80b644aa82c64e5592d07e35fc27fd462c99571dbd6fdebb4b57'
a=read(audit)
fields=['candidate_id','standard_key','recommendation','recommendation_reason','complete_pdf','draft_content_complete','version_class','publication_edition','version_match','completeness','pages','sha256','requested_url','final_url']
receipt={'source_id':'SEARCH-R09-RECEIPT-AUDIT-1410-20261017','recorded_at':now,
 'statement_type':'原文事实（审查独立冻结回执；检索侧未重新定级）',
 'audit_freeze_path':'pdf-audit/audit-pending-round06-freeze-1410.json','audit_freeze_sha256':sha(audit),
 'results':[{k:r.get(k) for k in fields} for r in a['results']],
 'new_decisions':{'formal_complete_B':4,'complete_submission_draft_B_separate':1,'C':2,'TLS_failure':1},
 'canonical_at_receipt':'40条仍冻结；1410这8条pending需主控授权。合入后48/正式14链12版12哈希为预期，不能先称已合。',
 'method_boundary':'122/17为本件数字排版闭合，不宣称出版社原页式；287出版身份未闭合，不直接判草案；333疑似空白页缺证明不叫正文已缺失；草案B不计正式完整。'}
rp=folder/'quality-feedback-r09-audit-1410.json';assert not rp.exists();rp.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'candidate_path':str(p),'sha256':sha(p),'candidates':5,'blocked_metadata_routes':2,'audit_receipt_sha256':sha(rp)},ensure_ascii=False))
