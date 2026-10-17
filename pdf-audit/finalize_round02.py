import datetime, json, pathlib
ROOT=pathlib.Path(__file__).resolve().parent
NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
p=ROOT/'audit-results.json';doc=json.loads(p.read_text(encoding='utf-8'))
updates={
 'AUD-PUBLIC-001': {
  'complete_pdf':False,'version_verified':True,'completeness_status':'未闭环：页码58附近疑似省空白页，未获得对照本',
  'completeness':'目录PDF7-10列1-8章、附录A/B、用词、引用规范与条文说明。正文打印1-56连续；PDF67为条文说明扉页（目录57），PDF68直接为目录59，须核打印58是否确为空白。后续59-89连续，PDF98附录B条文说明B.0.3自然结束；PDF99/100均为封底重复。不能声称打印90或整本无缺页。',
  'recommendation':'C','recommendation_reason':'正文与附录可读，版本正确；打印58的缺口性质尚未用对照本证明，保留完整性待核。',
  'visual_review_pages':[1,5,7,8,9,10,11,12,50,51,52,96,97,98,99,100],
  'page_continuity':'逐页图像页脚查1-56、59-89；57为扉页，58未见；两张页脚接触表保存证据',
  'body_searchable':False,'body_text_layer':'正文扫描，无可用中文文本层；末页43字符为网页导航，不属于正文',
 },
 'AUD-PUBLIC-002': {
  'complete_pdf':True,'version_verified':True,'completeness_status':'目录、全部正文页码与终页闭环',
  'completeness':'封面与第1270号发布公告匹配T/CECS1140-2022。PDF9-14中英文目录含1-12章、附录A-F、用词、引用标准及条文说明；正文PDF15-192打印1-178逐页连续。目录条文说明117起，PDF190为附录C说明，PDF191-192为附录E说明，E.4.1在178页以完整句结束。无内容页码断档。',
  'recommendation':'B','recommendation_reason':'官方公开附件，版本及正文完整性闭环，扫描正文表格清楚；无正文文本层、书签或目录Link，文件约31.4MB。',
  'visual_review_pages':[1,5,7,8,9,10,11,12,13,14,15,70,97,190,191,192],
  'page_continuity':'已逐页审看全部1-178页脚，四张页脚接触表；非逐字校对',
  'body_searchable':False,'body_text_layer':'扫描件，无文本层',
 },
 'AUD-PUBLIC-003': {
  'complete_pdf':True,'version_verified':True,'completeness_status':'官方电子版正文完整性闭环（保留版本异常）',
  'completeness':'来源详情页明确作为正式发布规程的电子版附件。PDF5/6总目录列至条文说明29；PDF36条文说明目录末项为第8章55；PDF7-61打印1-55连续，全部61页Poppler渲染成功。终页55的8.0.8、公式(1)及C系数说明自然结束，目录无更后章节/附录。此结论限该官方电子版，不宣称与出版社纸本逐页同一。',
  'version_anomalies':['PDF35条文说明扉页仍有T/CECS ***-20**占位编号','PDF元数据Title为内部资料；不得据此否认官方详情页正式发布属性，也不静默掩盖'],
  'version_match':'封面T/CECS935-2021与国管局正式发布电子版详情页一致；内页占位编号作为异常保留',
  'recommendation':'B','recommendation_reason':'官方发布电子版正文与目录/页码/终页闭环，矢量文字清楚，可复制中文并有可用目录Link；无原生书签，条文说明扉页占位编号须告知。',
  'visual_review_pages':[1,4,5,6,7,31,34,35,36,59,60,61],
  'page_continuity':'PDF7-61全部打印1-55提取校验，且61页全渲染成功；页脚接触表人工核对',
  'body_searchable':True,'body_text_layer':'正文中文可抽取；抽核PDF7首段及PDF61末段与图像一致，公式复制含符号错序，数式须对照图像',
  'searchable':'中文正文搜索复制抽查通过；公式字符复制有错序，不能把文本提取当计算公式真值',
  'clickable_toc':'文件76条Link全部解析为有效内部目标；PDF5中文目录22条逐项核对目标页/章节（含同一项重复注释），PDF6英文目录38条、PDF36条文说明目录16条目标有效。链接均在目录页，部分条目重复注释，不是76个书签。',
  'link_navigation_evidence':'link-target-evidence.json记录矩形与内部目标；目标有效不代表已在每款阅读器鼠标点击',
  'source_evidence':{'source_url':'https://ecpi.ggj.gov.cn/tzgg/202111/t20211125_40789.htm','claim':'2021-11-25正式发布消息，电子版附件供公共机构参照使用，2022-03-01起施行','type':'原文事实','checked_at':NOW},
 },
 'AUD-PUBLIC-004': {
  'complete_pdf':True,'version_verified':True,'completeness_status':'目录、全部正文页码与终页闭环',
  'completeness':'目录PDF5/6列1-8章、附录A/B、用词说明（打印37）；PDF7-43打印1-37逐页连续，PDF42为附录B末段B.0.5，PDF43为用词说明完整结尾，PDF44-46确为空白尾页。全部46页Poppler渲染成功。',
  'recommendation':'B','recommendation_reason':'交通部公开附件版本与正文完整性闭环，文字、公式可视清楚；中文复制乱码严重，无书签/Link，主要适合目读。',
  'visual_review_pages':[1,5,6,7,24,42,43,44,45,46],
  'page_continuity':'全46页渲染及1-37页码目视连续；保存页脚接触表',
  'body_searchable':False,'body_text_layer':'有字体文字对象，中文提取为/Gxx乱码，不能据text_layer=true声称正文中文可搜索',
  'standard_year':2018,'implementation_date':'2019-04-01',
 },
 'R01-G3-003': {
  'complete_pdf':False,'version_verified':True,'completeness_status':'不完整征求意见稿：条文说明仅扉页',
  'version_match':'封面明确征求意见稿与T/CECS XXX-202X占位编号；未识别正式编号年份',
  'version_class':'征求意见稿','standard_key':'DRAFT-建筑索结构节点设计标准-20201023',
  'completeness':'PDF4目录末项条文说明打印56；PDF61正好是条文说明扉页，之后无任何条文说明正文。前55页技术正文、附录与引用标准可读，但不是目录所含全部材料，不能作为完整正式标准或完整征求意见稿推荐。',
  'download_status':'可下载的不完整征求意见稿（条文说明缺正文）','recommendation':'D','recommendation_reason':'占位编号征求意见稿且条文说明仅扉页；技术正文可参考，不进入完整PDF集合。',
  'visual_review_pages':[1,3,4,5,6,7,30,59,60,61],
  'clarity':'矢量文字和公式清楚，无明显水印；仅正文与附录可读',
  'body_searchable':True,'body_text_layer':'中文正文可抽取，公式提取可能错序',
 },
 'R01-G4-005': {
  'name':'绿色建材评价 保温系统材料','standard_key':'T/CECS 10032-2019','complete_pdf':True,'version_verified':True,
  'completeness_status':'12页全部目视，目录/页码/终页闭环',
  'version_match':'封面及页眉T/CECS10032-2019；正式名称绿色建材评价 保温系统材料；封面2019-09-12发布，2020-03-01实施',
  'completeness':'12页全目视：封面、目录中英I/II、前言III、正文打印1-7连续、版权封底；目录最后第5章评价方法位于打印7，5.4以完整句收束；非仅样章。',
  'download_status':'实测可下载完整PDF（正文和表格有大面积水印）','recommendation':'B',
  'recommendation_reason':'版本及全文闭环，但扫描正文/表格含橙色圆形跨栏水印；可读作备用，需继续找同版无遮挡副本。无文字层或书签。',
  'visual_review_pages':list(range(1,13)),
  'clarity':'扫描文字基本清楚；PDF6/7/9大幅橙色圆形水印跨正文表格，影响阅读；抽查未见裁去正文',
  'watermark':'大幅橙色圆形水印覆盖正文与表格，未去除','body_searchable':False,'body_text_layer':'无文本层',
  'standard_year':2019,'issue_date':'2019-09-12','implementation_date':'2020-03-01',
 },
 'R01-G5-004': {'complete_pdf':False,'version_verified':False,'completeness_status':'本次403未获得PDF','download_status':'本次HTTP403访问受限，是否需登录未知','version_match':'2020/2021年份冲突未解决；未获得可读封面，不按URL年份判定'},
}
for r in doc['results']:
    ident=r['candidate_id']
    r.setdefault('complete_pdf',False);r.setdefault('version_verified',False)
    r.setdefault('standard_key',r.get('standard_number'))
    r['transfer_size_matches_header']=(r.get('bytes')==int(r['content_length_header'])) if str(r.get('content_length_header','')).isdigit() and r.get('bytes') is not None else None
    if r.get('pdf_header_valid'):r['pdf_parse']='页面树可遍历；已尝试逐页文本提取。图像/字体/内容流可读性另以渲染与目视记录判断'
    r['bookmark_provenance']='下载文件未见Outline书签' if r.get('bookmark_count')==0 else '下载文件自带Outline；无法仅从结构证明为出版社原生或第三方后加'
    r.setdefault('permission_status','公开GET成功，未提供账号或绕过认证；内容许可未单独授权再分发' if r.get('http_status')==200 else '本次未验证可公开取得全文')
    if ident in updates:
        r.update(updates[ident]);r['visual_checked_at']=NOW
        if r.get('complete_pdf') and ident!='R01-G4-005':r['download_status']='实测可下载完整PDF（已核目录/页码/终页）'
        evidence=list((ROOT/ident).glob('supplement-contact.jpg'))+list((ROOT/ident).glob('footer-continuity-*.jpg'))+list((ROOT/ident).glob('rendered-footers-*.jpg'))+list((ROOT/ident).glob('link-target-evidence.json'))
        r['evidence_paths']=list(dict.fromkeys(r.get('evidence_paths',[])+[str(x) for x in evidence]))
        r.setdefault('audit_history',[]).append({'checked_at':NOW,'method':'接手独立核验：目录、终页、逐页页码接触表、必要全页渲染与内部Link目标；原件未改动','outcome':r['completeness'] if 'completeness' in r else r.get('completeness_status')})
doc['updated_at']=NOW;doc['handoff_state']='接手对话唯一写入，持续审查';doc['explicit_complete_flags']=True
p.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'updated_at':NOW,'count':len(doc['results']),'complete_pdf_count':sum(r['complete_pdf'] for r in doc['results']),'recommendations':{s:sum(r['recommendation']==s for r in doc['results']) for s in ['A','B','C','D']}},ensure_ascii=False))
