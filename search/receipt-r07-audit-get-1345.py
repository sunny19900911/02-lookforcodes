from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib,json

base=Path(r'C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017')
source=base/'pdf-audit/audit-pending-round05.json'
raw=source.read_bytes()
data=json.loads(raw.decode('utf-8-sig'))
ids={'R07-G4-10025-2019-DLSSYHT','R07-G5-727-2020-YSJIANZHAN','R07-G5-DRAFT-ZERO-2025','R07-WATER-MEP-41-2004','R07-WATER-MEP-164-2004','R07-WATER-MEP-1012-2022','R07-WATER-MEP-828-2021'}
results=[]
for r in data['results']:
    if r['candidate_id'] not in ids: continue
    results.append({k:r.get(k) for k in ['candidate_id','standard_number','checked_at','requested_url','final_url','http_status','download_status','pages','bytes','sha256','bookmark_count','link_annotation_count','complete_pdf','version_verified','recommendation','recommendation_reason']})
assert len(results)==7
out={
    'source_id':'SEARCH-RECEIPT-R07-AUDIT-GET-1345-20261017',
    'statement_type':'原文事实（审查角色反馈及其pending文件读取回执；检索侧未重复GET/目视）',
    'recorded_at':datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'),
    'source_path':'pdf-audit/audit-pending-round05.json',
    'source_file_sha256_at_read':hashlib.sha256(raw).hexdigest(),
    'source_mutability':'审查pending仍在完善；此哈希仅锁定读取时刻，不称其已冻结。',
    'results_at_read':results,
    'message_received_observations':{
        'actual_get_parseable_pdfs':4,
        'http_403_candidates':['R07-G5-727-2020-YSJIANZHAN','R07-WATER-MEP-1012-2022','R07-WATER-MEP-828-2021'],
        '10025_watermark':'审查角色报告大橙水印，目视完整性仍在核验。',
        'zero_carbon_draft':'审查角色明确为84页报批稿，单列草案，不混正式。',
        'boundary':'本次403不证明永久失效，也不推断一定要登录；不绕过。4可解析不等于4完整。'
    },
    'canonical_unchanged_reported':'审查1330 canonical33条/SHA84e4361fbbcdee054efb3ac89e5610001df33e049db3271ba2f2fd1616686629未动。',
    'next_method':'后续针对403另找正常公开独立托管源；不反复同URL试图绕过。10025寻找清晰替代，草案单列版本。',
    'sharing_boundary':'仅回执及结构化状态；不含本地PDF、页面PNG或瞬时下载脚本。'
}
p=base/'search/receipt-r07-audit-get-1345.json'
assert not p.exists()
p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'results':len(results)},ensure_ascii=False))
