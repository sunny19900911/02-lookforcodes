from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,re

base=Path(r'C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017')
search=base/'search'; folder=search/'round08-public-expansion'
now=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
old_manifests=['freeze-inputs-1320.json','freeze-inputs-round04.json','freeze-inputs-1330.json','freeze-inputs-1340.json','freeze-inputs-1340-water-mep-addendum.json','freeze-inputs-1340-water-mep-addendum-v2.json','freeze-inputs-g2-round02-share-1350.json']
checks=[]
for name in old_manifests:
    m=read(search/name)
    bad=[x['path'] for x in m['files'] if sha(base/x['path']).lower()!=x['sha256'].lower()]
    checks.append({'manifest':'search/'+name,'file_count':len(m['files']),'unchanged':not bad,'failures':bad})
assert all(c['unchanged'] for c in checks),checks
root_candidates=read(folder/'candidates-r08-association.json')['candidates']
water_path=folder/'water-historical/round08-water-historical-candidates.json'
assert sha(water_path)=='223658d0a58498a9515d0bfdac01ef726a49da071bf518ba2a95c03cce027b22'
water=read(water_path)['candidates']
assert len(root_candidates)==5 and len(water)==3
assert len({r['candidate_id'] for r in root_candidates+water})==8
directory_path=folder/'directory2/directory-round08.json'
assert sha(directory_path)=='e3bac1d3877707fc32c17c8b15b6d882333272c8f635ba402f0a04eb52786c81'
d=read(directory_path); records=d['records']
assert len(records)==165
assert all(isinstance(r['pdf_page_one_based'],int) and 1<=r['pdf_page_one_based']<=186 and r['source_id'] and r['raw_cells'] for r in records)
assert len({r['source_id'] for r in records})==165
assert len({(r['number'],r['year']) for r in records})==156
visual=read(folder/'directory2/conflict-visual-check-r08.json')
assert visual['conclusion']['visual_conflict_confirmed'] is True
v=read(folder/'directory2/validation-summary.json')
raw_obs=folder/'public-page-observations-r08.json'; observations=read(raw_obs)
for o in observations['observations']:
    if 'relevant_links' in o:
        o['relevant_links']=[r for r in o['relevant_links'] if 'CECS' in r['text'].upper()]
observations['share_projection']={'recorded_at':now,'raw_metadata_sha256':sha(raw_obs),'note':'仅保留CECS实际附件href及访问观察；非CECS链接略，不含HTML/PDF/瞬时参数。原始结构化观察本地保留。'}
obs_share=folder/'public-page-observations-r08-share.json'
assert not obs_share.exists()
obs_share.write_text(json.dumps(observations,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audit=base/'pdf-audit/audit-results-freeze-1350.json'
assert sha(audit)=='400cf857fd7d1a084bb44cb4f0b387cda220f679e88370784296314f96386d33'
state={
    'source_id':'SEARCH-R08-CHECKPOINT-1400-20261017','recorded_at':now,
    'new_pdf_candidates':8,'historical_formal_pdf_candidates':6,'draft_pdf_candidates':2,
    'non_pdf_word_draft_routes':2,
    'new_directory_source_records':165,'unique_number_years_in_new_directory_source_records':156,
    'number_years_not_in_round07':152,'not_in_round07_boundary':'不是主库净新增数，由catalog对全主库去重决定。',
    'all_directory_rows_have_actual_pdf_physical_page':True,'directory_internal_conflict_groups':2,
    'conflict_visual_check':'原PDF物理53/62/165页目视确认，不是提取丢位；只确认目录可见冲突，不猜正式编号。',
    'unresolved_year_or_number_rows':15,'nonstandard_code_explanations':2,
    'audit_latest_canonical_freeze':{'path':'pdf-audit/audit-results-freeze-1350.json','sha256':sha(audit),'frozen_at':'2026-10-17T14:00:03+08:00','results':40,'formal_complete_links':10,'formal_complete_versions':8,'formal_complete_hashes':8,'complete_approval_drafts_separate':1},
    'r08_complete_pdf_added_by_search':0,
    'previous_freeze_integrity':checks,
    'boundary':'R08新候选尚待独立审查。目录/Word不计PDF；现行性/转载授权未核；无Git、账号登录或原PDF上传。'
}
sp=folder/'state-r08.json';assert not sp.exists()
sp.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
discussion='''# 14:00 检索检查点

source_id: SEARCH-DISCUSSION-1400-20261017；记录时间：%s（北京时间）。

原文事实（本轮来源与结构化观察）：R08新增8条PDF候选，6个历史正式版候选（212:2006、235:2008、333:2012、122:2001、17:2000、287:2011）及2个草案PDF（工业建筑非工业化改造送审稿、绿色住区占位征求意见稿）。协会公开资料页普通匿名GET成功，实际href给出前3历史及送审稿；其移动/桌面页HTTP/HTTPS地址按同一路径归一，不重复计候选。绿色住区本次TLS握手失败，仍只作公开索引候选。公元/永高3个历史附件普通GET均为200/PDF，具体附件父页未知，已明确，不用首页冒充。另2份Word征求稿仅格式路线，不计PDF候选。

原文事实（新疆目录）：186页逐页文本扫描，43个CECS命中页做表格提取；新增165来源记录、156个编号年份，其中152个编号年份未在R07列示，但不是主库净新增数。全部记录附实际PDF物理页、source_id、原始单元格；15条年份/编号不全保留缺口，2条代号释义不作标准。原目录处于修订版征求意见阶段，不据此把其中每条已编号标准也当成草案，不以目录历史状态确认2026现行性。

原文事实（目录视觉核对）：1137-2022在物理53页对应BIM设计应用、物理62页对应模块应急传染病医院；22-2012在物理165页对应两个供水/热水名称。局部图像确认格内数字完整，未见裁切丢位。只确认目录内部可见内容冲突，正式编号/名称须再核公告或封面，不静默选择或“修正”为猜测编号。

原文事实（审查角色冻结）：主控已批准R07回灌，14:00:03审查40条冻结SHA400cf857fd7d1a084bb44cb4f0b387cda220f679e88370784296314f96386d33，正式完整10条链接/8版本/8哈希，完整报批稿另1。10025正式完整B但大橙水印，备用；零碳报批B不混正式；41/164 C不因疑似空白装帧页就称正文缺失。R08尚未计入审查完整数。

我的观点（方法）：政府目录可扩编号范围，但目录自身有可见错误，必须保留原格与冲突；实际协会附件页能一轮带出多版本，效果优于反复追相同403。web读取超时与普通GET成功并存，应如实记录工具观察差异；不因此绕过认证或TLS校验。10025/10032清洁替代本前两批查询无新公开PDF，零结果已登记。

共享仅取本批manifest列出的结构化文件。无原PDF、页面PNG、HTML原始响应、瞬时下载参数值；旧manifest全部哈希未变。主控独自操作GitHub，检索侧不声称本轮已发布。
'''%now
dp=search/'discussion-1400.md';assert not dp.exists();dp.write_text(discussion,encoding='utf-8')
rels=[
 'round08-public-expansion/candidates-r08-association.json',
 'round08-public-expansion/query-ledger-r08-root.json',
 'round08-public-expansion/public-page-observations-r08-share.json',
 'round08-public-expansion/quality-feedback-r08-audit-1350.json',
 'round08-public-expansion/water-historical/round08-water-historical-candidates.json',
 'round08-public-expansion/directory2/directory-round08.json',
 'round08-public-expansion/directory2/directory-conflicts.json',
 'round08-public-expansion/directory2/raw-cells.json',
 'round08-public-expansion/directory2/validation-summary.json',
 'round08-public-expansion/directory2/front-matter-evidence.json',
 'round08-public-expansion/directory2/conflict-visual-check-r08.json',
 'round08-public-expansion/state-r08.json','discussion-1400.md'
]
for rel in rels:
    p=search/rel
    assert p.is_file(),rel
    if p.suffix=='.json':read(p)
    assert not re.search(r'(?i)[?&](?:uhash|access_token|token|signature|secret|password)=',p.read_text(encoding='utf-8-sig')),rel
mf=search/'freeze-inputs-1400.json';assert not mf.exists()
manifest={'producer':'search','checkpoint':'14:00','checked_at':now,'frozen':True,
 'input_file_count':len(rels),'previous_freeze_integrity':checks,
 'note':'固定后不修改。仅结构化分享元数据/来源/缺口，无PDF/PNG/HTML/瞬时下载参数值。原始结构化观察及脚本不列同步。目录不当全文，R08候选未升级完整。',
 'files':[{'path':'search/'+rel,'sha256':sha(search/rel),'bytes':(search/rel).stat().st_size} for rel in rels]}
mf.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'manifest':str(mf),'sha256':sha(mf),'files':len(rels),'candidate_count':8,'directory_source_records':165,'old_freezes_unchanged':True},ensure_ascii=False))
