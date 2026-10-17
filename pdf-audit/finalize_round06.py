"""Record R08 review in its own pending file; keep the 40-row canonical frozen."""
import collections
import datetime
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
PATH = ROOT/'audit-pending-round06.json'
CANONICAL_SHA = '400cf857fd7d1a084bb44cb4f0b387cda220f679e88370784296314f96386d33'
assert hashlib.sha256((ROOT/'audit-results.json').read_bytes()).hexdigest() == CANONICAL_SHA
doc = json.loads(PATH.read_text(encoding='utf-8'))
rows = {r['candidate_id']:r for r in doc['results']}
assert len(rows) == 8
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')

v = {
 'R08-CNASS-212-2006':dict(
    complete_pdf=True,version_verified=True,recommendation='B',implementation_date='2006-12-01',publication_edition='2006年12月第一版/第一次印刷',
    version_class='正式历史版（2026现行性未核）',draft_stage='正式历史版（封面/扉页/版权核对）',
    version_match='封面、扉页及版权对应CECS212:2006预应力钢结构技术规程；仅确认历史版本身份',
    completeness_status='正文/附录/说明及实际空白页闭环',
    completeness='117物理页全部产图。PDF8-80对应印1-73连续；PDF81真实空白对应74，PDF82说明扉页75，PDF83真实空白对应76；PDF84-115对应印77-108连续。八章正文、附录A/B（PDF78/79印71/72）、用词73齐；说明目录PDF85末8.4监测108，PDF115实际8.4.1自然结束。PDF116征订信息、117封底。版权1/32开3.5印张与PDF4-115的112页相符仅作辅助。',
    recommendation_reason='历史版本、全页序和目录/说明终页闭环，正文公式和节点图扫描清楚；正文无OCR，无书签/点击目录，保留页边水印和渲染字体提示，评B。',
    body_searchable=False,body_text_layer='58页只能提取乱码水印、CJK=0；扫描正文没有可用OCR，不能按text_pages=58称正文可检索',
    searchable='正文不可直接搜索复制；少量水印文字不代表正文文本层',
    clarity='公式、表格、节点图及末页抽查清楚；偶数页下缘淡bzfxw.com水印未见遮挡正文',
    watermark='偶数页下缘淡bzfxw.com水印，抽查不挡正文',
    visual_review_pages=[1,2,3,8,16,17,30,59,78,79,80,81,82,83,84,85,115,116,117],
    independent_review='第二审独立核117张图/全部页脚位置并抽查公式节点图，原footer表局部裁边另在原PNG放大核实，支持B。',
 ),
 'R08-CNASS-235-2008':dict(
    complete_pdf=True,version_verified=True,recommendation='B',implementation_date='2008-07-01',publication_edition='2008年6月第一版',
    version_class='正式历史版（2026现行性未核）',draft_stage='正式历史版（封面/扉页/公告/版权核对）',
    version_match='封面、PDF2右标题、PDF3右第18号公告均CECS235:2008铸钢节点应用技术规程；公告2008-04-15，出版与标准年分别记录',
    completeness_status='双页扫描的正文/附录/说明与实际空白位置闭环',
    completeness='43个物理双页扫描。PDF6右正文1，PDF7-25左右对应2-39；PDF26左实际空白40/右说明标题41，PDF27左实际空白42/右说明目录43，PDF28左目录44/右说明正文45，PDF29-43左右连续对应46-75。八章、附录A、用词39、说明41齐；说明目录末附录A75，PDF43右75该说明三条自然结束（左74为表2）。空白40/42真实在文件内。',
    recommendation_reason='版本、正文/说明全部页序与末项双审闭环；双页扫描略斜、书脊黑边及噪点，部分横表需转向，正文无OCR/书签/Link，适合作为阅读备份。',
    body_searchable=False,body_text_layer='仅6页提取少量非中文文字，CJK=0；扫描正文无可用OCR',
    searchable='正文不可直接搜索复制',clarity='双页扫描稍倾斜、书脊黑边和噪点明显，正文/公式/小字抽查可辨；未见遮正文水印',
    watermark='抽查未见明显覆盖正文水印',
    visual_review_pages=[1,2,3,4,5,6,7,22,25,26,27,28,29,30,38,39,40,41,42,43],
    independent_review='root与第二审分别核双页映射、实际空白位置和末页75；元数据创建时间早于实物年份不能取代封面公告版权证据，支持B。',
 ),
 'R08-CNASS-333-2012':dict(
    complete_pdf=False,version_verified=True,recommendation='C',implementation_date='2013-03-01',publication_edition='2013年2月第一版',
    version_class='正式历史版（2026现行性未核）',draft_stage='正式历史版（封面/公告/版权核对）',
    version_match='封面、版权及PDF3协会第128号公告匹配CECS333:2012结构健康监测系统设计标准；公告2012-12-10，2013出版/实施不改标准年份',
    completeness_status='正文与说明末项已到，印36/38/40空白性质未证明',
    completeness='80页均产图。PDF10-44为印1-35连续（7章、附录A/B、用词）；PDF45说明扉页对应目录37，PDF46说明目录印39，PDF47-79说明正文印41-73连续，末附录A的A.4.3自然结束；PDF80索购告知。印36/38/40未收录，可能为装帧空白但无可靠同版旁证，不认定已完整或已缺技术正文。',
    recommendation_reason='版本匹配、扫描可读，但印36/38/40未收录且空白性质待证明；另有19目录Link中12错跳，OCR公式复制不可靠，维持C。',
    suspected_omitted_printed_pages=[36,38,40],substantive_missing_pages_proven=False,
    body_searchable=True,body_text_layer='ABBYY OCR，普通中文可检索；PDF78/印72谐振频率公式图像可见但文本不完整，公式/希腊符号复制不可靠',
    searchable='可检索普通中文，数值/公式/希腊符号需核扫描图',clarity='抽查扫描清楚，未见明显遮挡水印',watermark='抽查未见明显水印',
    clickable_toc='19个Link目标均存在，仅7个语义匹配/12错跳：PDF7的4个匹配；PDF46的15个仅3匹配，例“3传感器的选择和布置43”跳PDF15/印6，应PDF49/印43',
    semantic_link_match_count=7,semantic_link_error_count=12,
    visual_review_pages=[1,2,3,7,10,43,44,45,46,47,49,76,78,79,80],
    independent_review='第二审独立核全部页序、说明末项及19Link坐标/标题，确认7对12错；root登记原始目标列表，不将存在的目标等同正确导航。',
 ),
 'R08-CNASS-DRAFT-INDUSTRIAL-CONVERSION':dict(
    complete_pdf=False,draft_content_complete=True,version_verified=True,recommendation='B',
    standard_number='T/CECS XXX-20XX',standard_key='T/CECS XXX-20XX（工业建筑非工业化改造结构检测鉴定标准送审稿）',
    version_class='送审稿',draft_stage='送审稿',draft_date='2022-09',number=None,year=None,
    version_verified_scope='仅核对文件送审稿身份；不指正式批准、正式编号或现行性',
    version_match='PDF1明确送审稿、2022年9月、T/CECS XXX-20XX；完整草案单列，不与正式编号合并',
    completeness_status='完整送审稿，非正式标准全文',
    completeness='完整送审稿，非正式标准全文。63页全产图。七章PDF9-26、附录A-G在27-46、用词47、引用48、说明49-63齐；正文PDF9-49印1-41，PDF50较小纸张为未印42的制定说明，随后PDF51-63印43-55连续，末附录D说明D.0.10自然结束，未见下载造成技术缺页。',
    recommendation_reason='送审稿内容闭环，中文正文清楚可检索，56书签及56目录Link真实有效；公式提取有代理字符，原稿条号/引用/表值疑点保留，仅评草案阅读B。',
    recommendation_scope='草案阅读质量；不代表正式标准推荐',formal_complete_set_exclusion='complete_pdf=false；完整送审稿单列，不计正式完整集合',
    body_searchable=True,body_text_layer='数字文字正文可检索；11页数学符号提取共126个代理字符，公式/上下标不能依赖复制',
    searchable='普通中文可搜索复制；公式和下标需核图',clarity='正文、表格及末页清楚，抽查未见明显水印',watermark='抽查未见明显水印',
    bookmark_navigation='56个真实章节书签，标题去空白后全部匹配目标页文字',bookmark_semantic_match_count=56,bookmark_semantic_error_count=0,
    clickable_toc='PDF5中文目录/7英文目录各28Link，按目录序列全与正确章节目标对应；共56Link',semantic_link_match_count=56,semantic_link_error_count=0,
    quality_anomalies=[{'pdf_pages':[33],'observed':'同页D.0.5直接接D.0.8，属于原稿条号跳号，不能指控下载缺页'},{'pdf_pages':[43],'observed':'F.0.1/F.0.2援引G表而实际表题为F表；表F.0.2-2中可视原稿印75/125，不自动更正或称提取漏小数点'}],
    visual_review_pages=[1,5,7,9,26,27,32,33,43,46,47,48,49,50,51,61,62,63],
    independent_review='第二审核63页、七章/七附录及说明末项，56书签标题与56目录链接全部对应；原稿内部问题与PDF下载完整性分别记录。',
 ),
 'R08-WH-001':dict(
    complete_pdf=True,version_verified=True,recommendation='B',implementation_date='2001-05-01',
    version_class='正式历史版数字重排副本（2026现行性未核）',draft_stage='历史版本副本（封面核对）',
    version_match='封面/扉页CECS122:2001埋地硬聚氯乙烯排水管道工程技术规程匹配，施行2001-05-01；不是出版社原页式验证',
    completeness_status='按本件目录的正文/九附录/用词末项闭环',
    completeness='54页均产图。PDF6-33正文印1-28；附录A为34/29，B为35-37/30-32，C为38-40/33-35，D为41-42/36-37，E为43-44/38-39，F为45-49/40-44，G为50/45，H为51/46，I为52-53/47-48，PDF54用词说明49与目录末项吻合。无物理位置缺口；目录未列且本件无条文说明，不把用词说明充作条文说明，不额外宣称出版社原页式完整。',
    recommendation_reason='按本件目录/正文/九附录和终页闭合、技术内容抽查可读，沿用历史数字重排本B口径；页脚部分字形裁切、字体替换及复制漏数字限制均保留。',
    body_searchable=True,body_text_layer='建标浏览器2003/PDFWriter数字重排导出，非可靠OCR扫描；中文可提取，条号/英文/数值/公式大量漏提，图像相关数值抽查仍可见',
    searchable='中文可部分检索，条号/数值/公式复制不准确，需核图',
    clarity='技术正文/公式/表格抽查可读；奇数印页右页脚末位数字确有局部裁切，不能写全印码完整可读；部分A3媒体框与A4混排',
    watermark='抽查未见遮挡性水印',
    quality_anomalies=[{'pdf_pages':[8,14,54],'observed':'奇数印页右页脚末位数字局部字形裁切，原图300dpi复核存在；正文/公式/附表抽查未见同类技术内容裁切'}],
    visual_review_pages=[1,2,3,5,6,8,14,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54],
    independent_review='第二审核54页及九附录边界，放大发现页脚实际裁切并据原图/位置核序；按现有数字重排本范围建议B，未把未列说明当缺页。',
 ),
 'R08-WH-002':dict(
    complete_pdf=True,version_verified=True,recommendation='B',implementation_date='2000-12-01',
    version_class='正式历史版数字重排副本（2026现行性未核）',draft_stage='历史版本副本（封面核对）',
    version_match='封面/扉页CECS17:2000埋地硬聚氯乙烯给水管道工程技术规程匹配，施行2000-12-01；不是出版社原页式验证',
    completeness_status='按本件目录的正文/五附录/用词末项闭环',
    completeness='64页均产图，渲染日志为空。PDF7-48正文印1-42，附录A为49-56/43-50，B为57/51，C为58-59/52-53，D为60-62/54-56，E为63/57，PDF64用词说明58，与目录末项吻合。印1-58清楚连续，无缺号或空白疑点。目录未列且本件无条文说明，不将用词说明充作条文说明，不额外宣称出版社原页式完整。',
    recommendation_reason='按本件目录/正文/五附录和终页闭合、技术内容可读，沿用历史数字重排本B口径；中文能检索但复制条号/数字/公式漏失，无书签或点击目录。',
    body_searchable=True,body_text_layer='数字重排/打印导出，非可靠OCR扫描；中文可提取，条号/英文/数值/公式大量漏提，图像数值抽查仍在',
    searchable='中文可部分检索，数值/条号/公式复制需核图',clarity='正文/公式/表格抽查可读；存在CropBox设置但抽查技术内容在可见范围内',watermark='抽查未见遮挡性水印',
    visual_review_pages=[1,2,4,6,7,48,49,56,57,58,59,60,61,62,63,64],
    independent_review='第二审独立核64页/印1-58连续与附录边界，正文表格可读，按数字重排本范围支持B。',
 ),
 'R08-WH-003':dict(
    complete_pdf=False,version_verified=True,recommendation='C',implementation_date='2011-07-01',
    version_class='正式编号排版文件（出版状态待核）',draft_stage='正式编号文件，内含占位编号；稿型待核',is_draft=None,
    version_verified_scope='仅封面/正文扉页编号名称匹配；正式出版内容身份尚未闭合',
    version_match='封面/正文扉页CECS287:2011漩流降噪特殊单立管排水系统技术规程，PDF60说明扉页仍为CECS XXX:201X；未证明正式出版排版或明确稿型，不仅凭占位号把整件定草案',
    completeness_status='内容边界可到达；目录与页码不一致、正式出版内容身份待核',
    completeness='73页均产图，PDF7-73内容顺序与逻辑位置1-67连续；PDF20有前后衔接正文但本页未印14，不能称全印码可见。六章、附录A-D、用词、引用和说明六章可达，PDF73工程验收自然结束。主目录引用标准标54/说明55，实际引用PDF59印53、说明扉页PDF60印54；说明目录末工程验收标68，实际末页印67。存在源内目录与实际页码不一致，不能仅据相差1判实际缺页；另说明扉页占位编号、正式出版内容身份未闭合，不计正式完整。',
    recommendation_reason='数字排版正文可读且末章可达，但内含CECS XXX:201X占位号、目录与页码差异，正式出版内容身份未闭合，暂C；不武断定技术缺页或草案。',
    body_searchable=True,body_text_layer='Microsoft Word2010数字文字导出，普通中文可搜索；公式次序/符号复制须核图，不称OCR扫描',
    searchable='可检索普通中文，公式及符号复制需核图',clarity='数字正文、管件图/尺寸表及末页抽查清楚；Poppler有Symbol字体提示',watermark='抽查未见遮挡性水印',
    clickable_toc='仅英文目录PDF6有9个内部Link，4对/5错：1→7、2→8、3.1→11、3.3→13对应正确页（3.3落点偏低）；错3→9应11、3.2→13应11、3.4→13应14、6.1→23应29、6.2→23应30',
    semantic_link_match_count=4,semantic_link_error_count=5,
    substantive_missing_pages_proven=False,
    visual_review_pages=[1,2,5,6,7,20,37,59,60,61,62,63,64,65,70,71,72,73],
    independent_review='第二审独立支持C：逻辑页位连续，PDF20原稿未印14；9目录链接4对5错已核，标称正式编号的Word排版电子稿与出版终稿一致性待核。',
    quality_anomalies=[{'pdf_pages':[1,2,60],'observed':'封面/扉页为CECS287:2011，说明扉页CECS XXX:201X，图像明确；稿型待核'},{'pdf_pages':[5,59,60,61,73],'observed':'目录标号与实际页脚部分差1，不能由差1直接指控缺一页'}],
 ),
}

for ident,r in rows.items():
    if ident in v:
        r.update(v[ident])
        r['name'] = r.get('name') or r.get('standard_name')
        r['reviewed_at'] = NOW
        r['visual_checked_at'] = NOW
        r['download_check_status'] = '已完成GET及版本/内容/阅读质量核验，限制见独立字段'
        r['full_text_review_status'] = r['completeness_status']
        r['candidate_only'] = False
        r['download_status'] = ('实测可下载完整PDF（按本件目录及所述范围核验）' if r.get('complete_pdf') else ('实测可下载完整送审稿PDF（非正式标准全文）' if r.get('draft_content_complete') else '实测可下载PDF；完整性或正式出版身份尚未闭合'))
        r['native_outline_present'] = bool(r.get('bookmark_count'))
        r['publisher_original_bookmarks'] = None
        if r.get('bookmark_count'):
            r['bookmark_provenance'] = '下载文件自带Outline，审查未添加；出版社原生制作身份未证明'
        folder = ROOT/ident
        render = folder/'continuity-render'
        r['full_render_check'] = {'rendered_pages':len(list(render.glob('page-*.png'))),'stderr':(render/'render-errors.txt').read_text(encoding='utf-8',errors='replace'),'scope':'产图证明基础渲染，正文清晰度限记录抽查范围'}
        assert r['full_render_check']['rendered_pages'] == r['pages']
        r['evidence_paths'] = list(dict.fromkeys(r.get('evidence_paths',[])+[str(p) for pattern in ['supplement-contact.jpg','rendered-footers-*.jpg','continuity-render/render-errors.txt','resolved-link-targets.json'] for p in folder.glob(pattern)]))
        r.setdefault('audit_history',[]).append({'checked_at':NOW,'method':'独立PDF版本/目录终页/页序/全页产图与文字/导航检查','outcome':r['recommendation_reason']})
    else:
        r.update(recommendation='D',recommendation_reason='本次普通GET TLS握手失败，未取得PDF，不推断永久失效、登录要求或稿型已核',complete_pdf=False,version_verified=False,reviewed_at=NOW)
    r['audit_statement_type'] = 'AI实测判断（GET/解析/图像核对及独立复核）'
    r['discovery_observations_scope'] = '候选文件的access/metadata_evidence/来源路线保留检索时事实；本轮实测以download_status及reviewed_at后审查字段为准'

doc.update(updated_at=NOW,status='ready_for_next_checkpoint_not_canonical',new_get_count=8,replacement_count=0,
           canonical_base={'path':'audit-results.json','count':40,'sha256':CANONICAL_SHA},
           formal_complete_pdf_added=4,complete_draft_added=1,
           rating_counts=dict(collections.Counter(r['recommendation'] for r in rows.values())),
           counting_note='本轮正式完整4件；完整送审稿1单列。B包含4历史正式副本及1草案阅读质量。1TLS失败不推断永久失效。')
assert doc['rating_counts'] == {'B':5,'C':2,'D':1}
assert sum(r.get('complete_pdf') is True for r in rows.values()) == 4
assert sum(r.get('draft_content_complete') is True for r in rows.values()) == 1
PATH.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8')
assert hashlib.sha256((ROOT/'audit-results.json').read_bytes()).hexdigest() == CANONICAL_SHA
print(json.dumps({'pending_count':8,'ratings':doc['rating_counts'],'formal_complete_added':4,'complete_draft_added':1,'canonical_unchanged':True,'updated_at':NOW},ensure_ascii=False))
