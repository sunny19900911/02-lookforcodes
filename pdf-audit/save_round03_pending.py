import copy,datetime,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
path=ROOT/'audit-pending-round03.json';pending=json.loads(path.read_text(encoding='utf-8'));canonical=json.loads((ROOT/'audit-results.json').read_text(encoding='utf-8'));NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
base={r['candidate_id']:r for r in canonical['results']}
data={
'R02-G1-010':{
 'version_verified':True,'version_match':'封面CECS22:2005，岩土锚杆（索）技术规程，2005-08-01施行；未把红色现行标准旧印记作2026现行性证据',
 'complete_pdf':False,'completeness_status':'条文说明扉页后打印60未见，需同版对照','completeness':'总目录列正文1-58、条文说明59；PDF65为说明扉页，PDF66/67目录打印61/62，PDF68正文63，PDF105末打印100、11.3.3与目录末项吻合。打印60可能是空白背页但未旁证；装帧封面/版权页亦不全。全文105页渲染成功，当前不直接判缺正文或完整全书。',
 'bookmark_count':105,'bookmark_valid_target_count':105,'bookmark_navigation':'105个GIF文件名逐页书签，目标依次PDF1-105有效；没有章节标题',
 'bookmark_provenance':'下载文件自带逐页GIF书签，添加者未知；不称出版社原生章节书签','body_searchable':False,'body_text_layer':'105页扫描，无正文可抽取文本','searchable':'无正文文本层','clickable_toc':'无Link注释，纸面目录不可点击',
 'clarity':'扫描黑白文字、表格、曲线可读，少量噪点；封面红色现行标准印记不遮正文；105个逐页书签不能替代章节定位',
 'recommendation':'C','recommendation_reason':'比3页封面预览有全部主要技术章节与条文说明，仍须核60空白页性质/装帧页；不能因105书签升级A',
 'independent_review':'内部只读复核者独立核对书签全部GIF名及正文/说明边界，与审查者结论一致',
},
'G2-20261017-640-ONEHIKER':{
 'version_verified':True,'version_match':'封面/扉页/版权和第515号公告匹配T/CECS640-2019，2020-04-01实施','complete_pdf':False,
 'completeness_status':'技术正文和终页对应，但打印30未见待对照','completeness':'总目录PDF7-10列1-7章、附录A、用词/引用及说明29。PDF38为说明扉页29，PDF39目录31；说明末项附录A63与PDF71打印63对应，PDF72版权信息/PDF73封底。全73页渲染成功。打印30未见，可能省空白页但未证，暂C。',
 'clarity':'扫描正文、表格可视清楚，无遮挡水印；OCR层存在剐匕仓等错字与异常空格，不能当准确可复制正文','body_searchable':False,'body_text_layer':'OCR文本层有中文但明显错字/空格；全文短语搜索不可靠',
 'bookmark_navigation':'50个Outline含章节、节和说明；50目标有效，抽核正文1/3/4/5/6/7、附录及说明各章目标相符',
 'bookmark_provenance':'含关注公众号等推广Outline，属于第三方导航加工痕迹；不能称出版社原生书签','clickable_toc':'未发现Link注释；Outline导航与页面目录链接分开',
 'recommendation':'C','recommendation_reason':'当前有清楚扫描及章节导航，比无导航本更便于定位；OCR不准确且30页性质待核，不宣称最优或完整',
},
'G2-20261017-604-YDD17':{
 'version_verified':False,'version_match':'封面CECS604-2019（缺T/）同时写2017北京，扉页2020-01-01施行；前言编制名单空白。无法确认其为正式出版2019版',
 'version_class':'非出版排版/疑似草稿，待正式版本对照','complete_pdf':False,'completeness_status':'本文件目录技术内容闭合，正式版身份未闭环',
 'completeness':'51页从封面、扉页、前言、目录、正文1-46到引用标准末页；章节夹注条文说明，但不能证明与正式发布版全部内容相同。未把页数短于第三方89页介绍直接当截断证据。',
 'clarity':'扫描/图像正文可读，多处max.book118.com原力文档水印跨正文与图形','watermark':'重复原力文档水印遮挡正文/图形','body_searchable':False,'body_text_layer':'无文本层',
 'recommendation':'C','recommendation_reason':'可下载可读，但年份/编号与编制信息不一致，不能作为正式标准完整全文推荐',
},
'R02-G3-NWAFU-280-2010':{
 'version_verified':True,'version_match':'封面、扉页、版权及发布公告匹配CECS280:2010钢管结构技术规程','complete_pdf':False,
 'completeness_status':'打印90未见，条文说明扉页后缺口性质待核','completeness':'全161页渲染成功。适应扫描内嵌版心后逐页查看页脚，正文打印1-88、条文说明扉页89、目录91/92、说明93-150及版权/封底；打印90未见。说明末章9施工与打印150结尾可对应；未直接把可能省空白页认定缺正文或完整全书。',
 'clarity':'扫描版心居中缩小、留白较大；放大可读，少量扫描噪点，公式表图可视。页边浅站点字不遮正文','body_searchable':False,'body_text_layer':'正文扫描，无正常中文层','bookmark_provenance':'下载文件无Outline','recommendation':'C','recommendation_reason':'版本匹配、主要内容/终页可读；打印90性质待同版证明，无书签/正文复制便利',
},
'R02-G3-NWAFU-200-2006':{
 'version_verified':True,'version_match':'封面、扉页CECS200:2006建筑钢结构防火技术规范，2006-08-01施行，前言2006-06-23','complete_pdf':False,
 'completeness_status':'条文说明前打印120/122未见，需对照','completeness':'177页全渲染成功，正文打印1-119连续，目录列条文说明121，说明目录PDF127打印123、说明末章10于PDF176/177打印172/173结束；打印120/122未见，疑为空白页但无独立旁证。不能据电子页数177认定无缺页。',
 'clarity':'黑白扫描文字、密集表格基本清楚，少量噪点，无显著遮挡水印','body_searchable':False,'body_text_layer':'扫描无正文文本层','bookmark_provenance':'下载文件无Outline','recommendation':'C','recommendation_reason':'版本匹配、技术正文/附录与说明可读；打印120/122性质待对照，导航与文本检索不足',
},
'R02-G3-NWAFU-323-2012':{
 'version_verified':True,'version_match':'封面、扉页、公告匹配CECS323:2012交错桁架钢框架结构技术规程','complete_pdf':False,
 'completeness_status':'已得PDF且全87页渲染成功，内容页码/说明目录待最终闭环','completeness':'封面、前言、总目录及正文第9章、说明第12章末打印78与版权封底可见。87页均成功渲染，但完整页码序列及目录末项仍待人工闭环，维持C。',
 'download_status':'已实测GET可解析PDF；Outline结构异常，全文完整性待核','clarity':'黑白扫描可读，左侧有装订黑边但抽查未遮正文；无文本层','body_searchable':False,'body_text_layer':'无正文文本层',
 'bookmark_navigation':'Outline对象指向Metadata且缺Title，结构坏，不能导航；不能据计数0称没有损坏书签','bookmark_provenance':'下载文件Outline结构异常，未修复原件','recommendation':'C','recommendation_reason':'扫描可读，版本匹配；完整性尚待目录闭环，文件自带Outline损坏不推荐作高质量导航版',
},
'R02-G3-NWAFU-102-2002':{
 'version_verified':True,'version_match':'封面CECS102:2002；2003北京和2003-03-01施行与标准年份2002分存。第三方重排本，不是出版社原版已证事实','complete_pdf':False,
 'completeness_status':'技术正文/附录目录闭合，但不含条文说明且有转录错误','completeness':'83页涵盖九章、附录A-F、用词说明，目录末项83与末页闭合；没有条文说明。不称含说明完整全书，待原出版范围对照。',
 'clarity':'章节导航可用，但真实页面有错标题与单位异常，不能当可靠标准原文','content_errors':[{'pdf_page':2,'observed':'标题写水力控制阀应用设计规程，同时仍保留CECS102:2002与钢结构英文标题'},{'pdf_page':20,'observed':'平均高度单位实际排为4.5～9.0mm，存在单位转录风险'},{'pdf_page':21,'observed':'标题墙架来布置，段落有错接'},{'pdf_page':23,'observed':'变截面写成变戳面，书签同样错字'}],
 'bookmark_navigation':'42个章节/节/附录Outline层级和目标匹配，28个不同目标页；目录42个GoTo链接顺序与书签目标一致','bookmark_provenance':'第三方Word重排PDF自带章节导航，出版社原生未证',
 'clickable_toc':'PDF5有27、PDF6有15个GoTo目录链接，目标与42书签逐项相同','body_searchable':False,'body_text_layer':'普通正文可搜索但有错字；13页图表文本仅页边导航，公式上下标错序，不是全书准确复制','recommendation':'C','recommendation_reason':'仅作历史检索与比对。虽有章节书签/目录Link，但转录错误、图表无文字和无说明，优先找同版可靠扫描本',
 'independent_review':'只读独立复核者实际解析/目视书签、目录和错字/单位页，与主审保守结论一致',
}
}
byid={r['candidate_id']:r for r in pending['results']}
for ident,fields in data.items():
 r=copy.deepcopy(base[ident]);r.update(fields);r['local_reviewed_at']=NOW;r['merge_action']='replace_existing_candidate_after_freeze'
 r['evidence_paths']=list(dict.fromkeys(r.get('evidence_paths',[])+[str(p) for pattern in ['supplement-contact.jpg','rendered-footers-*.jpg','adaptive-footers-*.jpg'] for p in (ROOT/ident).glob(pattern)]))
 r.setdefault('audit_history',[]).append({'checked_at':NOW,'method':'冻结后本地增量：目录/终页、全页渲染、逐页页脚、文本与导航核验，canonical未改','outcome':r['completeness']})
 byid[ident]=r
for r in byid.values():
 if r.get('http_status')==403:r['download_status']='本次HTTP403访问受限，是否需登录未知'
pending['results']=list(byid.values());pending['updated_at']=NOW;pending['canonical_freeze_sha256']='46147ADD21CC3AB5453F683AC816C8763FDDC31A845BAA2908ADF2E902642F1D'
path.write_text(json.dumps(pending,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pending_count':len(pending['results']),'replacements':len(data),'new_candidates':len(pending['results'])-len(data),'at':NOW},ensure_ascii=False))
