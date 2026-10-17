import html
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parent
source_url = 'https://eol.nwafu.edu.cn/meol/homepage/course/listview.jsp?_colId=null&_style=new03&acttype=enter&folderid=283225&lid=47196'
raw = (root/'nwafu-public-list.html').read_bytes()
source = raw.decode('gb18030', errors='replace')
items = []
for href, title in re.findall(r'<a href="([^"]+)"[^>]*?title="([^"]*CECS[^"]*)"', source, re.S):
    title = html.unescape(title).strip()
    number = re.search(r'CECS\s*(\d+)[-:： ]+(\d{4})', title)
    if not number:
        continue
    num, year = number.groups()
    preview_url = urljoin(source_url, html.unescape(href))
    checked = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
    item = {'candidate_id':f'R02-G3-NWAFU-{num}-{year}', 'seed_ids':['S017','S081'] if num=='200' and year=='2006' else [], 'topic_group':'G3','standard_number':f'CECS {num}:{year}','year':year,'name':title[number.end():].strip(' _'),'draft_stage':'历史版本候选；正式出版与完整性待审','source_id':'NWAFU-PUBLIC-STEEL-COURSE-20261017','source_page':source_url,'preview_page':preview_url,'download_url':None,'alternative_urls':[],'checked_at':checked,'permission_status':'公开课程资料列表及预览页面；无登录；转载授权未独立核实','metadata_evidence':[{'source_url':source_url,'evidence_type':'原文事实','claim':f'课程公开列表以此标题列出文件：{title}；不作为2026现行性证据'}]}
    try:
        with urlopen(Request(preview_url,headers={'User-Agent':'Mozilla/5.0'}),timeout=20) as response:
            preview = response.read().decode('gb18030',errors='replace')
        match = re.search(r'encodeURIComponent\("([^"]+resPdfShow[^\"]*)"\)', preview)
        if not match:
            item['route_status']='预览未提供PDF链接；未绕过登录或权限'
        else:
            direct = urljoin(preview_url, html.unescape(match.group(1)))
            direct = re.sub(r';jsessionid=[^?;/]+', '', direct)
            item['download_url']=direct
            with urlopen(Request(direct,headers={'User-Agent':'Mozilla/5.0'}),timeout=20) as response:
                prefix = response.read(512)
                item['prefix_check']={'http_status':response.status,'final_url':response.url,'content_type':response.headers.get('Content-Type'),'bytes_checked':len(prefix),'starts_with_pdf':prefix.startswith(b'%PDF-')}
            item['route_status']='首512字节为PDF；全文版本/完整性/质量待独立审查' if item['prefix_check']['starts_with_pdf'] else '非PDF响应；不可计全文'
    except Exception as exc:
        item['route_status']='本次网络失败未验证'
        item['error']=str(exc)
    item['download_check_status']='候选未审'
    items.append(item)
out={'round':'R02-public-university','producer':'search','checked_at':datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'),'note':'从公开列表标题跟随明确预览链接，再提取页面实际提供的iframe PDF地址；未构造或枚举资源ID。首字节不证明完整性。','candidates':items}
(root/'candidates-round05-nwafu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'count':len(items),'results':[{'id':x['candidate_id'],'name':x['name'],'direct':x['download_url'],'status':x['route_status']} for x in items]},ensure_ascii=False,indent=2))
