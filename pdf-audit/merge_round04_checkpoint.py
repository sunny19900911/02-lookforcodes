import collections, copy, datetime, hashlib, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
path = ROOT / 'audit-results.json'
before_bytes = path.read_bytes()
before_sha = hashlib.sha256(before_bytes).hexdigest()
assert before_sha == '28e9f89c8134d5933aef28565efc2ddf22a8e4aaa5eb5691ccd09f5283063f25', before_sha
canonical = json.loads(before_bytes)
pending_path = ROOT / 'audit-pending-round04.json'
pending = json.loads(pending_path.read_text(encoding='utf-8'))
assert len(pending['results']) == 3
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
merged = {r['candidate_id']: copy.deepcopy(r) for r in canonical['results']}
replacements = 0
additions = 0
for record in pending['results']:
    ident = record['candidate_id']
    prior = merged.get(ident)
    replacement = copy.deepcopy(record)
    replacements += int(prior is not None)
    additions += int(prior is None)
    history = (prior or {}).get('audit_history', []) + replacement.get('audit_history', [])
    seen = set()
    combined = []
    for event in history:
        key = json.dumps(event, ensure_ascii=False, sort_keys=True)
        if key not in seen:
            combined.append(event)
            seen.add(key)
    combined.append({'checked_at': NOW, 'method': '主控13:30固定截点回灌；保留原GET、双审及证据纠错history', 'outcome': '替换既有审查' if prior else '追加新候选实测'})
    replacement['audit_history'] = combined
    merged[ident] = replacement

canonical['results'] = list(merged.values())
canonical['updated_at'] = NOW
canonical['handoff_state'] = '13:30冻结，待主控同步或本地封版完成'
canonical['checkpoint'] = '1330'
complete = [r for r in canonical['results'] if r.get('complete_pdf')]
assert len(canonical['results']) == 33
assert len(complete) == 9
assert all(r.get('version_verified') for r in complete)
assert len({r['standard_key'] for r in complete}) == 7
assert len({r['sha256'] for r in complete}) == 7
assert replacements == 1 and additions == 2
ratings = {label: sum(r.get('recommendation') == label for r in canonical['results']) for label in ['A', 'B', 'C', 'D']}
assert ratings == {'A': 0, 'B': 9, 'C': 11, 'D': 13}, ratings

after_bytes = json.dumps(canonical, ensure_ascii=False, indent=2).encode('utf-8')
after_sha = hashlib.sha256(after_bytes).hexdigest()
path.write_bytes(after_bytes)
(ROOT / 'audit-results-freeze-1330.json').write_bytes(after_bytes)
receipt = {
    'checkpoint': '2026-10-17T13:30:00+08:00', 'frozen_at': NOW,
    'before_sha256': before_sha, 'sha256': after_sha, 'updated_at': NOW,
    'result_count': len(canonical['results']), 'complete_link_count': len(complete),
    'complete_version_count': 7, 'complete_hash_count': 7, 'rating_counts': ratings,
    'metadata_only_count': sum(bool(r.get('metadata_only')) for r in canonical['results']),
    'replacements': replacements, 'additions': additions,
    'merged_candidate_ids': [r['candidate_id'] for r in pending['results']],
    'old_freeze': 'audit-results-freeze-1320.json', 'current_freeze': 'audit-results-freeze-1330.json',
    'history_preserved': True,
    'new_complete_candidate': 'R03-G1-22-2024-ZGB-202603',
    'quality_limit': '22-2024双审支持B；OCR有误，原图有重复条号疑点；不称出版社原生书签或全网最优。796单页公告非标准全文；661仍C。'
}
(ROOT / 'freeze-1330-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
pending['merged_at'] = NOW
pending['merged_candidate_ids'] = receipt['merged_candidate_ids']
pending['status'] = 'merged_into_1330_checkpoint'
pending_path.write_text(json.dumps(pending, ensure_ascii=False, indent=2), encoding='utf-8')
assert hashlib.sha256((ROOT / 'audit-results-freeze-1320.json').read_bytes()).hexdigest() == before_sha
assert (ROOT / 'audit-results-freeze-1330.json').read_bytes() == path.read_bytes()
print(json.dumps(receipt, ensure_ascii=False))
