"""Collect factual CECS directory metadata from public primary institutional sources."""
import concurrent.futures
import datetime
import hashlib
import html
import io
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
INDEX = 'https://sjw.qingdao.gov.cn/cxjsj3/cxjsj200/cxjsj_hydt2/'
OLD = 'https://lwec.net/www/upload/article/2018/0611/20180611105853108184.docx'
OLD_PAGE = 'https://lwec.net/article/detail-107'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
PATTERN = re.compile(r'(?:(T)\s*[/∕]?\s*)?(CECS(?:-CBIMU)?)\s*([0-9]{1,5})\s*[:：—–-]\s*((?:19|20)[0-9]{2})', re.I)

def get(url):
    with urllib.request.urlopen(url, timeout=25) as response:
        data = response.read(12 * 1024 * 1024 + 1)
        if len(data) > 12 * 1024 * 1024:
            raise ValueError('directory source exceeds 12MiB cap')
        return data, response.geturl()

def plain(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', value))).strip()

def code(raw):
    m = PATTERN.search(raw)
    if not m:
        return None
    prefix = ('T/' if m[1] else '') + m[2].upper()
    number = str(int(m[3]))
    year = m[4]
    return {'standard_number': f'{prefix} {number}-{year}', 'number': number,
            'year': year, 'standard_family': prefix, 'draft_stage': '正式版目录记录'}

records, sources, failures = [], [], []
try:
    data, final = get(OLD)
    xml = ET.fromstring(zipfile.ZipFile(io.BytesIO(data)).read('word/document.xml'))
    rows = [[''.join(t.text or '' for t in cell.findall('.//w:t', NS))
             for cell in row.findall('./w:tc', NS)] for row in xml.findall('.//w:tr', NS)]
    sources.append({'source_id': 'LWEC-20180611-CECS-CATALOG', 'source_page': OLD_PAGE,
                    'attachment_url': final, 'source_date': '2018-06-11', 'checked_at': NOW,
                    'sha256': hashlib.sha256(data).hexdigest(), 'rows': len(rows) - 1,
                    'scope': '2018年机构有效目录历史快照，不能证明2026现行性'})
    for line, cells in enumerate(rows[1:], 2):
        if len(cells) < 4:
            continue
        parsed = code(cells[1])
        if not parsed:
            failures.append({'source': OLD, 'row': line, 'raw': cells, 'error': 'unparsed_number'})
            continue
        replacement = code(cells[4]) if len(cells) > 4 else None
        records.append({**parsed, 'name': cells[2].strip(), 'implementation_date_raw': cells[3],
            'source_id': f'LWEC-20180611-CECS-CATALOG:table-row-{line}', 'source_page': OLD_PAGE,
            'source_url': final, 'checked_at': NOW, 'status': '未知（2026现行性待核）',
            'historical_status': '2018年机构有效目录收录', 'replaces_raw': cells[4] if len(cells) > 4 else '',
            'replaces': replacement['standard_number'] if replacement else '',
            'evidence_type': '原文事实（历史目录记录）', 'raw_cells': cells})
    (ROOT / 'lwec-2018-catalog-extraction.json').write_text(json.dumps({
        'source_page': OLD_PAGE, 'source_url': final, 'checked_at': NOW,
        'status_scope': '2018年有效目录历史快照，不能证明2026现行性', 'rows': rows}, ensure_ascii=False, indent=2), encoding='utf-8')
except Exception as exc:
    failures.append({'source': OLD, 'error': f'{type(exc).__name__}: {exc}'})

def monthly(task):
    title, url = task
    data, final = get(url)
    text = data.decode('utf-8-sig')
    found = []
    for line, row in enumerate(re.findall(r'<tr\b[^>]*>(.*?)</tr>', text, re.S | re.I), 1):
        cells = [plain(c) for c in re.findall(r'<t[dh]\b[^>]*>(.*?)</t[dh]>', row, re.S | re.I)]
        if len(cells) < 4:
            continue
        parsed = code(cells[1])
        if parsed:
            found.append({**parsed, 'name': cells[2], 'implementation_date_raw': cells[3],
                'source_id': f'QINGDAO-{hashlib.sha256(final.encode()).hexdigest()[:10]}:table-row-{line}',
                'source_page': final, 'source_url': final, 'checked_at': NOW,
                'status': '未知（实施日期有官方记录；现行性待核）', 'source_title': title,
                'evidence_type': '原文事实（官方月度实施清单）', 'raw_cells': cells})
    source = {'source_page': final, 'title': title, 'checked_at': NOW,
              'sha256': hashlib.sha256(data).hexdigest(), 'cecs_rows': len(found),
              'scope': '青岛住建局月度实施清单中的CECS元数据；不是青岛地方标准，不是完整CECS目录'}
    return source, found

try:
    data, _ = get(INDEX)
    text = data.decode('utf-8-sig')
    tasks = []
    for href, title in re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', text, re.S | re.I):
        title = plain(title)
        if re.search(r'202[56]年\d+月开始实施的工程建设标准', title):
            item = (title, urllib.parse.urljoin(INDEX, href).replace('http://sjw.qingdao.gov.cn/', 'https://sjw.qingdao.gov.cn/'))
            if item not in tasks:
                tasks.append(item)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(monthly, task): task for task in tasks}
        for future in concurrent.futures.as_completed(futures):
            try:
                source, found = future.result()
                sources.append(source)
                records.extend(found)
            except Exception as exc:
                failures.append({'source': futures[future][1], 'error': f'{type(exc).__name__}: {exc}'})
except Exception as exc:
    failures.append({'source': INDEX, 'error': f'{type(exc).__name__}: {exc}'})

result = {'schema_version': 1, 'checked_at': NOW, 'producer': 'controller-authority-directory',
    'note': '官方或机构原始目录元数据。不是全文下载证据，不确认2026现行性；不补猜未列编号。',
    'coverage': {'sources_count': len(sources), 'record_count': len(records),
                 'unique_number_year_count': len(set(r['standard_number'] for r in records))},
    'sources': sources, 'standards': records, 'failures': failures}
canonical = ROOT / 'authority-directory-records.json'
if canonical.exists():
    old = canonical.read_bytes()
    history = ROOT / 'history'
    history.mkdir(exist_ok=True)
    (history / ('authority-directory-records-' + hashlib.sha256(old).hexdigest()[:12] + '.json')).write_bytes(old)
canonical.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result['coverage']))
print('failures', len(failures))
