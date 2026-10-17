"""Authorized 15:10 checkpoint: append fixed R09/R10/R11; no network or Git."""
import collections
import copy
import datetime
import hashlib
import json
import pathlib
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent
PATH = ROOT / 'audit-results.json'
FREEZE = ROOT / 'audit-results-freeze-1510.json'
RECEIPT = ROOT / 'freeze-1510-receipt.json'
OLD_SHA = 'a81a40dfff05c0bd437b99875baba5efc7f540c05ae9c59437aceb66d5aa65e2'
FIXED_INPUTS = [
    ('audit-pending-round07-freeze-1430.json', '1f75a6b1536d5265a2a8cb814e1c2d1c7630de38d9dd49ec707650a174aebe0f', 6),
    ('audit-pending-round08-fixed-r10.json', 'b85f429140403811b90b5215ca38ab9c45d420705073ccb55c93f072805843e5', 2),
    ('audit-pending-round09-freeze-1450-v2.json', '339a53ad776599ca4181a75633dd0479b1f040d293e9bf35d02dd762937196ef', 7),
]
REFERENCES = {
    'candidates-r11-alt31-share.json': '2aa5cd96cfcc3f9d3848c7046575bb72e53b7426fb602f8b58b191558b94a61d',
    'audit-round09-publication-selection-1450.json': '91744369ebd0b0916afa791012dd3ab6ca3dedbaa0b57c061d92848d41523e44',
    'evidence-85-repeal-cecs69-94.json': '442e9485aae9fed84a118ebfdc0365e80bb2328ef05ba901958274a81178f95e',
    'active-cecs-scope.json': 'acc68fea52f390c7a97580cd6c9e67d141e7c1b467af8afecd3c4740e48838ec',
    'scope-change-engineering-all-20261017.json': 'dcabb6987e1868c497e043cc8f24047e9a2154bf22fd23e056c5b8b505f61c4a',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_verified(name, digest):
    content = (ROOT / name).read_bytes()
    assert sha(content) == digest, f'Input changed: {name}'
    return json.loads(content.decode('utf-8-sig'))


def primary_url(row):
    # resId/lid and other query values identify resources. Never reduce to host/path.
    value = next((row.get(k) for k in ['requested_url', 'download_url', 'direct_url'] if row.get(k)), None)
    if not value:
        return None
    u = urllib.parse.urlsplit(value)
    return urllib.parse.urlunsplit((u.scheme.lower(), u.netloc.lower(), u.path, u.query, ''))


before = PATH.read_bytes()
assert sha(before) == OLD_SHA
assert (ROOT / 'audit-results-freeze-1410.json').read_bytes() == before
assert not FREEZE.exists() and not RECEIPT.exists(), 'Never overwrite a checkpoint'
old_freezes = {p.name: sha(p.read_bytes()) for p in ROOT.glob('audit-results-freeze-*.json')}
base = json.loads(before)
assert len(base['results']) == 48
old_rows = copy.deepcopy(base['results'])
pending = [(name, read_verified(name, digest), count) for name, digest, count in FIXED_INPUTS]
reference_data = {name: read_verified(name, digest) for name, digest in REFERENCES.items()}
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
ids = {r['candidate_id'] for r in old_rows}
urls = {primary_url(r) for r in old_rows if primary_url(r)}
assert len(ids) == 48
assert len(urls) == sum(primary_url(r) is not None for r in old_rows)
added = []
for name, document, count in pending:
    assert len(document['results']) == count
    for row in document['results']:
        assert row['candidate_id'] not in ids, f'Duplicate ID: {row["candidate_id"]}'
        url = primary_url(row)
        assert url and url not in urls, f'Duplicate tested URL: {url}'
        ids.add(row['candidate_id'])
        urls.add(url)
        r = copy.deepcopy(row)
        r.setdefault('audit_history', []).append({
            'checked_at': NOW,
            'method': '主控明确批准15:10固定R09/R10/R11回灌',
            'input_snapshot': name,
            'outcome': '仅追加固定审查与证据字段；保留主评级、正文浏览范围、版本及完整性独立结论',
        })
        base['results'].append(r)
        added.append(r)

evidence = reference_data['evidence-85-repeal-cecs69-94.json']
assert evidence['announcement_number'] == '85'
assert evidence['announcement_date'] == '2011-06-22'
assert evidence['implementation_date'] == evidence['repeal_effective_date'] == '2011-10-01'
assert evidence['repealed_standard_number'] == 'CECS 69:94'
assert evidence['pdf_physical_page'] == 2 and evidence['page_side'] == '左半页'
assert evidence['printed_page'] is None
assert reference_data['active-cecs-scope.json']['active_source_id'] == 'USER-20261017-CECS-ENGINEERING-ALL'
assert reference_data['active-cecs-scope.json']['non_building_structure_is_exclusion_reason'] is False
base.update(updated_at=NOW, checkpoint='1510', handoff_state='15:10冻结，待主控本轮本地封版；R12/R13等后续候选不纳入本批')
base['counting_rules']['complete_draft'] = 'draft_content_complete=true单列并保留实际报批稿/送审稿/征求意见稿阶段；complete_pdf=false不表示草案内容不完整'
base['counting_rules']['reading_quality'] = 'A/B/C/D主推荐与稿型、完整性分别保存；B19含14正式完整链接与5件完整草案；1555主D、正文浏览范围B不进入主B计数，200不补正文B'
base['checkpoint_inputs'] = [{'file': name, 'sha256': digest, 'result_count': count} for name, digest, count in FIXED_INPUTS]
base['checkpoint_references'] = [{'file': name, 'sha256': digest} for name, digest in REFERENCES.items()]
base['active_scope_reference'] = {'source_id': 'USER-20261017-CECS-ENGINEERING-ALL', 'record': 'active-cecs-scope.json', 'priority': '房屋结构设计相关优先'}

rows = base['results']
by_id = {r['candidate_id']: r for r in rows}
complete = [r for r in rows if r.get('complete_pdf') is True]
drafts = [r for r in rows if r.get('draft_content_complete') is True]
ratings = {k: sum(r.get('recommendation') == k for r in rows) for k in ['A', 'B', 'C', 'D']}
stages = dict(collections.Counter(r['version_class'] for r in drafts))
assert len(rows) == len(by_id) == 63 and len(added) == 15
assert len(complete) == 14 and all(r.get('version_verified') is True for r in complete)
assert len({r['standard_key'] for r in complete}) == len({r['sha256'] for r in complete}) == 12
assert ratings == {'A': 0, 'B': 19, 'C': 18, 'D': 26}
assert len(drafts) == 5 and stages == {'报批稿': 3, '送审稿': 1, '征求意见稿': 1}
assert all(r['complete_pdf'] is False for r in drafts)
assert old_rows == rows[:48]
assert sum(bool(r.get('metadata_only')) for r in rows) == 1
assert by_id['R11-1555-2024-FAIUSR']['recommendation'] == 'D'
assert by_id['R11-1555-2024-FAIUSR']['body_reading_recommendation'] == 'B（仅已收录正文浏览范围）'
assert by_id['R11-200-2006-DLSSYHT']['recommendation'] == 'D'
assert not by_id['R11-200-2006-DLSSYHT'].get('body_reading_recommendation')
assert by_id['R11-31-2017-APEXTRAY'].get('pages') is None
assert by_id['R11-31-2017-APEXTRAY']['web_pages_observed'] == 64
assert by_id['R11-31-2017-GUANGYUXC'].get('pages') is None
assert by_id['R11-31-2017-GUANGYUXC']['web_pages_observed'] is None
assert by_id['R11-INST-PDF-001']['sha256'] == by_id['R01-G4-009']['sha256'] == by_id['R01-G4-009-ALT']['sha256']
assert not any(r['candidate_id'].startswith(('R12-', 'R13-')) for r in rows)

out = json.dumps(base, ensure_ascii=False, indent=2).encode('utf-8')
digest = sha(out)
receipt = {
    'checkpoint': '2026-10-17T15:10:00+08:00', 'frozen_at': NOW, 'updated_at': NOW,
    'before_sha256': OLD_SHA, 'sha256': digest,
    'input_snapshots': base['checkpoint_inputs'], 'reference_snapshots': base['checkpoint_references'],
    'result_count': 63, 'complete_link_count': 14, 'complete_version_count': 12, 'complete_hash_count': 12,
    'complete_draft_count': 5, 'complete_draft_stage_counts': stages,
    'complete_drafts': [{'candidate_id': r['candidate_id'], 'version_class': r['version_class']} for r in drafts],
    'rating_counts': ratings, 'rating_scope_note': base['counting_rules']['reading_quality'],
    'metadata_only_count': 1, 'additions': 15, 'replacements': 0,
    'merged_candidate_ids': [r['candidate_id'] for r in added],
    'old_freeze': 'audit-results-freeze-1410.json', 'current_freeze': FREEZE.name,
    'old48_records_unchanged': True, 'old_freeze_sha256': old_freezes, 'history_preserved': True,
    'tested_url_identity': 'requested_url优先，其次download_url/direct_url；保留资源query参数（含NWAFU resId/lid），不将alternative_urls元数据计为已测链接',
    'same_hash_different_url': 'R11-INST-PDF-001与旧两份02同SHA，保留实际GET新链接，不计新内容版本',
    'historical_repeal_evidence': {
        'source_id': evidence['source_id'], 'file': 'evidence-85-repeal-cecs69-94.json',
        'sha256': REFERENCES['evidence-85-repeal-cecs69-94.json'],
        'announcement': '中国工程建设标准化协会第85号，2011-06-22；2011-10-01实施并同时废止CECS69:94',
        'location': 'PDF2左半页、无印刷folio；PDF16右印25另佐证日期/公告号',
        'limits': '仅历史废止事件；不推断69:2011在2026现行，旧69:94及HPU404记录均保留',
    },
    'publication_selection': '仅R11 v2及备用31当前sharing投影；历史v1/继承64页的派生输入保留但不选用',
    'active_scope_source_id': 'USER-20261017-CECS-ENGINEERING-ALL',
    'quality_limits': '1555整件D/正文浏览B；200整件D且原件漏单位，不补正文B；197/69:2011疑似空白背页未证仍C；243技术文字缺失仍C；五件完整草案不计正式完整。',
    'excluded_pending': 'R12/R13及其他后续新候选不纳入本次63；封版前暂停新GET',
    'canonical_frozen_until': '主控本轮本地封版；后续新GET另存独立pending',
    'publication_status': '本角色未操作Git或远端，PDF及PNG仅本地；发布状态由主控另登记',
}
PATH.write_bytes(out)
FREEZE.write_bytes(out)
RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
assert PATH.read_bytes() == FREEZE.read_bytes()
for name, expected in old_freezes.items():
    assert sha((ROOT / name).read_bytes()) == expected
for name, expected, _ in FIXED_INPUTS:
    assert sha((ROOT / name).read_bytes()) == expected
for name, expected in REFERENCES.items():
    assert sha((ROOT / name).read_bytes()) == expected
print(json.dumps(receipt, ensure_ascii=False))
