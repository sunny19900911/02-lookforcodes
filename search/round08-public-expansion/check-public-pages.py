import urllib.request,urllib.parse,concurrent.futures,re,json
from html.parser import HTMLParser
from datetime import datetime,timezone,timedelta
from pathlib import Path

targets=[
 'https://www.lsjcrzzx.com/',
 'https://m.cnass.cn/site/content/325.html',
 'https://www.cnass.cn/site/content/325.html',
 'https://media.src.leju.com/imp/imp/deal/10/1f/3/e20c955f600d4a5ca00a52e7ac1_p24_mk24.pdf'
]
class Links(HTMLParser):
 def __init__(self): super().__init__();self.links=[];self.current=None
 def handle_starttag(self,t,attrs):
  if t=='a':
   self.current=[dict(attrs).get('href',''),''];self.links.append(self.current)
 def handle_endtag(self,t):
  if t=='a':self.current=None
 def handle_data(self,d):
  if self.current is not None:self.current[1]+=d
def safe(u):
 parts=urllib.parse.urlsplit(u)
 return not any(k.lower() in {'uhash','token','access_token','signature','sign','secret','password','authorization'} for k,v in urllib.parse.parse_qsl(parts.query))
def one(u):
 out={'requested_url':u,'checked_at':datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'),'method':'ordinary anonymous GET; PDF body only prefix read, not completeness audit'}
 try:
  with urllib.request.urlopen(u,timeout=20) as r:
   out.update(http_status=r.status,final_url=r.geturl() if safe(r.geturl()) else None,content_type=r.headers.get('Content-Type'))
   prefix=r.read(64)
   out['pdf_prefix']=prefix.startswith(b'%PDF-')
   if out['pdf_prefix']:
    out['observation']='GET opened and PDF signature prefix read only; body not fully downloaded or audited'
   else:
    b=prefix+r.read(2000000)
    text=b.decode('utf-8',errors='replace')
    p=Links();p.feed(text)
    out['title']=(re.findall(r'<title[^>]*>(.*?)</title>',text,re.I|re.S) or [None])[0]
    out['relevant_links']=[{'url':urllib.parse.urljoin(r.geturl(),h),'text':t.strip()[:250]} for h,t in p.links if safe(urllib.parse.urljoin(r.geturl(),h)) and (re.search(r'CECS|绿色建材|\.pdf|\.docx',h+' '+t,re.I))]
    out['body_bytes_read']=len(b)
 except Exception as e:
  out['error_type']=type(e).__name__
  out['error_summary']=str(e).split(u)[0][:200] if u in str(e) else str(e)[:200]
 return out
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: rows=list(pool.map(one,targets))
p=Path(r'C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017/search/round08-public-expansion/public-page-observations-r08.json')
assert not p.exists()
data={'source_id':'SEARCH-R08-PUBLIC-PAGES-20261017','statement_type':'原文事实（普通匿名GET观察，非完整性审查）','observations':rows}
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(data,ensure_ascii=False,indent=2))
