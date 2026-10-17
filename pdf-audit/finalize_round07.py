"""Finalize six R09 candidates separately from the frozen 48-row canonical."""
import collections, datetime, hashlib, json, pathlib
ROOT=pathlib.Path(__file__).resolve().parent
PATH=ROOT/'audit-pending-round07.json'
BASE_SHA='a81a40dfff05c0bd437b99875baba5efc7f540c05ae9c59437aceb66d5aa65e2'
assert hashlib.sha256((ROOT/'audit-results.json').read_bytes()).hexdigest()==BASE_SHA
doc=json.loads(PATH.read_text(encoding='utf-8'));rows={r['candidate_id']:r for r in doc['results']};assert len(rows)==6
NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
verdicts={
 'R09-CNASS-DRAFT-CABLE-ACCEPT':dict(
  version_class='征求意见稿',draft_stage='征求意见稿',draft_content_complete=True,complete_pdf=False,version_verified=True,recommendation='B',
  standard_number='T/CECS XXX-202X',number=None,year=None,
  version_match='PDF1明确建筑索结构工程施工质量验收标准（征求意见稿）；PDF2施行日期占位，不认定送审或正式版',
  completeness='完整征求意见稿，非正式标准全文。41页全渲染、日志空；PDF6-41对应印1-36连续，七章、附录A-H齐，PDF41/36附录H表H.0.1及签署栏完整。条文说明红字穿插正文，目录未声称独立说明册，不据此判缺说明。',
  recommendation_reason='征求意见稿内容与末表闭合、数字文字清楚；38语义书签正确但31目录Link首项错跳，保留原稿交叉引用问题，仅评草案阅读B。',
  bookmark_navigation='38真实导航全部标题/目标匹配：7前置标签+31正文/附录/表格标签（含附录E分行）',bookmark_semantic_match_count=38,bookmark_semantic_error_count=0,
  clickable_toc='PDF4中文目录31个Link中30按行匹配；1总则错指PDF5英文目录底部，应PDF6正文；附录E两行链接同指PDF36',semantic_link_match_count=30,semantic_link_error_count=1,
  body_text_layer='数字文字，41页可提取中文14038汉字；普通中文/数字基本可复制，表格换行及符号需核图',
  quality_anomalies=[{'pdf_pages':[31],'observed':'原稿写附录F中表G.0.1-G.0.3，交叉引用疑点'},{'pdf_pages':[40],'observed':'原表引用6.4.6-6.4.8而该节正文止于6.4.5，不能据此认下载缺页'}],
  visual_review_pages=[1,2,4,5,6,31,36,40,41],
  independent_review='第二审核全41页/目录末表/38书签及31Link坐标，支持内容完整征求意见稿B，原稿引用问题不当下载缺页。',
 ),
 'R09-DRAFT-DRAIN-MANHOLE-GRATING':dict(
  version_class='报批稿',draft_stage='报批稿',draft_revision='复审V3.0，终稿（仍在报批范围）',draft_content_complete=True,complete_pdf=False,version_verified=True,recommendation='B',number=None,year=None,
  standard_number='T/CECS xxx-202X',standard_number_literals={'cover_pdf1':'T/CECS XXX-2020','title_pdf2':'T/CECS xxx-202X','notes_pdf31':'T/CECS XXX-202X'},
  version_match='封面明确报批稿、复审V3.0终稿；封面字面2020但正文扉页/说明为202X及占位施行日，分字段保留，不能认正式2020版',
  completeness='完整报批稿，非正式标准全文。41页全渲染、日志空；PDF7-41印1-35连续，七章正文、附录A/B、用词、引用及说明均齐。说明目录PDF32末6.2主控项目35，PDF41/35的6.2.4段落自然结束，未见技术缺页。',
  recommendation_reason='报批稿内容闭合、图文清楚，26书签语义正确；29Link中26内部目录有1错跳，另3为前言单位外部链接，保留编号字面差异，仅评草案B。',
  bookmark_navigation='26真实章节书签全部标题及目标匹配',bookmark_semantic_match_count=26,bookmark_semantic_error_count=0,
  clickable_toc='29Link=26内部目录+3前言单位外部URI；内部25正确，PDF32说明目录4设计选型错跳PDF37产品性能，应PDF38',internal_link_count=26,external_uri_link_count=3,semantic_link_match_count=25,semantic_link_error_count=1,
  body_text_layer='数字文字，普通中文/尺寸/温度/公差抽查可复制，未见代理字符；表格合并单元格复制次序需核图',
  quality_anomalies=[{'pdf_pages':[1,2,31],'observed':'封面占位号含2020，内扉页/说明含202X；稿型明确报批，年份不猜'},{'pdf_pages':[5,6,11],'observed':'原稿目录3.2名称与正文不一致，保留来源差异'}],
  visual_review_pages=[1,2,5,6,7,11,31,32,37,38,41],
  independent_review='第二审核41页、说明末项及26书签/29Link，支持完整报批稿单列B，外部URI未作为章节导航。',
 ),
 'R09-DRAFT-WOOD-FIRE-COATINGS':dict(
  version_class='报批稿',draft_stage='报批稿',draft_revision='复审V3.0，终稿（仍在报批范围）',draft_content_complete=True,complete_pdf=False,version_verified=True,recommendation='B',number=None,year=None,
  version_match='封面明确报批稿（复审V3.0，终稿），T/CECS XXX-202X、出版社及施行日期占位；不以WPS元数据2021作为标准年份',
  completeness='完整报批稿，非正式标准全文。36页全渲染、日志空；PDF7-36印1-30连续，七章正文至PDF21，附录A为22-23、用词24、引用25、说明扉页26、说明目录27、说明正文28-36。说明目录只列至6/6.1印30，PDF36/30实际6.1.5自然结束。未列说明7，选择性跳6.1.4不构成下载缺页；PDF11为表3.0.4续项6-9并非空白。',
  recommendation_reason='报批稿内容闭合、WPS数字文字清楚；27书签25对2错，但27目录Link正确，原稿字词及上标复制限制保留，仅草案阅读B。',
  bookmark_navigation='27真实章节Outline，25语义匹配；正文5施工错PDF13应14，说明6验收错PDF35应36',bookmark_semantic_match_count=25,bookmark_semantic_error_count=2,
  clickable_toc='27内部目录Link全部正确：PDF5有17个，PDF27有10个；Link与错误Outline须分别登记',semantic_link_match_count=27,semantic_link_error_count=0,
  body_text_layer='WPS数字文字，普通中文/条号/数值可搜索复制；cm³/m²提取线性化cm3/m2，表格次序需核图',
  quality_anomalies=[{'pdf_pages':[21],'observed':'图像原稿暖器片，非OCR错误'},{'pdf_pages':[24],'observed':'图像原稿采“可”，不自动纠正'},{'pdf_pages':[31],'observed':'图像原稿没有和很少量，字词待核'}],
  visual_review_pages=[1,5,7,11,13,14,21,22,23,24,25,26,27,28,31,35,36],
  independent_review='第二审独立核36页/说明目录末项、27Outline与27Link，root核封面及说明目录/终页；支持完整报批稿单列B。',
 ),
 'R09-WM-001':dict(
  complete_pdf=False,version_verified=True,recommendation='C',version_class='正式历史版数字重排副本（技术文字可靠性待核）',draft_stage='标称历史正式版本，非草案认定',implementation_date='2008-10-01',announcement_date='2008-06-13',announcement_number='25',
  version_match='PDF1标题/第25号公告对应CECS243:2008园林绿地灌溉工程技术规程，公告2008-06-13、实施2008-10-01；不据此证明2026现行或重排技术文字准确',
  completeness='21页全产图。PDF2起九章正文，PDF18的9.3.5后为用词说明；PDF19-21有独立条文说明、末8.2.3自然结束。未见独立目录/附录/原版印刷页码。章节边界可达，但PDF17/8.2.3可见版面实测微灌均匀系数不应低于后直接句号，关键限值为空；同页9.2.3第4项规范名称/编号可见乱码，不能当已核准确完整标准。',
  completeness_status='章节边界已到；可见技术限值缺损，准确完整性未闭合',content_boundary_closed=True,technical_content_reliability='原图可见关键限值空缺和规范引用乱码；不补猜原值',
  recommendation_reason='政府托管且版本标称匹配，但重排原图本身缺关键限值并有规范引用乱码；与单纯复制漏数字不同，保持C不计正式完整。',
  body_text_layer='数字重排，中文可提取但逐词断行明显；公式上下标、分数及运算顺序被打散，原图另有真实限值空缺',
  quality_anomalies=[{'pdf_pages':[17],'observed':'8.2.3原图实测微灌均匀系数不应低于后无数值；9.2.3第4项规范引用乱码。双审图像确认，非单纯提取漏字，也非下载缺页证据'}],
  visual_review_pages=[1,2,5,7,11,17,18,19,21],
  independent_review='第二审发现原图技术限值空缺并建议C；root在PDF17原图复核确认，不以政府域名或章节齐全自动升B。',
 ),
}
share=ROOT.parent/'search/round09-new-sources/candidates-r09-root-share.json'
water=ROOT.parent/'search/round09-new-sources/water-mep/round09-water-mep-candidates.json'
for ident,r in rows.items():
 r['reviewed_at']=NOW
 if ident in verdicts:
  r.update(verdicts[ident]);r['name']=r.get('name') or r.get('standard_name');r['visual_checked_at']=NOW;r['body_searchable']=True
  r['clarity']='数字正文/表格/公式抽查清楚，文字准确性及导航限制另列';r['watermark']='抽查未见遮挡性水印';r['searchable']='普通中文可检索；公式/表格次序须核原页'
  r['native_outline_present']=bool(r.get('bookmark_count'));r['publisher_original_bookmarks']=None
  if r.get('bookmark_count'):r['bookmark_provenance']='下载文件自带Outline，审查未添加；出版社原生制作身份未证明'
  if r.get('draft_content_complete'):
   r['standard_key']=r['standard_number']+'（'+r['name']+'；'+r['version_class']+'）'
   r['version_verified_scope']='只核对文件实际草案身份，不代表正式批准/正式标准年份/2026现行性'
   r['formal_complete_set_exclusion']='完整草案单列，complete_pdf=false不表示草案内容不完整'
   r['recommendation_scope']='仅草案阅读质量，非正式标准推荐';r['completeness_status']='完整'+r['version_class']+'，非正式标准全文'
   r['download_status']='实测可下载完整'+r['version_class']+'PDF（非正式标准全文）'
  else:r['download_status']='实测可下载PDF；原图技术文字缺损，准确完整性未闭合'
  r['download_check_status']='已完成GET、版本/内容边界及阅读质量核验';r['candidate_only']=False;r['full_text_review_status']=r['completeness_status']
  folder=ROOT/ident;render=folder/'continuity-render';r['full_render_check']={'rendered_pages':len(list(render.glob('page-*.png'))),'stderr':(render/'render-errors.txt').read_text(encoding='utf-8',errors='replace'),'scope':'全页产图，文字准确/清晰度按记录抽查'};assert r['full_render_check']['rendered_pages']==r['pages']
  r['evidence_paths']=list(dict.fromkeys(r.get('evidence_paths',[])+[str(p) for pat in ['supplement-contact.jpg','rendered-footers-*.jpg','continuity-render/render-errors.txt','resolved-navigation-targets.json'] for p in folder.glob(pat)]))
  r.setdefault('audit_history',[]).append({'checked_at':NOW,'method':'独立版本/完整性/导航语义及原图核对','outcome':r['recommendation_reason']})
 else:
  r.update(complete_pdf=False,version_verified=False,recommendation='D')
  if r.get('http_status')==404:r.update(download_status='本次HTTP404未取得PDF',recommendation_reason='本次精确URL普通GET404，未得本地PDF，不推断永久失效；第85号公告未核图',historical_event_image_verified=False)
  else:r['recommendation_reason']='本次TLS握手超时未取得PDF，未关闭校验，不推断永久失效或稿型已核'
 source=water if ident=='R09-WM-001' else share
 r['search_input_path']=str(source.relative_to(ROOT.parent)).replace('\\','/');r['search_input_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
 r['audit_statement_type']='AI实测判断（含独立只读复核）'
doc.update(updated_at=NOW,status='ready_for_next_checkpoint_not_canonical',audited_candidate_count=6,ordinary_get_attempt_count=7,get_count_note='6候选首轮尝试+243换默认Windows TLS栈额外普通GET1；复用文件解析不计新GET',replacement_count=0,formal_complete_pdf_added=0,complete_draft_added=3,canonical_base={'path':'audit-results.json','count':48,'sha256':BASE_SHA},rating_counts=dict(collections.Counter(r['recommendation'] for r in rows.values())))
assert doc['rating_counts']=={'D':2,'B':3,'C':1};assert not any(r.get('complete_pdf') for r in rows.values());assert sum(r.get('draft_content_complete') is True for r in rows.values())==3
PATH.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8')
assert hashlib.sha256((ROOT/'audit-results.json').read_bytes()).hexdigest()==BASE_SHA
print(json.dumps({'candidates':6,'get_attempts':7,'ratings':doc['rating_counts'],'new_formal_complete':0,'new_complete_drafts':3,'canonical_unchanged':True,'at':NOW},ensure_ascii=False))
