import json
from datetime import datetime,timedelta,timezone
from pathlib import Path
root=Path(__file__).resolve().parent
path=root/'conflict-796-years.json'
data=json.loads(path.read_text(encoding='utf-8'))
url='https://ebook.chinabuilding.com.cn/zbooklib/bookpdf/probation?SiteID=1&bookID=140749'
if not any(x['source_url']==url for x in data['evidence']):
    data['evidence'].append({'source_url':url,'source_id':'CABP-796-2020-PREVIEW-20261017','statement_type':'原文事实','claim':'出版方公开试读网页标题和目录标T/CECS796-2020；它是出版方年份证据，不是可用完整PDF证据；与2021公告及2020/2021双馆藏关系仍待澄清'})
data['checked_at']=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print('conflict evidence count:',len(data['evidence']))
