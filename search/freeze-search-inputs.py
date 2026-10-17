import hashlib
import json
from datetime import datetime,timedelta,timezone
from pathlib import Path

root=Path(__file__).resolve().parent
relative=[
 'candidates-round01.json','candidates-round02.json','candidates-round03-tj-links.json',
 'candidates-round04-g1-replacement.json','candidates-round05-nwafu.json','candidates-round06-g1-22-alternative.json',
 'g2-public-routes/round01-candidates.json','g2-public-routes/extension-preview-routes.json','g2-public-routes/round02-candidates.json',
 'baseline-external-routes/candidates-round01.json','baseline-external-routes/directory-round02.json',
 'baseline-external-routes/query-log-round01.json','baseline-external-routes/followup-661-links.json',
 'g1-round03-coverage.json','query-ledger-r02.json','quality-feedback-r03.json','conflict-796-years.json',
 'discussion-1320.md','search-state.json'
]
records=[]
for name in relative:
    path=root/name
    payload=path.read_bytes()
    if path.suffix=='.json':
        json.loads(payload.decode('utf-8-sig'))
    records.append({'path':'search/'+name,'sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload)})
out={'checked_at':datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'),'producer':'search','checkpoint':'13:20','frozen':True,'input_file_count':len(records),'note':'这些输入从本清单生成后保持不变；后续新查询另建下一轮文件，不改本批。此清单不含PDF、图片、HTML、瞬时响应头或凭据。相同candidate_id补充字段按ID合并，不重复计数。','files':records}
(root/'freeze-inputs-1320.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'manifest':str(root/'freeze-inputs-1320.json'),'input_file_count':len(records),'checked_at':out['checked_at']},ensure_ascii=False))
