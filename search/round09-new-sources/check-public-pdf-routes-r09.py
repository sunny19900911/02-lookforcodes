from pathlib import Path
from datetime import datetime,timezone,timedelta
import urllib.request,urllib.error,concurrent.futures,json,urllib.parse

targets=[
 'https://www.uibim.com/wp-content/uploads/2025/02/8e20c59990bd0f2.pdf',
 'https://www.ttbz.org.cn/Home/PdfFileStreamGet/c3RuLDE1MTIxNA%28eq%29%28eq%29',
 'https://www.ttbz.org.cn/Home/PdfFileStreamGet/c3QsMTUxMDQ5',
 'https://static1.tianyancha.com/czd_file/standard/30d8c78389ad4736c5f36a3b8365f980.pdf'
]
def one(u):
 out={'requested_url':u,'checked_at':datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'),'method':'ordinary anonymous GET, first64bytes only, not full-PDF audit'}
 try:
  with urllib.request.urlopen(u,timeout=20) as r:
   final=r.geturl()
   out.update(http_status=r.status,final_url=final if not urllib.parse.urlsplit(final).query else None,content_type=r.headers.get('Content-Type'),pdf_prefix=r.read(64).startswith(b'%PDF-'))
   out['observation']='仅签名/响应类型；不证明版本或完整性。'
 except urllib.error.HTTPError as e:out.update(http_status=e.code,error_type='HTTPError',observation='本次访问状态；不推断登录要求或永久失效。')
 except Exception as e:out.update(error_type=type(e).__name__,error_summary=str(e)[:220])
 return out
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(one,targets))
p=Path(r'C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017/search/round09-new-sources/public-route-observations-r09.json')
assert not p.exists()
data={'source_id':'SEARCH-R09-PUBLIC-ROUTE-OBSERVATIONS-20261017','statement_type':'原文事实（匿名GET签名观察，非全文审查）','observations':rows}
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(data,ensure_ascii=False,indent=2))
