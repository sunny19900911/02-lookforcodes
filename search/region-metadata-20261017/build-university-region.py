import json,pathlib,hashlib,datetime,urllib.parse
B=pathlib.Path(r'C:\Users\mj528\Documents\004 工作\web-demo\outputs\cecs-master-20261017');O=B/'search/region-metadata-20261017';U=O/'universities'
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
def read(p):return json.loads((B/p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256((B/p).read_bytes()).hexdigest()
def write(p,d):
 q=O/p;assert not q.exists(),str(q);q.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raw=(B/'catalog/cecs-master.json').read_bytes();master=json.loads(raw.decode('utf-8-sig'))
eol=[dict(link_id=l['link_id'],download_url=l['requested_url']) for l in master['links'] if urllib.parse.urlsplit(l.get('requested_url') or '').hostname=='eol.nwafu.edu.cn']
assert len(eol)==4
hpu_source='search/round09-new-sources/candidates-r09-root-share.json'
hpu=[c for c in read(hpu_source)['candidates'] if urllib.parse.urlsplit(c.get('download_url') or '').hostname=='tmky.hpu.edu.cn']
assert len(hpu)==1
proofs=[dict(path=p,sha256=sha(p)) for p in ['search/region-metadata-20261017/universities/official-html-observations.json','search/region-metadata-20261017/universities/platform-identity-observations-v2.json']]
records=[dict(region_evidence_id='REG-SOURCE-NWAFU-EOL-20261017',source_id='REG-SOURCE-NWAFU-EOL-20261017',statement_type='原文事实（官方平台名称及高校官网地址）；省名规范化为AI整理',
 match_hosts=['eol.nwafu.edu.cn'],download_urls=[r['download_url'] for r in eol],existing_link_ids=[r['link_id'] for r in eol],
 source_entity='西北农林科技大学网络教学综合平台',proof_url='https://www.nwafu.edu.cn/',
 excerpt='地址：陕西杨凌 邮编：712100',source_location=dict(html_source_line=1269,web_parser_lines=[395,397]),
 identity_evidence=dict(source_id='REGION-NWAFU-EOL-IDENTITY-V2-20261017',proof_url='https://eol.nwafu.edu.cn/meol/jpk/course/layout/newpage/default_demonstrate.jsp?courseId=31600',
  excerpt='西北农林科技大学网络教学综合平台https://eol.nwafu.edu.cn/eol/homepage/common/',html_source_line=1316,decode_encoding='gb18030（原页面声明gbk）'),
 registered_source_page='https://eol.nwafu.edu.cn/meol/homepage/course/listview.jsp?_colId=null&_style=new03&acttype=enter&folderid=283225&lid=47196',
 official_region_raw='陕西杨凌',province='陕西省',city=None,locality_as_published='杨凌',
 download_source_region=dict(region_status='partial',province='陕西省',city=None,source_entity='西北农林科技大学网络教学综合平台',
  region_evidence_ids=['REG-SOURCE-NWAFU-EOL-20261017'],region_basis='平台正文明确名称及同域URL；学校官网页脚地址为陕西杨凌。省级已核，未把杨凌强行改为地级市或推定咸阳。'),
 city_boundary='原文仅杨凌，不推行政级别；city留空，交catalog选择地区摘要展示。',
 mapping_status='proposed_catalog_review',source_address_kind='高校主体官方公开地址',checked_at=now),
 dict(region_evidence_id='REG-SOURCE-HPU-TMKY-20261017',source_id='REG-SOURCE-HPU-TMKY-20261017',statement_type='原文事实（子站名称/主页链接及高校官网地址）',
 match_hosts=['tmky.hpu.edu.cn'],download_urls=[hpu[0]['download_url']],existing_candidate_ids=[hpu[0]['candidate_id']],
 source_entity='河南理工大学（tmky子站：生态建筑与环境构建工程实验室）',
 proof_url='https://www.hpu.edu.cn/xxgk/xxjj.htm',excerpt='地址：河南省焦作市世纪路2001号',source_location=dict(html_source_line=259,web_parser_lines=[36,37,38]),
 identity_evidence=dict(source_id='REGION-HPU-LAB-IDENTITY-20261017',proof_url='https://tmky.hpu.edu.cn/',
  excerpt='河南理工大学生态建筑与环境构建工程实验室',html_source_line=6,
  observed_school_home_link=dict(html_source_lines=[33,275],href='https://www.hpu.edu.cn/',anchor_text='学校主页/河南理工大学')),
 province='河南省',city='焦作市',official_region_raw='河南省焦作市',
 download_source_region=dict(region_status='verified',province='河南省',city='焦作市',
  source_entity='河南理工大学（tmky子站：生态建筑与环境构建工程实验室）',region_evidence_ids=['REG-SOURCE-HPU-TMKY-20261017'],
  region_basis='子站明确大学名称并链接学校主页；学校简介的公开地址明确河南省焦作市。本字段为高校主体公开地址，不推上传人员位置或具体校区。'),
 address_boundary='子站当前名称不冒称历史PDF的原作者；大学另有郑州校区，若要求具体上传部门实际驻地则应另待核，本提案仅高校主体公开地址。',
 access_boundary='既有PDF路线的404记录保留；本次未请求PDF，来源地区不表示该PDF已可下载。',
 original_candidate_input=dict(path=hpu_source,sha256=sha(hpu_source)),mapping_status='proposed_catalog_review',source_address_kind='高校主体官方公开地址',checked_at=now)]
write('university-region-evidence-proposal.json',dict(source_id='SEARCH-UNIVERSITY-SOURCE-REGION-20261017',recorded_at=now,
 instruction_source_id='USER-20261017-CECS-DOWNLOAD-SOURCE-REGION',scope_rule_source_id='USER-20261017-CECS-ENGINEERING-ALL',
 region_meaning='实际资料发布/下载来源主体的省市；不是标准适用地、CDN/IP或作者籍贯',
 schema_owner='catalog',schema='link.download_source_region; standards.download_source_regions仅聚合链接地区',
 source_snapshot=dict(path='catalog/cecs-master.json',sha256=hashlib.sha256(raw).hexdigest(),standards=len(master['standards']),links=len(master['links'])),
 evidence_files=proofs,evidence=records,subject_count=2,proposed_existing_master_links=4,proposed_pending_candidate_routes=1,
 auto_apply_to_master=False,scope='仅两个已登记高校下载主体，未遍历新地方标准',
 tianjin_status='本批未取得明确天津下载主体证据，不猜测归属，也不将该结论泛化为全库无天津来源。',
 limits=['match_hosts仅限已核具体子站，不泛用*.nwafu.edu.cn或*.hpu.edu.cn','优先按download_urls及已有链接ID映射，最终由catalog决定','无PDF GET、无规范新增、无完整数新增；质量/现行状态不变']))

aux=[]
for p,role in [('search/region-metadata-20261017/tjad/tjad-identity-pending.json','身份未闭合，不映射省市'),('search/region-metadata-20261017/beijing-organizations/beijing-organizations-crosscheck.json','分工确认前已获官方证据的交叉核对，catalog另有专人负责，不作为本高校registry输入')]:
 if (B/p).exists():aux.append(dict(path=p,sha256=sha(p),current_registry_input=False,role=role))
write('ancillary-observations-selection.json',dict(source_id='SEARCH-REGION-ANCILLARY-SELECTION-20261017',recorded_at=now,
 auxiliary_files=aux,notes=['knowledge.tjad.cloud不由tjad字母推同济设计或上海，81来源链接地区待核','cnass具体主体应核空间结构分会；勿把总会与分会省市依据混写','此辅助选择不启动新GET，不改catalog地域表']))
print(json.dumps(dict(subjects=2,master_links=4,pending_routes=1,nwafu_city=None,hpu_city='焦作市',pdf_get=0),ensure_ascii=False))
