import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

root=Path(__file__).resolve().parent
errors=[]
json_files=[]
for path in root.rglob('*.json'):
    if 'master-authority' in path.parts:
        continue
    try:
        json.loads(path.read_text(encoding='utf-8-sig'))
        json_files.append(str(path.relative_to(root)))
    except Exception as exc:
        errors.append({'path':str(path.relative_to(root)),'error':str(exc)})
candidate_files=sorted(root.glob('candidates-*.json'))+[root/'g2-public-routes/round01-candidates.json',root/'g2-public-routes/extension-preview-routes.json',root/'baseline-external-routes/candidates-round01.json']
candidate_files.extend(sorted((root/'g2-public-routes').glob('round02-candidates.json')))
by_id={}
id_sources=defaultdict(list)
for path in candidate_files:
    if not path.exists():
        continue
    payload=json.loads(path.read_text(encoding='utf-8-sig'))
    for item in payload.get('candidates',[]):
        key=item['candidate_id']
        by_id[key]={**by_id.get(key,{}),**item}
        id_sources[key].append(str(path.relative_to(root)))
audit_path=root.parent/'pdf-audit/audit-results.json'
audit=json.loads(audit_path.read_text(encoding='utf-8-sig'))
complete=[x for x in audit.get('results',[]) if x.get('complete_pdf') is True and x.get('version_verified') is True]
state={'checked_at':datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'),'producer':'search','validated_json_count':len(json_files),'json_errors':errors,'candidate_file_count':len([p for p in candidate_files if p.exists()]),'unique_search_candidate_id_count':len(by_id),'supplemented_existing_ids':{k:v for k,v in id_sources.items() if len(v)>1},'audit_canonical_snapshot':{'result_count':len(audit.get('results',[])),'complete_version_verified_link_count':len(complete),'unique_complete_sha256_count':len({x.get('sha256') for x in complete if x.get('sha256')})},'limits':['候选不等于全文；HTTP首字节探测不算独立完整性核验','目录池650编号年份不是逐项全文检索覆盖','当前完整数来自冻结canonical；后续审查增量另存，不能据此假定没有新增','原81条只读，未宣称穷尽全网']}
(root/'search-state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(state,ensure_ascii=False,indent=2))
if errors:
    raise SystemExit(1)
