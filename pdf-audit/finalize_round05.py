"""Finalize only round05 pending; never write the canonical frozen audit."""
import collections
import datetime
import hashlib
import json
import pathlib

from pypdf import PdfReader

ROOT = pathlib.Path(__file__).resolve().parent
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
PATH = ROOT / 'audit-pending-round05.json'
CANONICAL = ROOT / 'audit-results.json'
EXPECTED = '84e4361fbbcdee054efb3ac89e5610001df33e049db3271ba2f2fd1616686629'
assert hashlib.sha256(CANONICAL.read_bytes()).hexdigest() == EXPECTED
doc = json.loads(PATH.read_text(encoding='utf-8'))
rows = {x['candidate_id']: x for x in doc['results']}
assert len(rows) == 7

formal = rows['R07-G4-10025-2019-DLSSYHT']
formal.update(
    complete_pdf=True, version_verified=True, version_class='正式发布版（2026现行性未核）',
    draft_stage='正式发布版（封面核对）',
    release_date='2019-09-12', implementation_date='2020-03-01',
    version_match='封面与页眉为T/CECS 10025-2019，名称绿色建材评价 预制构件；发布日期及实施日清楚，不由此推断2026现行状态',
    completeness_status='按本件目录与全页目视闭环',
    completeness='10页全部目视：封面、中文目录I、英文目录II、前言III，PDF5-9为连续正文印刷1-5；五章、表1续表、附录A.1-A.6和表A.1均在，末页版权/封底。目录末项附录A起4，PDF9印刷5自然收束，未见缺漏。',
    download_status='实测可下载完整PDF（扫描，无文本层；橙色大水印备用件）',
    download_check_status='已完成GET与全文边界核验',
    recommendation='B', recommendation_reason='版本与目录末项、正文及附录闭环，扫描正文仍可读；PDF5橙色大水印覆盖正文，不具备文字检索和章节导航，作为较低质量备用件。',
    body_searchable=False, body_text_layer='全部10页无文本层，扫描图像，不能直接搜索复制正文',
    searchable='无文本层，不能直接搜索复制',
    watermark='PDF5正文有橙色大幅圆形水印，覆盖引用标准和术语；底下文字抽查仍可辨认',
    clarity='全10页目视文字、表格、公式及末页可辨；扫描略倾斜，PDF5有遮挡水印',
    native_outline_present=False, publisher_original_bookmarks=None,
    visual_review_pages=list(range(1, 11)),
    comparison='当前已审此版本仅此可解析副本；不称全网最优，建议保留水印限制',
)

draft = rows['R07-G5-DRAFT-ZERO-2025']
draft.update(
    complete_pdf=False, draft_content_complete=True, version_verified=True,
    version_class='报批稿', draft_stage='报批稿',
    version_verified_scope='只证明文件封面匹配报批稿身份；不证明正式批准、标准编号或2026现行性',
    version_match='封面明确“报批稿”，T/CECS ××××-2025、出版社及施行日期仍为占位，不能登记为正式发布标准',
    completeness_status='完整报批稿，非正式标准全文',
    completeness='完整报批稿，非正式标准全文。84页页首/页序连续1-84；目录十章至PDF23，用词说明24、引用标准25、条文说明扉页26、制定说明27、说明目录28，说明十章至PDF80-84，末条10.2.10跨83-84自然结束；目录未列附录。全84页Poppler产图且日志为空，双审核对全文边界，未见内容缺页。',
    formal_complete_set_exclusion='占位编号报批稿单列，不计正式完整PDF链接、版本和哈希集合',
    download_status='实测可下载完整报批稿PDF（非正式标准全文）',
    download_check_status='已完成GET与草案全文边界核验',
    recommendation='B', recommendation_scope='草案阅读质量；不代表正式标准推荐',
    recommendation_reason='报批稿全文内容闭环、数字文字清楚，章节导航基本可用；1书签和至少4处英文目录错链，存在原稿文字问题，限草案研究参考。',
    body_searchable=True, body_text_layer='WPS数字文字导出，84页均有正文文字，非OCR扫描；普通中文可搜索复制，公式上下标和次序需对照图像',
    searchable='可搜索复制普通正文；公式复制有次序和上下标问题',
    clarity='抽查封面、目录、公式、表格和末章清楚，未见遮挡性水印或明显裁切；全84页完成基础渲染',
    watermark='抽查未见遮挡性水印',
    bookmark_navigation='74个为章节导航，目标均在页范围内；73个标题与目标正文匹配，“引用标准名录”错跳PDF24用词说明，应为PDF25',
    bookmark_semantic_match_count=73, bookmark_semantic_error_count=1,
    native_outline_present=True, publisher_original_bookmarks=None,
    bookmark_provenance='下载文件已自带74章节Outline，审查未添加；出版社原生制作身份未证明',
    clickable_toc='102个Link含标题区/页码区重复注释；英文目录PDF5至少4处错链：9.1→20应21、10.1→20应23、引用标准→24应25、条文说明→24应26',
    visual_review_pages=[1,4,5,11,24,25,26,27,28,35,36,43,80,82,83,84],
    independent_review='第二审独立核对84页编号与全页渲染、目录/说明末项、74书签及102Link；支持完整报批稿单列，发现导航及原稿文字问题，root重点图像复核。',
    quality_anomalies=[
        {'pdf_pages':[25], 'observed':'原稿可见“本条准”“近对”文字，非单纯提取错误', 'statement_type':'原文事实（图像）'},
        {'pdf_pages':[27], 'observed':'编制原则编号为（1）、（1）、（3），不静默纠正', 'statement_type':'原文事实（图像）'},
    ],
)

water41 = rows['R07-WATER-MEP-41-2004']
water41.update(
    complete_pdf=False, version_verified=True, version_class='正式历史版（2026现行性未核）',
    draft_stage='正式历史版（封面核对）',
    version_match='封面/扉页CECS 41:2004与建筑给水硬聚氯乙烯管管道工程技术规程匹配；不证明现行状态',
    completeness_status='正文/附录/说明末项已到，疑似装帧空白页未证明',
    completeness='47页均可渲染且日志为空。目录八章、附录A、用词说明、条文说明可定位；PDF7-32正文印刷1-26连续，PDF33说明扉页对应目录27，PDF34说明目录印29，PDF35说明正文印31后至PDF47印43连续并自然结束（7.2.1续文）。印刷28/30未收录，形态疑似空白装帧页但无同版可靠证据，不称已证明正文缺失，也暂不计完整。',
    download_status='实测可下载PDF；全文完整性仍有印刷28/30疑点',
    download_check_status='已完成GET及正文/说明边界核验；完整性待外证',
    recommendation='C', recommendation_reason='正文、附录及说明末项均可读，但说明扉页附近28/30页未收录且尚无可靠空白页证明；OCR错误较多，复制不能代替原图。',
    body_searchable=True, body_text_layer='TH-OCR扫描文字层，普通中文可部分检索；断行、字词、温度/数字/公式识别错误明显',
    searchable='有OCR可检索，但复制数值/符号需逐项核图',
    clarity='抽查正文、表格和末页扫描可读，略有噪点；未见遮挡性水印或裁去正文',
    watermark='抽查未见遮挡性水印',
    native_outline_present=False, publisher_original_bookmarks=None,
    suspected_omitted_printed_pages=[28,30], substantive_missing_pages_proven=False,
    visual_review_pages=[1,2,3,4,5,6,7,8,9,10,31,32,33,34,35,43,44,45,46,47],
)

water164 = rows['R07-WATER-MEP-164-2004']
water164.update(
    complete_pdf=False, version_verified=True, version_class='正式历史版（2026现行性未核）',
    draft_stage='正式历史版（封面/正文扉页核对）',
    version_match='封面及正文扉页为CECS 164:2004“埋地聚乙烯排水管管道工程技术规程”；说明扉页PDF44印为“工程设计规程”，保留原件内名称差异，不静默改写',
    completeness_status='正文/附录/说明末项已到，疑似装帧空白页未证明',
    completeness='73页均产图，Poppler另有hint-table及字体替换提示。目录十一章、附录A-D、用词说明及说明已定位；PDF7-43对应印刷1-37连续（末用词说明37），PDF44说明扉页对应目录39，PDF45/46说明目录印41/42，PDF47起说明正文43至PDF73印69第11章自然结束。印刷38/40未收录，可能为空白装帧页，未获同版可靠证明；不称已证明技术内容缺失，也暂不计完整。',
    download_status='实测可下载PDF；全文完整性仍有印刷38/40疑点',
    download_check_status='已完成GET及正文/说明边界核验；完整性待外证',
    recommendation='C', recommendation_reason='正文、四附录及末章说明可读，38/40印刷页未收录且空白性质尚未证明；另有原稿说明扉页名称差异、OCR错误及页边下载站水印。',
    body_searchable=True, body_text_layer='扫描OCR文字层，中文可部分检索但字词/空格/数字/符号不可靠；不能称高质量数字原生正文',
    searchable='有OCR可检索，复制正文及公式需核对扫描图',
    clarity='抽查扫描正文、表格及末页可读；PDF37横置表格需旋转阅读，metadata旋转0；页边有freebz.net水印。字体替换提示不等于已证实正文缺字，抽查图像另记。',
    watermark='页顶/页底freebz.net下载站水印，抽查主要在页边未遮正文',
    native_outline_present=False, publisher_original_bookmarks=None,
    suspected_omitted_printed_pages=[38,40], substantive_missing_pages_proven=False,
    visual_review_pages=[1,2,3,4,5,6,7,8,9,10,37,42,43,44,45,46,47,69,70,71,72,73],
    quality_anomalies=[{'pdf_pages':[2,44], 'observed':'正文扉页“技术规程”与条文说明扉页“设计规程”名称不一致，图像可见，非OCR推断', 'statement_type':'原文事实（文件图像）'}],
)

for r in doc['results']:
    r['reviewed_at'] = NOW
    if r['candidate_id'].startswith('R07-WATER-MEP-'):
        r['search_input_path'] = 'search/round07-broad-attachments/water-mep/candidates-round07-water-mep-share-v2.json'
        r['search_input_sha256'] = '89e6f9ba3544c40986ad790f602a3b7d457db039d90a6eacc132f9aa2333dbcd'
        r['search_input_note'] = 'v2仅收窄其他历史HEAD失败表述，本件ID与稳定下载URL不变；本次GET事实独立保存'
    if r.get('pages'):
        r['visual_checked_at'] = NOW
        r['evidence_paths'] = list(dict.fromkeys(r.get('evidence_paths', []) + [str(p) for pattern in ['supplement-contact.jpg','rendered-footers-*.jpg','continuity-render/render-errors.txt'] for p in (ROOT/r['candidate_id']).glob(pattern)]))
        r.setdefault('audit_history', []).append({'checked_at':NOW, 'method':'版本/目录与终页/页序/全文渲染、OCR与图像及导航检查', 'outcome':r['recommendation_reason']})

# Preserve machine-replayable navigation target data separately from the prose review.
reader = PdfReader(draft['local_path'])
outlines = []
def walk(items, depth=0):
    for x in items:
        if isinstance(x, list):
            walk(x, depth+1)
        else:
            outlines.append({'title':str(x.title), 'depth':depth, 'target_pdf_page':reader.get_destination_page_number(x)+1})
walk(reader.outline)
nav = {'candidate_id':draft['candidate_id'], 'checked_at':NOW, 'bookmarks':outlines,
       'semantic_checked_count':74, 'semantic_match_count':73,
       'wrong_bookmark':{'title':'引用标准名录','target_pdf_page':24,'expected_pdf_page':25},
       'english_toc_pdf_page':5, 'known_wrong_links':[
           {'title':'9.1 Prerequisite items','target_pdf_page':20,'expected_pdf_page':21},
           {'title':'10.1 Bonus requirements','target_pdf_page':20,'expected_pdf_page':23},
           {'title':'List of quoted standards','target_pdf_page':24,'expected_pdf_page':25},
           {'title':'Addition: Explanation of provisions','target_pdf_page':24,'expected_pdf_page':26},
       ], 'note':'Link注释数量含标题/页码重复点击区域，不能视为独立目录条目数；独立复核记录与root目视复核共同支持'}
nav_path = ROOT/draft['candidate_id']/'draft-navigation-evidence.json'
nav_path.write_text(json.dumps(nav,ensure_ascii=False,indent=2),encoding='utf-8')
draft['evidence_paths'].append(str(nav_path))

doc.update(updated_at=NOW,status='ready_for_next_checkpoint_not_canonical',new_get_count=7,replacement_count=0,
           formal_complete_pdf_added=1,complete_draft_added=1,
           rating_counts=dict(collections.Counter(x['recommendation'] for x in doc['results'])),
           canonical_base={'path':'audit-results.json','count':33,'sha256':EXPECTED},
           counting_note='正式完整新增10025-2019一链/一版本/一哈希；零碳报批稿完整内容单列，complete_pdf=false，不计正式集合。B评级包含1正式+1草案阅读质量。')
PATH.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8')
assert hashlib.sha256(CANONICAL.read_bytes()).hexdigest() == EXPECTED
print(json.dumps({'pending_count':7,'formal_complete_added':1,'complete_draft_added':1,'ratings':doc['rating_counts'],'canonical_unchanged':True,'at':NOW},ensure_ascii=False))
