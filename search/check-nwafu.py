import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import urlopen, Request

root = Path(__file__).resolve().parent
url = 'https://eol.nwafu.edu.cn/meol/analytics/resPdfShow.do?resId=283228&lid=47196'
result = {'source_page':'https://eol.nwafu.edu.cn/meol/homepage/course/listview.jsp?_colId=null&_style=new03&acttype=enter&folderid=283225&lid=47196', 'preview_page':'https://eol.nwafu.edu.cn/meol/common/script/preview/download_preview.jsp?fileid=577890&resid=283228&lid=47196&preview=preview', 'observed_public_iframe_url':url,'checked_at':datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')}
try:
    with urlopen(Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=25) as response:
        data = response.read(512)
        result.update({'status':response.status,'final_url':response.url,'content_type':response.headers.get('Content-Type'), 'starts_with_pdf':data.startswith(b'%PDF-'), 'bytes_checked':len(data)})
        if not data.startswith(b'%PDF-'):
            result['non_pdf_prefix'] = data.decode('utf-8', errors='replace')[:250]
except Exception as exc:
    result['error'] = str(exc)
result['boundary']='仅公开预览iframe GET首512字节探测；非完整PDF验证；若认证/权限拒绝则停止，不绕过'
(root/'nwafu-route-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
