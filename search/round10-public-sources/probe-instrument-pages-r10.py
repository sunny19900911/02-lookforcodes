from pathlib import Path
from datetime import datetime,timezone,timedelta
import urllib.request,urllib.parse,urllib.error,concurrent.futures,re,json,html

targets=['https://bjhcgk.com/html/61.html','https://bjhcgk.com/html/1031.html','https://bjhcgk.com/html/115.html','https://bjhcgk.com/upload/files/20230113/RWLQPGVG-20230113133107.pdf','https://www.cctedu.net/lustersoft_file/source_file/e3145e1f-06b6-4c36-848c-ead86d7d39ff/c1c2a313-c99a-4221-a9e6-4f1b8d884edb/c44430cb-0b80-4111-92a2-c0b6f6f177c8.pdf']
def one(u):
 out={'requested_url':u,'checked_at':datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'),'method':'ordinary anonymous GET; PDF signature prefix only, no full-PDF audit'}
 try:
  with urllib.request.urlopen(u,timeout=20) as r:
   out.update(http_status=r.status,final_url=r.geturl(),content_type=r.headers.get('Content-Type'));prefix=r.read(64);out['pdf_prefix']=prefix.startswith(b'%PDF-')
   if not out['pdf_prefix']:
    t=(prefix+r.read(1500000)).decode('utf-8',errors='replace');rows=[]
    for chunk in re.findall(r'<(?:li|tr)\b[^>]*>[\s\S]*?</(?:li|tr)>',t,re.I):
     label=html.unescape(re.sub(r'<[^>]+>',' ',chunk));label=re.sub(r'\s+',' ',label).strip()
     if 'CECS' not in label.upper():continue
     urls=[]
     for m in re.finditer(r'(?:https?://|/upload/)[^\s\"\'<>\\)]+?\.pdf',html.unescape(chunk),re.I):
      url=urllib.parse.urljoin(r.geturl(),m.group(0))
      if not urllib.parse.urlsplit(url).query:urls.append(url)
     rows.append({'label':label[:240],'actual_pdf_urls':list(dict.fromkeys(urls))})
    out['cecs_rows']=rows
 except urllib.error.HTTPError as e:out.update(http_status=e.code,error_type='HTTPError')
 except Exception as e:out.update(error_type=type(e).__name__,error_summary=str(e)[:200])
 return out
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:rows=list(pool.map(one,targets))
p=Path(r'C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017/search/round10-public-sources/instrument-observations-r10.json');assert not p.exists()
d={'source_id':'SEARCH-R10-INSTRUMENT-OBSERVATIONS-20261017','observations':rows,'boundary':'Only structured labels/observed PDF routes and GET facts. No HTML, PDF bodies, transient parameters, credentials or completeness judgment.'}
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(d,ensure_ascii=False,indent=2))
