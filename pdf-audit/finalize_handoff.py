import json,pathlib,datetime
base=pathlib.Path(__file__).resolve().parent
p=base/'audit-results.json';d=json.loads(p.read_text(encoding='utf-8'))
stamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
notes={
'AUD-PUBLIC-001':dict(version_match='封面目视匹配 T/CECS 896-2021 玻璃栈道工程技术规程',clarity='已目视PDF1/5/7/51/98/100：扫描文字与表格清晰；封面轻微扫描纹理，右下淡水印不遮主要正文',searchable='正文为扫描图像，无可搜索复制中文文本层；末页43字仅网页导航，不可误当OCR正文',clickable_toc='PDF目录抽查页7未见Link；全文件唯一Link在末页网页导航，目录不具备点击导航',completeness='可下载，完整性待核：已看到封面、目录第1页、正文及条文说明附录B打印页89、封底；尚须看目录末项及PDF99打印页90并核对连续页码',visual_review_pages=[1,5,7,51,98,100],watermark='右下可见淡水印，不遮主要正文'),
'AUD-PUBLIC-002':dict(version_match='封面目视匹配 T/CECS 1140-2022 景区人行悬索桥工程技术规程',clarity='已目视PDF1/5/7/97/190/192：扫描清楚，正文表述可读；纸边/轻微扫描倾斜，不见显著水印遮挡',searchable='无文本层，不能直接搜索复制',clickable_toc='没有Link注释，目录不可点击',completeness='可下载，完整性待核：已看到封面、发布公告、正文第12章、条文说明附录C及最后E.4静定性荷载试验（打印页178）；尚须核对目录末项/正文图表页及页码连续性',visual_review_pages=[1,5,7,97,190,192],watermark='抽查未见遮挡性水印'),
'AUD-PUBLIC-003':dict(version_match='封面目视匹配 T/CECS 935-2021 公共机构建筑空调系统节能改造技术规程',clarity='已目视PDF1/5/7/31/59/61：文字矢量清晰，无扫描噪点；抽查正文可读',searchable='有中文文本层：61页均可抽取，22939个汉字；仍须逐句对照一次验证复制准确性',clickable_toc='有76个Link注释，目录页5可见目录；须接手者核对Link目标与目录行，不能仅凭Link数称可点击目录',completeness='可下载，完整性待核：目录列正文/用词/引用标准/条文说明，文件末页打印页55为第8章条文说明和公式(1)，尚须确认不是被截断，避免误荐',visual_review_pages=[1,5,7,31,59,61],watermark='抽查未见水印'),
'AUD-PUBLIC-004':dict(version_match='封面目视匹配 T/CECS G:K50-30-2018 公路机制砂高性能混凝土技术规程；封面实施日期2019-04-01',clarity='已目视PDF1/5/7/24/44/46：封面、目录、正文公式清晰；PDF44/46为空白尾页，需要检查PDF43正文终页',searchable='有字体文字对象但中文复制严重乱码：全文抽取124964字符仅6汉字，不能标为可搜索复制中文',clickable_toc='无Link注释，目录不可点击',completeness='可下载，完整性待核：目录第1页列1至7章；PDF44-46为空白尾页，尚须核对目录第2页和PDF43是否为目录末项完整结尾',visual_review_pages=[1,5,7,24,44,46],watermark='抽查未见水印'),
'R01-G1-001':dict(download_status='HTML伪PDF或非PDF响应',completeness='非PDF，未获得正文',version_match='不可核验',clarity='无PDF图像可核验',recommendation='D',recommendation_reason='实际GET为84,455字节HTML；URL以.pdf结尾及搜索摘录不构成PDF证据'),
'R01-G1-002':dict(download_status='仅封面/扉页/版权页，不是完整PDF',version_match='3页目视匹配 CECS 22:2005 岩土锚杆(索)技术规程',completeness='不完整：仅封面、扉页、版权页3页，没有前言、目录、正文和附录；版权页印有3.5印张/86千字，与3页响应不相符',clarity='3页扫描文字清楚；仅供辨别版本',searchable='无文本层，不能搜索复制',clickable_toc='没有目录及Link注释',visual_review_pages=[1,2,3],recommendation='D',recommendation_reason='实测3页全部为封面版权信息，不能进入完整PDF清单')
}
for r in d['results']:
    if r['candidate_id'] in notes:
        r.update(notes[r['candidate_id']]);r['visual_checked_at']=stamp
        if r['candidate_id'].startswith('AUD-PUBLIC'):
            r['recommendation']='C';r['recommendation_reason']='实际GET与版本/抽样阅读通过，但目录末项与终页完整性尚未闭环，不进入已核验完整PDF清单'
    r['audit_history']=[{'checked_at':r['checked_at'],'method':'Actual GET + PDF header + strict pypdf all-pages parse + metadata/text/outline/Link scan + six-page Poppler render','outcome':r['download_status']},{'checked_at':stamp,'method':'交接前目视接触表抽查/保守结论','outcome':r.get('completeness','本次网络失败，未获得PDF')}]
d['updated_at']=stamp;d['handoff_state']='已停写，可由接手审查对话独占后续更新'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print('Saved',len(d['results']),'audit records')
