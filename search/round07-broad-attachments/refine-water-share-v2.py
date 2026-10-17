from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,copy

base=Path(r'C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017')
folder=base/'search/round07-broad-attachments/water-mep'
now=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
old=folder/'candidates-round07-water-mep-share.json'
data=json.loads(old.read_text(encoding='utf-8-sig'))
data['share_revision']='v2'
data['share_prepared_at']=now
data['supersedes_share_file']='search/round07-broad-attachments/water-mep/candidates-round07-water-mep-share.json'
for r in data['zero_candidate_or_pending_routes']:
    if r['source_id']=='FIRONE-PUBLIC-DOWNLOAD-262':
        r['transient_parameter_note']='下载地址随正常页面请求生成；本项file_id=112实际GET提示地址已失效。不应把瞬时地址当持久PDF URL。'
    else:
        r['transient_parameter_note']='下载地址随正常页面请求生成；本项仅HEAD返回HTML，本轮未取得可用PDF，未以实际GET证明其已失效。需正常会话复核，不应把瞬时地址当持久PDF URL。'
data['revision_reason']='独立只读复核收窄失败证据：只有file_id=112实测GET过期，其余三项仅HEAD为HTML，不称已失效。4候选URL/身份/数量与v1完全不变。'
out=folder/'candidates-round07-water-mep-share-v2.json'
assert not out.exists()
out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert 'uhash=' not in out.read_text(encoding='utf-8')
previous=json.loads(old.read_text(encoding='utf-8-sig'))
assert [(r['candidate_id'],r['download_url']) for r in previous['candidates']]==[(r['candidate_id'],r['download_url']) for r in data['candidates']]
receipt={
 'source_id':'SEARCH-R07-WATER-SHARE-REVIEW-V2-20261017','recorded_at':now,
 'statement_type':'原文事实（独立只读文件复核及修正回执）',
 'old_frozen_files_unchanged':True,
 'verified':'v1 manifest三文件SHA/字节匹配；四候选原始与download URL未变；分享无瞬时参数实际值、原始响应或PDF；41/164父页归因准确。',
 'problem_found':'v1四项transient_parameter_note均称本轮已失效，证据仅支持112实际GET过期。',
 'v2_fix':'74/111/130收窄为仅HEAD HTML、未证明失效；112保留GET过期。四候选不变。',
 'supersedes_for_catalog_and_publication':'search/round07-broad-attachments/water-mep/candidates-round07-water-mep-share.json',
 'preferred_share_file':'search/round07-broad-attachments/water-mep/candidates-round07-water-mep-share-v2.json',
 'independent_reviewer':'subagent /root/g2_public_routes read-only followup',
 'boundary':'公开下载端点去瞬时参数仅是待修路线，不是验证可用PDF；download_url维持null。未改旧冻结输入。'
}
rp=folder/'share-review-v2.json'
rp.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
paths=[out,folder/'query-ledger-r07-water-mep-share.json',folder/'addendum-r07-water-mep.json',rp]
manifest={'producer':'search','checkpoint':'13:40-water-mep-addendum-v2','checked_at':now,'frozen':True,
 'input_file_count':len(paths),
 'supersedes_share_selection':'search/freeze-inputs-1340-water-mep-addendum.json（保留旧文件不改；出版分享请选v2候选，不选v1候选）',
 'note':'只修失败路线证据强度，不增加候选/全文；仅结构化元数据，无PDF/PNG/HTML/瞬时参数值。',
 'files':[{'path':p.relative_to(base).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in paths]}
mf=base/'search/freeze-inputs-1340-water-mep-addendum-v2.json'
assert not mf.exists()
mf.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'manifest':str(mf),'sha256':sha(mf),'candidate_share_sha256':sha(out),'files':len(paths)},ensure_ascii=False))
