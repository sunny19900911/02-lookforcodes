import html
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

root = Path(__file__).resolve().parent
source = (root / 'tj-raw.html').read_text(encoding='utf-8-sig')
old = json.loads((root / 'candidates-round02.json').read_text(encoding='utf-8-sig'))
blocks = re.findall(r"<div class='line g_item'>(.*?)(?=<div class='separatorLine|\t<div class='clearfloat')", source, flags=re.S)
items = []
for block in blocks:
    title = re.search(r"class='fileNameWrap' title='([^']+)'", block)
    if not title or not title.group(1).startswith('CECS '):
        continue
    title = html.unescape(title.group(1))
    hrefs = re.findall(r"href='([^']+)'", block)
    links = ['https:' + html.unescape(x) if x.startswith('//') else html.unescape(x) for x in hrefs]
    for item in old['candidates']:
        number = item['standard_number'].split()[1].split(':')[0]
        if re.match(r'CECS\s+' + re.escape(number) + r'[：:]', title):
            result = dict(item)
            result['download_url'] = next(x for x in links if 'download.s21i.co99.net' in x)
            result['alternative_urls'] = [x for x in links if x != result['download_url']]
            result['checked_at'] = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
            result['permission_status'] = '公开页面明确提供下载href；未登录；独立GET待审'
            result['source_id'] = 'SEARCH-TJ-JWDZ-20261017-P4'
            result['discovery_evidence'] = 'curl公开GET并解压页面HTML，提取同一CECS标题行的下载href和站点预览href；未用HTTP200推断PDF完整性'
            result['download_check_status'] = '候选未审'
            items.append(result)
output = {'round': 'R02-tj-href-supplement', 'producer': 'search', 'replaces_fields_only': '保留R01-G4-006至009原candidate_id，补充download_url及备用链接', 'candidates': items}
(root / 'candidates-round03-tj-links.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'candidate_count': len(items), 'ids': [x['candidate_id'] for x in items]}, ensure_ascii=False))
