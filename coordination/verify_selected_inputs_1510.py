"""Controller's read-only hash and union check for the selected 15:10 inputs."""
import collections
import datetime
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parent
SELECTED = {
    'search/freeze-inputs-1420.json': 'cc3118242ffa6b13e530ef48678adacb5a6fc9a2d0fe553f39be2ca6e66df2ed',
    'search/freeze-inputs-1430.json': '3974c2d6470358bce3c086132f783d963e351988ab4bf18450def551067d5722',
    'search/freeze-inputs-1440.json': 'c6da85fcbe8c2c3a5a54166ee03eacee36f0c1b5f7de58eadb398686525d0be7',
    'search/freeze-region-metadata-1530.json': 'a2f5754e0962f20204fd05fcd17cabaec077e16035fb9cc6d08ad6e7184c1772',
    'pdf-audit/audit-results-freeze-1410.json': 'a81a40dfff05c0bd437b99875baba5efc7f540c05ae9c59437aceb66d5aa65e2',
    'pdf-audit/audit-pending-round07-freeze-1430.json': '1f75a6b1536d5265a2a8cb814e1c2d1c7630de38d9dd49ec707650a174aebe0f',
    'pdf-audit/audit-pending-round08-fixed-r10.json': 'b85f429140403811b90b5215ca38ab9c45d420705073ccb55c93f072805843e5',
    'pdf-audit/audit-pending-round09-freeze-1450-v2.json': '339a53ad776599ca4181a75633dd0479b1f040d293e9bf35d02dd762937196ef',
    'pdf-audit/candidates-r11-alt31-share.json': '2aa5cd96cfcc3f9d3848c7046575bb72e53b7426fb602f8b58b191558b94a61d',
    'pdf-audit/evidence-85-repeal-cecs69-94.json': '442e9485aae9fed84a118ebfdc0365e80bb2328ef05ba901958274a81178f95e',
}

def read_checked(rel, expected):
    raw = (ROOT / rel).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected, f'Selected input changed: {rel}'
    return json.loads(raw.decode('utf-8-sig')) if Path(rel).suffix == '.json' else None

docs = {rel: read_checked(rel, sha) for rel, sha in SELECTED.items()}
manifest_files = []
for rel, doc in docs.items():
    if rel.startswith('search/') and isinstance(doc.get('files'), list):
        for entry in doc['files']:
            read_checked(entry['path'], entry['sha256'])
            manifest_files.append(entry['path'])

audit_paths = [rel for rel in SELECTED if '/audit-' in rel]
observations = [a for rel in audit_paths for a in docs[rel]['results']]
ids = [a.get('audit_id') or a.get('candidate_id') for a in observations]
assert len(observations) == 63 and len(ids) == len(set(ids))
urls = [a.get('requested_url') or a.get('download_url') for a in observations]
assert len(urls) == len(set(urls)), 'Duplicate selected request URL'
formal = [a for a in observations if a.get('complete_pdf') and a.get('version_verified')]
drafts = [a for a in observations if a.get('draft_content_complete')]
assert len(formal) == 14 and len({a['sha256'] for a in formal}) == 12
assert len(drafts) == 5 and all(not a.get('complete_pdf') for a in drafts)
ratings = dict(collections.Counter(a.get('recommendation') for a in observations))
assert ratings == {'B': 19, 'C': 18, 'D': 26}, ratings
by_id = {a.get('audit_id') or a.get('candidate_id'): a for a in observations}
alt = by_id['R11-31-2017-GUANGYUXC']
assert alt.get('pages') is None and alt.get('web_pages_observed') is None
assert not alt.get('complete_pdf')
selection = json.loads((ROOT / 'pdf-audit/audit-round09-publication-selection-1450.json').read_text(encoding='utf-8-sig'))
assert selection['selected_audit_snapshot']['sha256'] == SELECTED['pdf-audit/audit-pending-round09-freeze-1450-v2.json']
assert selection['current_alternate_share_projection']['sha256'] == SELECTED['pdf-audit/candidates-r11-alt31-share.json']
sealed_path = 'pdf-audit/audit-results-freeze-1510.json'
sealed_sha = '815565100ff8959e609b223af1c64e43451b98fbb4cb1dfc83ddcd5f778c4449'
sealed = read_checked(sealed_path, sealed_sha)
assert len(sealed['results']) == len(observations)
for index, (original, current) in enumerate(zip(observations, sealed['results'])):
    if index < 48:
        assert current == original, 'Previously sealed audit changed'
        continue
    assert {k: v for k, v in current.items() if k != 'audit_history'} == {k: v for k, v in original.items() if k != 'audit_history'}, 'Selected audit observation changed'
    before = original.get('audit_history') or []
    after = current.get('audit_history') or []
    assert len(after) == len(before) + 1 and after[:-1] == before, 'Audit history is not append-only'
    expected_input = next(Path(rel).name for rel in audit_paths[1:] if original in docs[rel]['results'])
    assert after[-1].get('input_snapshot') == expected_input
    assert after[-1].get('checked_at') == sealed['updated_at']

result = {
    'checked_at': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
    'status': 'selected_frozen_inputs_pass',
    'selected_hashes': SELECTED,
    'sealed_audit': {'path': sealed_path, 'sha256': sealed_sha, 'selected_observations_unchanged_with_merge_history': True},
    'manifest_files_checked': len(manifest_files),
    'audit_union': {'results': len(observations), 'formal_complete_links': len(formal),
                    'formal_complete_unique_hashes': len({a['sha256'] for a in formal}),
                    'complete_drafts': len(drafts), 'ratings': ratings},
    'checks': ['selected SHA256', 'transitive manifest file SHA256', 'unique audit IDs and request URLs',
               'formal and draft counts separate', 'R11 current v2 and alternate share selection',
               'failed alternate does not inherit main link pages', 'old 48 observations byte-equivalent as JSON objects',
               'new 15 observations unchanged except one provenance merge history event'],
    'limit': 'Input union only; not yet a catalog or published Excel receipt.'
}
(REPO / 'coordination/selected-inputs-1510-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'ok': True, 'manifest_files': len(manifest_files), 'audits': len(observations), 'formal': len(formal), 'drafts': len(drafts)}))
