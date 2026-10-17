from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib

base=Path(r'C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017')
folder=base/'search/round08-public-expansion'
now=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
obs=json.loads((folder/'public-page-observations-r08.json').read_text(encoding='utf-8-sig'))
desktop=next(r for r in obs['observations'] if r['requested_url']=='https://www.cnass.cn/site/content/325.html')
mobile=next(r for r in obs['observations'] if r['requested_url']=='https://m.cnass.cn/site/content/325.html')
links=[r for r in desktop['relevant_links'] if 'CECS' in r['text'].upper()]
formal_specs=[('212','2006','预应力钢结构技术规程',[]),('235','2008','铸钢节点应用技术规程',['S041']),('333','2012','结构健康监测系统设计标准',[])]
candidates=[]
for number,year,name,seeds in formal_specs:
    l=next(l for l in links if l['text'].startswith('CECS '+number+'-'))
    backup=next(r['url'] for r in mobile['relevant_links'] if r['text']==l['text'])
    candidates.append({
        'candidate_id':f'R08-CNASS-{number}-{year}', 'source_id':f'SEARCH-R08-CNASS-{number}-{year}',
        'seed_ids':seeds,'topic_group':'G3','standard_number':f'CECS {number}:{year}', 'number':number,'year':year,'name':name,
        'source_page':desktop['requested_url'],'source_page_alternatives':[mobile['requested_url']],
        'download_url':l['url'],'alternative_urls':[backup],'final_url':None,
        'draft_stage':'正式历史版候选，待PDF封面核验；2026现行性未核',
        'source_link_text':l['text'],'source_page_access':{'method':'普通匿名GET','http_status':desktop['http_status'],'checked_at':desktop['checked_at']},
        'permission_status':'分会公开资料页无登录/付费即可读到附件href；PDF尚未GET，转载授权未核。',
        'download_check_status':'候选未审；父页GET成功不证明PDF可下载或完整。',
        'complete_pdf':None,'metadata_evidence':[{'source_url':desktop['requested_url'],'source_id':'CNASS-CONTENT-325-20261017','evidence_type':'原文事实（实际HTML附件名称与href）','claim':'页面列示该名称及附件地址；封面及完整性由独立PDF审查判定。'}],
        'dedupe_note':'2026-10-17 13:57读取catalog/cecs-master.json，按host+path合并HTTP/HTTPS比对，未见该附件URL；不表示编号在主库不存在。'
    })
l=next(l for l in links if '工业建筑非工业化' in l['text'])
backup=next(r['url'] for r in mobile['relevant_links'] if r['text']==l['text'])
candidates.append({
    'candidate_id':'R08-CNASS-DRAFT-INDUSTRIAL-CONVERSION','source_id':'SEARCH-R08-CNASS-DRAFT-INDUSTRIAL-CONVERSION',
    'seed_ids':[],'topic_group':'G3','standard_number':'T/CECS（编号未见）','number':None,'year':None,
    'name':'工业建筑非工业化改造结构检测鉴定标准','source_page':desktop['requested_url'],
    'download_url':l['url'],'alternative_urls':[backup],'final_url':None,
    'draft_stage':'附件名标送审稿；PDF封面阶段/占位编号待核，不混正式版。','source_link_text':l['text'],
    'source_page_access':{'method':'普通匿名GET','http_status':desktop['http_status'],'checked_at':desktop['checked_at']},
    'permission_status':'公开资料页提供实际href；PDF未GET，转载授权未核。','download_check_status':'草案候选未审','complete_pdf':None
})
leju='https://media.src.leju.com/imp/imp/deal/10/1f/3/e20c955f600d4a5ca00a52e7ac1_p24_mk24.pdf'
leju_obs=next(r for r in obs['observations'] if r['requested_url']==leju)
candidates.append({
    'candidate_id':'R08-DRAFT-GREEN-RESIDENTIAL-LEJU','source_id':'SEARCH-R43-GREEN-RESIDENTIAL-DRAFT',
    'seed_ids':[],'topic_group':'G5','standard_number':'T/CECS ***:201x','number':None,'year':None,'name':'绿色住区标准',
    'source_page':leju,'download_url':leju,'alternative_urls':[],'final_url':None,
    'draft_stage':'公开搜索索引封面写征求意见稿、编号占位；未得正文核验，不混正式版。',
    'permission_status':'公开索引PDF；web open超时，普通GET本次TLS握手失败，未绕过证书校验/认证。',
    'download_check_status':'草案候选未审；本次连接失败非永久失效结论。','complete_pdf':None,
    'access_observation':leju_obs,'parent_page_status':'未定位具体父页；source_page为实际索引PDF。'
})
metadata=[]
for l in links:
    if not l['url'].lower().endswith(('.doc','.docx')):continue
    metadata.append({'source_id':'SEARCH-R08-CNASS-WORD-'+l['url'].rsplit('/',1)[-1].split('.')[0],
        'name_raw':l['text'],'source_page':desktop['requested_url'],'document_url':l['url'],
        'download_url':None,'format':l['url'].rsplit('.',1)[-1].upper(),'draft_stage':'页面附件名明确征求意见稿；未读取Word原文，不当正式版。',
        'counting_boundary':'非PDF，仅登记格式与来源路线；不计PDF候选/完整PDF。'})
data={'schema_version':1,'producer':'search/root','round':'R08','recorded_at':now,
    'source_id':'SEARCH-R08-ASSOCIATION-ATTACHMENTS-20261017',
    'counts':{'pdf_candidates':len(candidates),'historical_formal_candidates':3,'draft_pdf_candidates':2,'non_pdf_word_draft_routes':len(metadata)},
    'candidates':candidates,'metadata_only_non_pdf_routes':metadata,
    'failed_routes':[{'source_page':'https://www.lsjcrzzx.com/','observation':'web超时/普通GET证书过期；未关闭证书校验；0附件。'}],
    'excluded':[{'source_page':'https://www.ctc.ac.cn/module/download/downfile.jsp?classid=0&filename=f7f914875f014191b29768cee7e8d07d.pdf','reason':'儿童友好认证实施规则，仅引用CECS绿色建材标准，不是CECS全文。'},
        {'source_page':'https://www.webfree.net/download/2544','reason':'第三方介绍/压缩下载路线，未得公开直接PDF，无新增候选；不依据页数声称其为优于已审本的替代。'}],
    'method_revision':'协会资料页web工具超时后，普通匿名GET可读；实际href带出3历史+1送审PDF，另2Word草稿不冒充PDF。10025/10032清洁替代本两轮8查询未得新公开PDF。'}
p=folder/'candidates-r08-association.json'
assert not p.exists()
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audit=base/'pdf-audit/audit-pending-round05-freeze-1350.json'
assert sha(audit)=='90081712aea2c2ddb78202101d3e31753828ed6e663af87a139ec9e007e7dcf8'
a=json.loads(audit.read_text(encoding='utf-8-sig'))
fields=['candidate_id','standard_key','checked_at','reviewed_at','recommendation','recommendation_reason','complete_pdf','draft_content_complete','version_class','version_match','completeness','pages','sha256','requested_url','final_url']
receipt={'source_id':'SEARCH-R08-AUDIT-1350-RECEIPT-20261017','recorded_at':now,
    'statement_type':'原文事实（读取审查独立冻结结果；检索侧不重新目视定级）',
    'audit_freeze_path':'pdf-audit/audit-pending-round05-freeze-1350.json','audit_freeze_sha256':sha(audit),
    'results':[{k:r.get(k) for k in fields} for r in a['results']],
    'counts':{'new_formal_complete_links_audit_verified':1,'complete_approval_draft_audit_verified':1,'candidates_remaining_C':2,'get_403':3},
    'canonical_boundary':'canonical33仍冻结。本批7条pending未由主控授权合并时，不能声称canonical已40；正式完整10链/8版/8哈希仅为合并后预期。',
    'method_followup':'10025水印完整本只作备用；41/164页码跳跃的空白性质无证据，不直接断言正文缺失；草案B不计正式完整。'
}
rp=folder/'quality-feedback-r08-audit-1350.json'
assert not rp.exists()
rp.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'candidates_path':str(p),'candidate_count':len(candidates),'word_routes':len(metadata),'candidate_sha256':sha(p),'quality_receipt_sha256':sha(rp)},ensure_ascii=False))
