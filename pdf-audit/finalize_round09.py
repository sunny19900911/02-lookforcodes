"""R11: six main candidates plus one independently tested public alternate."""
import collections, datetime, hashlib, json, pathlib
ROOT=pathlib.Path(__file__).resolve().parent
PATH=ROOT/'audit-pending-round09.json'
BASE_SHA='a81a40dfff05c0bd437b99875baba5efc7f540c05ae9c59437aceb66d5aa65e2'
assert hashlib.sha256((ROOT/'audit-results.json').read_bytes()).hexdigest()==BASE_SHA
doc=json.loads(PATH.read_text(encoding='utf-8'));rows={r['candidate_id']:r for r in doc['results']};assert len(rows)==7
base=json.loads((ROOT/'audit-results.json').read_text(encoding='utf-8'))
NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
verdicts={
 'R11-1555-2024-FAIUSR':dict(
  complete_pdf=False,version_verified=True,recommendation='D',body_reading_recommendation='B（仅已收录正文浏览范围）',
  version_class='标称正式编号浏览版（未附条文说明）',draft_stage='未见草案阶段标识，不据此证明出版终稿一致',implementation_date='2024-05-01',
  version_verified_scope='仅核对文件标称编号与题名；不证明出版终稿一致或2026现行性',
  version_match='封面标T/CECS1555-2024碳中和建筑评价标准，水印为浏览版，PDF2施行2024-05-01；未附版权/ISBN/发布公告，非正式出版终稿一致性证明',
  completeness_status='已证未附英文目录所列条文说明',
  completeness='30页均产图。PDF7-30印1-24连续，八章正文/附录A-C/用词/引用齐；PDF6英文目录明确Addition: Explanation of provisions25，PDF30印24引用标准自然结束后文件终止，无嵌入附件、末页链接或另册提示，实际未附所列条文说明。',
  recommendation_reason='正文浏览质量可B，但本件已证未附目录所列条文说明，按不完整全文口径D；103有效语义书签不能弥补收录不全。',
  body_searchable=True,body_text_layer='数字文字可检索中文；6页共135数学代理字符、5页51私用符号，公式和上下标复制不可靠',
  bookmark_navigation='103真实标签均匹配目标：8章/13节/76条/3附录/用词引用/1公式号，非页图文件名导航',bookmark_semantic_match_count=103,bookmark_semantic_error_count=0,
  clickable_toc='26目录Link中25对/1错：PDF5用词说明跳PDF28附录C，应PDF29用词',semantic_link_match_count=25,semantic_link_error_count=1,
  clarity='正文表格公式图像可辨，灰色浏览版水印横跨内容',watermark='灰色《碳中和建筑评价标准》浏览版水印跨正文/表格/公式',
  quality_anomalies=[{'pdf_pages':[5],'observed':'中文目录说明项为错误！未定义书签。；用词标22实23'},{'pdf_pages':[6,28],'observed':'英文附录C标20实22；说明标25而本件未附'}],
  visual_review_pages=[1,2,5,6,7,28,29,30],
  independent_review='第二审核全30页/目录末项、103Outline及26Link，检查无嵌入附件；root原图复核英文说明25项与终页24，D与正文阅读B分开。',
 ),
 'R11-200-2006-DLSSYHT':dict(
  complete_pdf=False,version_verified=True,recommendation='D',version_class='正式历史版本正文重排摘编（未收录实际条文说明）',draft_stage='历史版本正文重排副本',implementation_date='2006-08-01',
  version_match='封面/扉页匹配CECS200:2006建筑钢结构防火技术规范，实施2006-08-01；重排不是原书全本',
  completeness_status='已证未收录同版本实际条文说明',
  completeness='96页全产图。PDF7-94为十章正文、附录A-I及用词，PDF94重排93自然结束，95-96均网站宣传。约100处浅灰条文说明标签后直接下一条，无解释段落。同版本旧扫描R02-G3-NWAFU-200-2006在PDF126说明标题、127-128印123-124说明目录，129/125有1.0.1-1.0.4实质解释至177/173的10.5.10；新件未收录这些实际说明。结论不由96vs177页数差单独推出。',
  recommendation_reason='已证正文重排摘编未附实际条文说明，另有原图单位漏写；不作为完整全文，D，旧大学C保留不受此新链接覆盖。',
  body_searchable=True,body_text_layer='数字重排，正文可检索；公式/表格多为嵌入图，提取漏数字不一概等于版面缺失；10.4.1缺mm单位为可见转录差异',
  clickable_toc='240Link=49内部目录+191外部URI；内部目标均存在但未全验证正确，已证附录D错PDF65应66、F错72应73',internal_link_count=49,external_uri_link_count=191,semantic_link_error_count_at_least=2,
  clarity='正文外观清楚，页眉网站/页脚二维码和后两页广告；公式图像需核读',watermark='网站页眉/页脚二维码，未见整页大水印',
  quality_anomalies=[{'pdf_pages':[56],'observed':'10.4.1重排为厚度大于100时；旧同版扫描PDF75/印69为100mm时，原图实际缺单位，不自动补改'}],
  comparison={'same_version_candidate':'R02-G3-NWAFU-200-2006','same_version_pdf_pages':[75,126,127,128,129,177],'note':'旧扫描保留C，仅作具体正文/说明对照；两个哈希不同，不按新页数猜缺页'},
  visual_review_pages=[1,2,3,7,56,57,94,95,96],
  independent_review='第二审全文范围核对并与已有同版扫描对读说明和单位；root复核灰色标签/用词末页及网站广告终页，D。',
 ),
 'R11-197-2006-FAIUSR':dict(
  complete_pdf=False,version_verified=True,recommendation='C',version_class='正式历史版扫描副本（2026现行性未核）',draft_stage='历史版本副本（封面核对）',implementation_date='2006-04-01',
  version_match='PDF1编号/题名匹配CECS197:2006孔内深层强夯法技术规程，施行2006-04-01；出版字面与标准年份分开，不推断现行性',
  completeness_status='正文及说明末项已到；印18/20/22空白性质未证明',
  completeness='34页均产图。PDF5-21印1-17连续，附录A为18/14，B为19-20/15-16，用词21/17。PDF22说明扉页对应主目录19无folio，PDF23说明目录印21，PDF24-34印23-33连续；末6.2检测从PDF33/32至34/33续6.2.6自然结束。印18/20/22未收录，无可靠同版旁证证明为空白，不断言已缺技术内容，也不计完整。说明目录未列第2章不构成说明缺章证据。',
  suspected_omitted_printed_pages=[18,20,22],substantive_missing_pages_proven=False,
  recommendation_reason='版本及正文/说明末项明确，扫描可读，但三处背页空白性质尚无可靠证明，维持C；23个印码分组书签不等于章节导航。',
  body_searchable=False,body_text_layer='全件无正文文字层/OCR，不能直接搜索复制',
  bookmark_navigation='23唯一有效目标，4标题标签（封面/两处目录/说明扉页）+19印码或印码区间标签；数字标签起页吻合，为印码分组导航',bookmark_title_label_count=4,bookmark_printed_page_label_count=19,
  clickable_toc='0Link，页面目录不可点击',clarity='正文公式及附表抽查可辨；xref非零索引修正提示不阻止34页解析/渲染，不据此判损坏',watermark='抽查未见遮挡性水印',
  visual_review_pages=[1,3,4,5,7,18,19,20,21,22,23,24,33,34],
  independent_review='第二审按实际版心而非空白footer表核全部页序和23书签，root核说明扉页/目录与末页，支持C。',
 ),
}
for ident,r in rows.items():
 r['reviewed_at']=NOW;r['audit_statement_type']='AI实测判断（含只读独立复核）'
 r['complete_pdf']=False
 if ident in verdicts:
  r.update(verdicts[ident]);r['download_status']='实测可下载PDF；'+r['completeness_status'];r['download_check_status']='已完成GET及版本/收录范围/质量检查'
  r['visual_checked_at']=NOW;r['native_outline_present']=bool(r.get('bookmark_count'));r['publisher_original_bookmarks']=None
  if r.get('bookmark_count'):r['bookmark_provenance']='下载文件已有Outline，审查未添加；出版社原生制作身份未证明'
  folder=ROOT/ident;render=folder/'continuity-render';r['full_render_check']={'rendered_pages':len(list(render.glob('page-*.png'))),'stderr':(render/'render-errors.txt').read_text(encoding='utf-8',errors='replace'),'scope':'全页产图，准确性及清晰度按列明图像核对'};assert r['full_render_check']['rendered_pages']==r['pages']
  r['evidence_paths']=list(dict.fromkeys(r.get('evidence_paths',[])+[str(p) for pat in ['supplement-contact.jpg','continuity-render/render-errors.txt','resolved-navigation-targets.json'] for p in folder.glob(pat)]))
  if ident=='R11-197-2006-FAIUSR':
   r['evidence_paths']=[p for p in r['evidence_paths'] if 'rendered-footers-' not in p];r['excluded_evidence']=[{'path':str(folder/'rendered-footers-001.jpg'),'reason':'固定0.88H裁在实际页码下方而全空；不作为页序证据'}]
  r.setdefault('audit_history',[]).append({'checked_at':NOW,'method':'版本/全文范围/实际页序与导航、原图对照','outcome':r['recommendation_reason']})
 elif ident=='R11-INST-PDF-001':
  old=next(o for o in base['results'] if o['candidate_id']=='R01-G4-009');assert r['sha256']==old['sha256']=='87ddefc91ee9256e07c4074d0dad8639a09e778e63db202de59372c80e25b5f0'
  for key in ['version_verified','version_match','completeness','recommendation_reason','body_searchable','body_text_layer','clarity','searchable','watermark']:
   if key in old:r[key]=old[key]
  r.update(recommendation='D',name=r.get('name') or r.get('standard_name') or old.get('name') or '超声回弹综合法检测混凝土强度技术规程',version_class='正式历史版不完整重排副本',draft_stage='历史版本副本（同哈希复用已核图像）',completeness_status='同哈希已证目录列说明但本件未附',download_status='实测可下载与旧缺说明本完全相同的PDF，非完整全文',download_check_status='新URL已GET/字节哈希核验，复用同一内容既有完整性审查',native_outline_present=False,publisher_original_bookmarks=None)
  r['content_identity_review']={'same_content_as':['R01-G4-009','R01-G4-009-ALT'],'sha256':r['sha256'],'method':'新URL445094B实际GET后SHA256与既有两件完全相同，复用同内容审查，未仅按42页推断','reused_evidence_paths':old.get('evidence_paths',[])}
  r.setdefault('audit_history',[]).append({'checked_at':NOW,'method':'新URL完整GET与同哈希内容身份核对','outcome':'版本封面/目录PDF4列说明；42页止用词41后无实际说明，沿用D；保留该厂家明确父页来源'})
 else:
  r.update(recommendation='D',version_verified=False)
  if ident=='R11-31-2017-APEXTRAY':r.update(download_status='本次返回HTML验证页面，未取得PDF',error='NonPDFResponse: HTML verification challenge, no PDF signature',recommendation_reason='普通GET返回HTML验证页；未操作/绕过验证，不以web64页观察当本次已得PDF')
  elif r.get('http_status')==403:r.update(download_status='本次HTTP403访问受限，是否需登录未知',recommendation_reason='普通GET本次403未得PDF，不推断永久失效或登录要求')
  else:r.update(download_status='本次TLS证书主机名不匹配，未取得PDF',recommendation_reason='公开独立备链默认TLS主机名验证失败，未关闭验证；不操作原站验证，不推断永久失效')
 if ident=='R11-INST-PDF-001':source=ROOT.parent/'search/round11-public-sources/instrument-pages/round11-instrument-pages.json'
 else:source=ROOT.parent/'search/round11-public-sources/candidates-r11-root.json'
 r['search_input_path']=str(source.relative_to(ROOT.parent)).replace('\\','/');r['search_input_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
 if ident=='R11-31-2017-GUANGYUXC':r['search_input_relation']='根候选31的alternative_urls[0]，另建链接候选实测，原验证页失败保留'
doc.update(updated_at=NOW,status='ready_for_next_checkpoint_not_canonical',audited_link_candidate_count=7,source_main_candidate_count=6,additional_public_alternate_tested=1,ordinary_get_attempt_count=7,replacement_count=0,formal_complete_pdf_added=0,complete_draft_added=0,rating_counts=dict(collections.Counter(r['recommendation'] for r in rows.values())),canonical_base={'path':'audit-results.json','count':48,'sha256':BASE_SHA},predecessor_pending=['audit-pending-round07-freeze-1430.json','audit-pending-round08-fixed-r10.json'])
assert doc['rating_counts']=={'D':6,'C':1};assert not any(r.get('complete_pdf') or r.get('draft_content_complete') for r in rows.values())
PATH.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8')
assert hashlib.sha256((ROOT/'audit-results.json').read_bytes()).hexdigest()==BASE_SHA
print(json.dumps({'at':NOW,'records':7,'main_source_candidates':6,'extra_alternate':1,'ratings':doc['rating_counts'],'new_complete':0,'canonical_unchanged':True},ensure_ascii=False))
