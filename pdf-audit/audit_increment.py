"""Run a separate pending audit queue without touching the frozen canonical JSON."""
import concurrent.futures, json, pathlib, sys
import audit_pdf as audit

path=pathlib.Path(__file__).resolve().parent/'audit-pending-round03.json'
document=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'schema_version':'1.0','producer':'audit','status':'pending_merge_after_canonical_freeze','results':[]}
baseline=json.loads((path.parent/'audit-results.json').read_text(encoding='utf-8'))
done={r['candidate_id'] for r in document['results']+baseline['results']}
queue=[]
for arg in sys.argv[1:]:
    data=json.loads(pathlib.Path(arg).read_text(encoding='utf-8-sig'))
    queue.extend(c for c in (data if isinstance(data,list) else data.get('candidates',[])) if c['candidate_id'] not in done)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    for result in executor.map(audit.inspect,queue):
        document['results'].append(result);document['updated_at']=audit.NOW()
        path.write_text(json.dumps(document,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:result.get(k) for k in ['candidate_id','download_status','pages','bytes','bookmark_count','error']},ensure_ascii=False),flush=True)
