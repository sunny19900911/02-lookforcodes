from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.parse import urlsplit, parse_qsl, urlencode, urlunsplit
import json, hashlib, copy

base = Path(r'C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017')
search = base / 'search'
folder = search / 'round07-broad-attachments/water-mep'
now = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
raw = folder / 'candidates-round07-water-mep.json'
data = json.loads(raw.read_text(encoding='utf-8-sig'))
share = copy.deepcopy(data)
share['share_prepared_at'] = now
share['derived_from_local_sha256'] = digest(raw)
share['sharing_note'] = '分享派生版；原始固定输入不改。公开下载脚本的瞬时uhash/原始响应不分享，保留稳定详情页、普通访问方法及失败结果。未取得具体父页时不以首页冒充父页。'
for c in share['candidates']:
    if c['candidate_id'] in ['R07-WATER-MEP-41-2004', 'R07-WATER-MEP-164-2004']:
        c['domain_context_homepage'] = c['source_page']
        c['source_page'] = c['download_url']
        c['detail_url'] = None
        c['parent_page_status'] = '未定位具体附件父页；原记录首页仅作域名背景。PDF URL由公开搜索索引发现。'
        for e in c['metadata_evidence']:
            e['source_url'] = c['download_url']
            e['evidence_type'] = '原文事实（公开搜索索引/本轮web解析观察；未作独立GET审查）'
    c['complete_pdf'] = None
for route in share['zero_candidate_or_pending_routes']:
    public = route.pop('public_download_route', {})
    ep = public.get('public_download_endpoint')
    if ep:
        u = urlsplit(ep)
        route['stable_public_endpoint_without_transient_parameter'] = urlunsplit((u.scheme,u.netloc,u.path,urlencode([(k,v) for k,v in parse_qsl(u.query) if k != 'uhash']),''))
    route['public_button_response_observation'] = '公开下载按钮脚本返回开始下载；瞬时响应/参数不纳入分享版。'
    head = route.get('head_observation', {})
    for key in ['download_url', 'final_url']:
        head.pop(key, None)
    route['transient_parameter_note'] = '下载地址随正常页面请求生成且本轮已失效；不应把瞬时地址当持久PDF URL。'
assert len(share['candidates']) == 4
assert len(share['zero_candidate_or_pending_routes']) == 4
assert all(c['source_id'] and c['download_url'] for c in share['candidates'])
text = json.dumps(share, ensure_ascii=False, indent=2) + '\n'
assert 'uhash=' not in text
out = folder / 'candidates-round07-water-mep-share.json'
assert not out.exists()
out.write_text(text, encoding='utf-8')
ledger = {
    'source_id': 'SEARCH-R07-WATER-MEP-QUERY-LEDGER', 'recorded_at': now,
    'observation_checked_at': data['checked_at'], 'queries': data['queries'],
    'coverage_numbers': data['coverage_numbers'],
    'failed_or_excluded': data['failed_or_excluded'],
    'method_revision': data['method_revision'],
    'method_boundary': '日志为本轮检索人员记录，非独立PDF质量审查。原始web响应仅本地保留，不列入同步manifest。',
    'raw_candidates_local_sha256': digest(raw),
    'raw_web_response_local_sha256': digest(folder / 'web-round07-water-mep.json')
}
ledger_path = folder / 'query-ledger-r07-water-mep-share.json'
assert not ledger_path.exists()
ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
summary = {
    'source_id': 'SEARCH-R07-WATER-MEP-ADDENDUM', 'recorded_at': now,
    'candidate_count': 4, 'historical_formal_candidates': 2,
    'draft_count': 0, 'failed_manufacturer_routes': 4,
    'standard_keys': [c['standard_number'] for c in share['candidates']],
    'r07_combined_candidate_count': 7, 'r07_numbered_candidates': 6, 'r07_placeholder_drafts': 1,
    'standard_complete_pdf_count_added_by_search': 0,
    'prior_1340_manifest_sha256': digest(search / 'freeze-inputs-1340.json'),
    'parent_source_correction': '公元41/164具体父页未定位；source_page为实际PDF，首页只作域名背景；1012由公开HTML checkbox value取得实际地址。',
    'boundary': '正式/历史均为候选，最终URL与完整性留给审查角色；失败按钮路线不计PDF。主库净新增数由目录角色去重决定。'
}
summary_path = folder / 'addendum-r07-water-mep.json'
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
paths = [out, ledger_path, summary_path]
manifest = {'producer': 'search', 'checkpoint': '13:40-water-mep-addendum', 'checked_at': now, 'frozen': True,
    'input_file_count': len(paths), 'note': '仅同步本manifest列出的3个结构化分享文件；原始web/candidates不纳入，不含PDF/PNG/HTML/瞬时uhash。1340及更早冻结不改。',
    'files': [{'path': p.relative_to(base).as_posix(), 'sha256': digest(p), 'bytes': p.stat().st_size} for p in paths]}
mf = search / 'freeze-inputs-1340-water-mep-addendum.json'
assert not mf.exists()
mf.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'manifest': str(mf), 'sha256': digest(mf), 'files': len(paths), 'summary': summary}, ensure_ascii=False, indent=2))
