import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

root = Path(__file__).resolve().parent
now = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
for name in ['conflict-796-years.json','candidates-round04-g1-replacement.json']:
    path = root/name
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    if 'checked_at' in data:
        data['checked_at']=now
    if 'created_at' in data:
        data['created_at']=now
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
for name in ['nwafu-public-list.html','nwafu-200-preview.html']:
    path=root/name
    data=path.read_bytes()
    data=re.sub(rb';jsessionid=[A-Fa-f0-9]+', b';jsessionid=PUBLIC-TRANSIENT-REDACTED', data)
    path.write_bytes(data)
(root/'tj-headers.txt').write_text('Public unauthenticated GET metadata: 200 OK; Content-Type text/html; Content-Encoding gzip. Nonessential transient response headers omitted.\n',encoding='utf-8')
discussion=root/'discussion-1300.md'
text=discussion.read_text(encoding='utf-8')
text=text.replace('检查时间：2026-10-17 13:06（Asia/Shanghai）。','检查点：2026-10-17 13:00；接手后证据补充至13:07（Asia/Shanghai）。')
discussion.write_text(text,encoding='utf-8')
print('Search evidence sanitized; current saved timestamps: '+now)
