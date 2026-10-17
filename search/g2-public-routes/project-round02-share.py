from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import urlsplit,parse_qsl,urlencode,urlunsplit
import json,hashlib,copy,re

base=Path(r'C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017')
folder=base/'search/g2-public-routes'
source=folder/'round02-candidates.json'
raw=source.read_bytes()
old_hash=hashlib.sha256(raw).hexdigest()
data=json.loads(raw.decode('utf-8-sig'))
share=copy.deepcopy(data)
now=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
target=next(r for r in share['candidates'] if r['candidate_id']=='G2-R02-117-2017-315368-ZIP')
u=urlsplit(target['redirect_entry'])
kept=[(k,v) for k,v in parse_qsl(u.query) if k.lower() not in {'uhash','token','signature','sign','auth','authorization','access_token','key','password','secret'}]
assert len(kept)<len(parse_qsl(u.query)), 'Expected a transient public parameter'
stable=urlunsplit((u.scheme,u.netloc,u.path,urlencode(kept),''))
target['redirect_entry']=None
target['stable_redirect_route_without_transient_parameters']=stable
target['stable_redirect_route_verification']='仅从当时公开跳转入口删除瞬时参数所得的路线结构；去参数后未访问、未验证，不是可用下载URL。'
target['redirect_entry_redaction']='分享投影移除了公开下载脚本生成的瞬时地址值；原始冻结记录仅本地保留。'
share['share_projection']={
    'source_id':'SEARCH-G2-R02-SHARE-PROJECTION-20261017',
    'prepared_at':now,
    'original_read_only_path':'search/g2-public-routes/round02-candidates.json',
    'original_sha256':old_hash,
    'purpose':'用于external分享；不修改原冻结文件或旧封版，不增加候选、不重复计数。',
    'redactions':[{'candidate_id':'G2-R02-117-2017-315368-ZIP','field_path':'candidates[1].redirect_entry','action':'原始瞬时URL值置null，另留稳定路由结构及未验证说明。','parameter_kind':'公开下载瞬时校验参数；仅移除，不保留值。'}],
    'preserved':'4个候选ID、来源页、实际观察的ZIP最终地址、旧时间戳、未成功GET事实及全部元数据均保留。',
    'stable_route_boundary':'去参数路由不作为已验下载；117-2017仍是ZIP候选，内部PDF未知，不是完整PDF。'
}
out=folder/'round02-candidates-share.json'
assert not out.exists(), 'Share projection is immutable once emitted'
serialized=json.dumps(share,ensure_ascii=False,indent=2)+'\n'
assert not re.search(r'(?i)(?:[?&]|%26)(?:uhash|token|signature|access_token|password|secret)=',serialized)
out.write_text(serialized,encoding='utf-8')
assert source.read_bytes()==raw
assert [(r['candidate_id'],r['download_url']) for r in data['candidates']]==[(r['candidate_id'],r['download_url']) for r in share['candidates']]
frozen=json.loads((base/'search/freeze-inputs-1320.json').read_text(encoding='utf-8-sig'))
entry=next(x for x in frozen['files'] if x['path']=='search/g2-public-routes/round02-candidates.json')
assert old_hash==entry['sha256']
mf=base/'search/freeze-inputs-g2-round02-share-1350.json'
assert not mf.exists()
manifest={
    'producer':'search','checkpoint':'13:50-g2-round02-share-projection','checked_at':now,'frozen':True,
    'source_id':'SEARCH-G2-R02-SHARE-MANIFEST-20261017',
    'original_frozen_input_unchanged':True,
    'input_file_count':1,
    'sharing_selection':'此文件仅替代external分享选择，不替代本地原始证据；旧round02-candidates.json不分享、不重计。',
    'note':'无PDF/PNG/HTML/公开下载瞬时参数值；稳定去参数地址未访问，不能当作已验PDF/ZIP。',
    'files':[{'path':'search/g2-public-routes/round02-candidates-share.json','sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size}]
}
mf.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'manifest':str(mf),'manifest_sha256':hashlib.sha256(mf.read_bytes()).hexdigest(),'share_path':str(out),'share_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'candidate_count':len(share['candidates']),'original_frozen_input_unchanged':True},ensure_ascii=False))
