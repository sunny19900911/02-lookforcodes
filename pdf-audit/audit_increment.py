"""Run a separate pending audit queue without touching the frozen canonical JSON."""
import argparse, concurrent.futures, json, pathlib, sys
import audit_pdf as audit

parser=argparse.ArgumentParser()
parser.add_argument('--pending-file',default='audit-pending-round03.json')
parser.add_argument('candidate_files',nargs='+')
args=parser.parse_args()
name=pathlib.PurePath(args.pending_file)
if len(name.parts)!=1 or not str(name).startswith('audit-pending-') or name.suffix!='.json':
    parser.error('--pending-file must be an audit-pending-*.json basename inside pdf-audit')
path=pathlib.Path(__file__).resolve().parent/name
document=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'schema_version':'1.0','producer':'audit','status':'pending_merge_after_canonical_freeze','results':[]}
baseline=json.loads((path.parent/'audit-results.json').read_text(encoding='utf-8'))
done={r['candidate_id'] for r in document['results']+baseline['results']}
queue=[]
for arg in args.candidate_files:
    data=json.loads(pathlib.Path(arg).read_text(encoding='utf-8-sig'))
    for candidate in (data if isinstance(data,list) else data.get('candidates',[])):
        if candidate['candidate_id'] not in done:
            queue.append(candidate)
            done.add(candidate['candidate_id'])
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    for result in executor.map(audit.inspect,queue):
        if result.get('http_status')==403:
            result['download_status']='本次HTTP403访问受限，是否需登录未知'
        document['results'].append(result);document['updated_at']=audit.NOW()
        path.write_text(json.dumps(document,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:result.get(k) for k in ['candidate_id','download_status','pages','bytes','bookmark_count','error']},ensure_ascii=False),flush=True)
