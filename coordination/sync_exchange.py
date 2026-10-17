"""Controller-only allowlisted sync. Never copy PDFs, page images or raw web responses."""
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil

REPO = Path(__file__).resolve().parents[1]
OUTPUT = REPO.parent
ALLOWED = {'.json', '.jsonl', '.md', '.xlsx', '.py', '.mjs', '.ps1'}
SECRET = re.compile(r'(?:sk-[A-Za-z0-9_-]{24,}|gh[pousr]_[A-Za-z0-9]{24,}|github_pat_[A-Za-z0-9_]{24,})')
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
copied, unchanged, skipped = [], [], []
sources = []
for folder in ('catalog', 'search', 'pdf-audit'):
    base = OUTPUT / folder
    if base.exists():
        sources.extend(p for p in base.iterdir() if p.is_file())
for folder in ('baseline-external-routes', 'g2-public-routes'):
    base = OUTPUT / 'search' / folder
    if base.exists():
        sources.extend(p for p in base.iterdir() if p.is_file())
authority = OUTPUT / 'search' / 'master-authority'
if authority.exists():
    sources.extend(authority.glob('*.json'))
    sources.extend(authority.glob('*.py'))
    sources.extend(authority.glob('*.md'))
    sources.extend((authority / 'history').glob('*.json'))
for src in sorted(sources):
    rel = src.relative_to(OUTPUT)
    if src.suffix.lower() not in ALLOWED or src.name.startswith('web-') or src.is_symlink():
        skipped.append({'path': str(rel), 'reason': 'outside metadata allowlist'})
        continue
    if src.stat().st_size > 20 * 1024 * 1024:
        raise ValueError(f'Unexpected metadata size, review required: {rel}')
    data = src.read_bytes()
    if src.suffix.lower() != '.xlsx' and SECRET.search(data.decode('utf-8', errors='replace')):
        raise ValueError(f'Potential credential pattern; refusing copy: {rel}')
    # Validate structured files before updating the exchange copy. An in-progress
    # writer or truncated JSON fails locally; no partial snapshot is published.
    if src.suffix.lower() == '.json':
        json.loads(data.decode('utf-8-sig'))
    if src.suffix.lower() == '.jsonl':
        for line in data.decode('utf-8-sig').splitlines():
            if line.strip():
                json.loads(line)
    dst = REPO / rel
    if dst.exists() and dst.read_bytes() == data:
        unchanged.append(rel.as_posix())
        continue
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    copied.append({'path': rel.as_posix(), 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
manifest = {'checked_at': now, 'copied': copied, 'unchanged': unchanged, 'skipped': skipped,
            'excluded': 'PDF originals, page images, downloaded documents, raw HTML/headers/web tool responses, credentials, unrelated files',
            'version_history': 'Git commits preserve prior exchange copies; source evidence and change logs remain append-only.'}
(REPO / 'coordination' / 'sync-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'copied': len(copied), 'unchanged': len(unchanged), 'skipped': len(skipped)}))
