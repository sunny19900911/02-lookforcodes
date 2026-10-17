import datetime,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
path=ROOT/'audit-pending-round04.json';doc=json.loads(path.read_text(encoding='utf-8'));NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
r=next(x for x in doc['results'] if x['candidate_id']=='R03-G1-22-2024-ZGB-202603')
r.update(
 complete_pdf=True,version_verified=True,standard_key='T/CECS 22-2024',standard_year=2024,publication_edition='2025年3月第1版/第1次印刷',publication_year=2025,implementation_date='2025-04-01',
 version_match='封面、扉页、版权及第2185号公告匹配T/CECS22-2024岩土锚杆技术规程；2025-03出版与2024标准年份分别保存',
 completeness_status='正文/附录/条文说明、全页码与实际空白页闭环',
 completeness='152页全部Poppler渲染成功，无渲染错误。PDF17-151按打印1-135位置顺序完整保留，打印96/98/100/102真实空白页在文件内；PDF113说明扉页97，115修订说明99，117说明目录101，119说明首章2（打印103），PDF149-151说明附录F打印133-135、图2跨页衔接且F.0.10自然收束，PDF152空白尾页。主目录十一章、附录A-F、用词、引用及说明齐全。版权1/32开4.75印张与152页相符仅作辅助，不单独判完整。',
 download_status='实测可下载完整PDF（清楚扫描/OCR，57章节书签）',
 recommendation='B',recommendation_reason='版本与全文完整性闭环，扫描正文表图清楚且57章节书签可定位；ABBYY OCR有错字/数值识别问题，原图另有重复条号疑点，不评A或宣称出版社原生书签最优。',
 clarity='扫描文字、公式、表格与波形图清楚，抽查无裁去正文或遮挡水印；封底在PDF2，正文顺序正常',
 watermark='抽查未见遮挡性水印',body_searchable=True,
 body_text_layer='ABBYY FineReader OCR；普通中文可检索，但封面铀/锚、版权9b/95及数字/单位/标点有误，公式复制需对照原图',
 searchable='有OCR可搜索复制普通中文，但识别并非准确原文，短语空格/数字/公式须核图',
 bookmark_navigation='57章节/节/附录/前后置书签目标均有效；50标题标准化后在目标文字匹配，其余7整页目视确认，真实章节导航',
 bookmark_provenance='下载文件自带57个章节Outline，ABBYY加工生成痕迹；出版社原生制作身份未证，审查未自行添加',
 native_outline_present=True,publisher_original_bookmarks=None,
 clickable_toc='0个Link注释，页面目录不可点击；Outline章节导航可用，二者分开',
 visual_review_pages=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,35,40,63,69,74,86,90,98,104,106,109,110,113,114,115,116,117,118,119,148,149,150,151,152],
 visual_checked_at=NOW,
 quality_anomalies=[{'pdf_pages':[149,151],'printed_pages':[133,135],'observed':'原图两处均标F.0.8，末页随后F.0.10；可能为同条号分处说明或排版疑点，未查出版社勘误，不自动改F.0.9、不据此判缺页','statement_type':'原文事实（文件图像所示）及待核解释'}],
 independent_review='第二审独立复算129个预期页脚OCR可直接匹配，打印53图像可见，说明扉页/真实空白页全部对应；57书签50文本+7目视复核。独立支持B并发现重复条号疑点，已双审目视确认。',
 source_page_gap='source_page目前为PDF直链，所属独立详情页未定位；公开第三方托管，转载授权未核',
 comparison={'same_standard_key':'T/CECS 22-2024','other_candidate_id':'R01-G1-001','preference':'本候选实得完整可读152页及章节导航，旧2025/12路径返回HTML；当前已审中优先此链，不代表全网最优','different_versions_not_compared':'CECS22:2005另保历史版本，不以新旧版页数作质量优劣判断'},
 merge_action='append_new_candidate_after_1320_freeze'
)
r['evidence_paths']=list(dict.fromkeys(r.get('evidence_paths',[])+[str(p) for pattern in ['supplement-contact.jpg','rendered-footers-*.jpg','bookmark-title-evidence.json'] for p in (ROOT/r['candidate_id']).glob(pattern)]))
r.setdefault('audit_history',[]).append({'checked_at':NOW,'method':'双审独立全文边界/目录/全部页脚、全页渲染、57书签目标、OCR与原图、版权辅助验证','outcome':r['recommendation_reason']})
doc['updated_at']=NOW;doc['status']='ready_for_next_checkpoint_not_canonical';doc['replacement_count']=1;doc['new_get_count']=2
path.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'at':NOW,'pending_count':len(doc['results']),'new_complete_pdf':r['candidate_id'],'canonical_unchanged':True},ensure_ascii=False))
