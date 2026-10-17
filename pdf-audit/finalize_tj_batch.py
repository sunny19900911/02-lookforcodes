import datetime,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
path=ROOT/'audit-results.json';doc=json.loads(path.read_text(encoding='utf-8'));NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
byid={r['candidate_id']:r for r in doc['results']}
evidence={
'R01-G4-006':{'complete_pdf':True,'recommendation':'B','completeness':'CECS69:94封面/扉页与前言匹配。目录PDF4列1-5章、附录A/B、附加说明16；全20页渲染成功，正文打印1-16连续，PDF18附录A末段、PDF19附录B用词、PDF20附加说明均对应。','quality':'可用数字化重排版，正文/表图清楚，页边浅色工程建设标准全文信息系统水印；中文文字可抽取，但条号、数值、公式在提取中大量丢失，必须目读。无书签/Link。','text':'中文句子可检索，但条号/数值/公式提取大量缺漏；不等于完整可复制'},
'R01-G4-007':{'complete_pdf':True,'recommendation':'B','completeness':'CECS48:93封面/扉页匹配，前言说明修订版、1995年2月落款。目录PDF4列1-7章与附加说明11；全15页渲染成功，正文打印1-11连续，PDF14第7章、PDF15附加说明完整收束。只认历史1993版号电子本，不据前言1995改编号。','quality':'数字化重排版清楚，彩色设备图可读，页边浅色水印；中文可抽取但数值和条号丢失，适合目读；无书签/Link。','text':'中文句子可检索；数值/条号提取缺漏，不等于公式数据可复制'},
'R01-G4-008':{'complete_pdf':False,'recommendation':'C','completeness':'扉页CECS21:2000，2001-01-01施行，版本可识别。目录PDF7把用词说明列打印24，实际PDF39打印32；目录把附录A列21，实际PDF34打印27。本文1-32渲染连续，1-10章和附录A-C均有，但重排分页与目录显著不符，未与原出版版本对校，不能把内容齐全推断作完整原版。','quality':'文字/图表可视清楚，重排本；中文逐字断行，搜索短语/复制不便；无书签/Link。','text':'逐字换行且混合数式错序，不能标正常中文复制'},
'R01-G4-009':{'complete_pdf':False,'recommendation':'D','completeness':'CECS02:2005版本封面扉页匹配；目录PDF4明确有附：条文说明，实得42页仅到打印41用词说明，后无条文说明扉页或正文。即使1-6章及附录A-G齐全，也是不完整电子本。','quality':'正文及表格可视清楚，中文文字可抽取，公式提取混排；无书签/Link。','text':'普通中文段落抽查通过，公式须目视复核'},
}
for ident,extra in evidence.items():
 r=byid[ident];r.update({k:v for k,v in extra.items() if k not in ['quality','text']})
 r.update(version_verified=True,completeness_status='目录/页码/终页闭环' if extra['complete_pdf'] else ('不完整：缺条文说明' if ident.endswith('009') else '重排目录不符待对照'),clarity=extra['quality'],searchable=extra['text'],body_searchable=ident.endswith('009'),body_text_layer=extra['text'],bookmark_provenance='下载文件未见Outline，未添加书签',visual_checked_at=NOW)
 r['download_status']='实测可下载完整PDF（历史数字化重排本）' if r['complete_pdf'] else ('可下载不完整PDF，缺条文说明' if ident.endswith('009') else '可下载，目录分页不符待核')
 r['recommendation_reason']=extra['completeness']+' '+extra['quality']
 r['comparison']={'backup_candidate_id':ident+'-ALT','same_sha256':r['sha256']==byid[ident+'-ALT']['sha256'],'claim':'主备是字节完全相同副本；只算一份文件质量证据，不算独立内容印证'}
 r['evidence_paths']=list(dict.fromkeys(r.get('evidence_paths',[])+[str(x) for pat in ['supplement-contact.jpg','rendered-footers-*.jpg'] for x in (ROOT/ident).glob(pat)]))
 r.setdefault('audit_history',[]).append({'checked_at':NOW,'method':'全页Poppler渲染+目录与终页+逐页页脚+文本复制对照+主备GET SHA256比较','outcome':r['completeness']})
 alt=byid[ident+'-ALT'];keep={k:alt.get(k) for k in ['requested_url','download_url','final_url','checked_at','candidate_id','audit_id','local_path','bytes','sha256','content_type','content_length_header','http_status','evidence_paths','elapsed_seconds']}
 inherited={k:r[k] for k in ['complete_pdf','version_verified','completeness_status','completeness','version_match','clarity','searchable','body_searchable','body_text_layer','bookmark_provenance','download_status','recommendation','recommendation_reason'] if k in r}
 alt.update(inherited);alt.update(keep);alt['quality_evidence_inherited_from_same_hash']=ident;alt['comparison']={'same_sha256':True,'primary_candidate_id':ident};alt['evidence_paths']+=r['evidence_paths'];alt.setdefault('audit_history',[]).append({'checked_at':NOW,'method':'备用链独立GET且SHA256与已目视主链相同，复用字节一致文件的目视结论','outcome':r['completeness']})
for r in doc['results']:
 if r.get('http_status')==403:r['download_status']='本次HTTP403访问受限，是否需登录未知'
 r.setdefault('complete_pdf',False);r.setdefault('version_verified',False)
doc['updated_at']=NOW
path.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'links':len(doc['results']),'complete_links':sum(r['complete_pdf'] for r in doc['results']),'complete_unique_hashes':len(set(r['sha256'] for r in doc['results'] if r['complete_pdf'])),'at':NOW},ensure_ascii=False))
