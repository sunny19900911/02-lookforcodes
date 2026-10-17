import concurrent.futures, datetime, hashlib, json, os, pathlib, re, subprocess, sys, time, urllib.request, urllib.error
from pypdf import PdfReader

BASE=pathlib.Path(__file__).resolve().parent.parent
OUT=BASE/'pdf-audit'; TEMP=BASE/'downloads-temp'
OUT.mkdir(parents=True,exist_ok=True); TEMP.mkdir(parents=True,exist_ok=True)
NOW=lambda:datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
MAX_BYTES=95*1024*1024
RULES={
 'A':'版本匹配、完整性证据闭环、抽查清晰，文本搜索复制正常且原生书签目标有效；优先推荐',
 'B':'版本匹配、完整性证据闭环、抽查清晰；缺书签或文本搜索等导航便利性不足，可用',
 'C':'可下载可解析，但完整性或版本尚未闭环；不进入已核验完整PDF清单',
 'D':'样章/预览/损坏/版本不符/访问受限或网络失败；不作为可用完整PDF推荐'
}

def inspect(c):
    ident=c['candidate_id']; url=c.get('download_url') or c.get('requested_url') or c.get('direct_url'); folder=OUT/ident; folder.mkdir(exist_ok=True)
    r={**c,'requested_url':url,'checked_at':NOW(),'audit_id':ident,'download_status':'本次网络失败未验证','recommendation':'D','recommendation_reason':'尚未完成下载与核验','evidence_paths':[],'audit_rules_version':'2026-10-17.2','complete_pdf':False,'version_verified':False,'standard_key':c.get('standard_key') or c.get('standard_number')}
    if not url:
      r.update(download_status='仅详情页线索，下载href待解析',recommendation_reason='没有可实际GET的候选直链；不猜附件URL')
      return r
    p=TEMP/(ident+'.pdf'); started=time.monotonic()
    try:
      if c.get('reuse_download') and p.exists():
        r['download_checked_at']=c.get('download_checked_at') or c.get('checked_at')
        r['local_reinspection_at']=NOW();r.pop('error',None)
      else:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; CECS-link-audit/1.0)','Accept':'application/pdf,*/*;q=0.5'})
        with urllib.request.urlopen(req,timeout=18) as resp:
          r.update(http_status=resp.status,final_url=resp.geturl(),content_type=resp.headers.get('Content-Type'),content_length_header=resp.headers.get('Content-Length'))
          size=0
          with p.open('wb') as f:
            while True:
              if time.monotonic()-started>130:raise TimeoutError('GET total budget 130 seconds exceeded')
              b=resp.read(256*1024)
              if not b:break
              size+=len(b)
              if size>MAX_BYTES:raise ValueError('download exceeds 95 MiB limit')
              f.write(b)
      r['bytes']=p.stat().st_size
      declared=r.get('content_length_header')
      r['transfer_size_matches_header']=(r['bytes']==int(declared)) if str(declared or '').isdigit() else None
      if r['transfer_size_matches_header'] is False:
        r.setdefault('transfer_warnings',[]).append('实际接收字节与Content-Length不同，须排查截断或传输编码')
      header=p.open('rb').read(1024)
      r['pdf_header_valid']=bool(re.search(br'%PDF-\d\.\d',header))
      if not r['pdf_header_valid']:
        data=p.read_bytes()[:3000].decode('utf-8','replace')
        r.update(download_status='HTML伪PDF或非PDF响应',error=data[:350],recommendation_reason='实际GET响应没有PDF文件头')
        if re.search(r'login|登录|signin',data,re.I):r['download_status']='需登录'
        return r
      r['sha256']=hashlib.sha256(p.read_bytes()).hexdigest(); r['local_path']=str(p)
      reader=PdfReader(str(p),strict=True)
      r['encrypted']=reader.is_encrypted
      enc=reader.trailer.get('/Encrypt')
      r['encryption_permissions']=int(enc.get_object().get('/P',0)) if enc else None
      if reader.is_encrypted and reader.decrypt('')==0:
        r.update(download_status='加密需密码',recommendation_reason='空密码不能打开，未尝试绕过')
        return r
      n=len(reader.pages); r['pages']=n
      r['pdf_parse']='页面树可遍历；已尝试逐页文本提取。图像/字体/内容流可读性另以渲染与目视记录判断'; r['eof_marker_present']=b'%%EOF' in p.read_bytes()[-2048:]
      texts=[]; links=[]; geometry=[]
      for i,page in enumerate(reader.pages):
        try:t=page.extract_text() or ''
        except Exception as e:t='';r.setdefault('page_text_errors',[]).append({'page':i+1,'error':str(e)})
        texts.append(t)
        geometry.append({'page':i+1,'rotation':int(page.get('/Rotate',0)),'media':[float(x) for x in page.mediabox],'crop':[float(x) for x in page.cropbox]})
        for ref in page.get('/Annots',[]):
          a=ref.get_object()
          if a.get('/Subtype')=='/Link':
            act=a.get('/A',{}); links.append({'page':i+1,'action':str(act.get('/S','')),'uri':str(act.get('/URI','')),'dest':str(a.get('/Dest') or act.get('/D',''))[:180],'rect':str(a.get('/Rect',''))})
      r['text_pages']=sum(bool(x.strip()) for x in texts)
      r['text_characters']=sum(len(x) for x in texts)
      r['cjk_characters']=sum(len(re.findall(r'[\u4e00-\u9fff]',x)) for x in texts)
      r['text_layer']=r['text_pages']>0
      r['body_searchable']=None
      r['body_text_layer']='待正文中文与图像对照；少量导航文字或乱码不能证明正文可搜索'
      r['searchable']='待抽查中文抽取准确性' if r['text_layer'] else '无文本层，不能直接搜索复制'
      outline=[]
      def visit(xs):
        for item in xs:
          if isinstance(item,list):visit(item)
          else:
            try:page=reader.get_destination_page_number(item); valid=page is not None and 0<=page<n
            except Exception:page=None;valid=False
            outline.append({'title':str(item.get('/Title','')),'page':None if page is None else page+1,'valid_target':valid})
      try:visit(reader.outline)
      except Exception as e:r['outline_error']=type(e).__name__+': '+str(e)
      r['bookmark_count']=len(outline); r['bookmark_valid_target_count']=sum(x['valid_target'] for x in outline)
      r['bookmark_navigation']='Outline结构异常，不能使用' if r.get('outline_error') else ('全部目标有效' if outline and all(x['valid_target'] for x in outline) else ('无原生书签' if not outline else '存在无效/未解析目标'))
      r['clickable_toc']='待人工核对目录页Link注释' if links else '未发现任何Link注释；目录不可点击'
      r['link_annotation_count']=len(links)
      r['rotation_summary']={str(x):sum(y['rotation']==x for y in geometry) for x in sorted(set(y['rotation'] for y in geometry))}
      r['cropbox_diff_pages']=[x['page'] for x in geometry if x['media']!=x['crop']]
      cover='\n'.join(texts[:min(5,n)])
      tail='\n'.join(texts[max(0,n-3):])
      r['version_match']='待封面人工核验'
      r['completeness']='可下载，完整性待核'
      r['clarity']='待封面/目录/正文/表图/末页目视抽查'
      r['download_status']='已实测GET可解析PDF；完整性待核'
      r['recommendation']='C';r['recommendation_reason']='实际GET和全部页面解析通过，等待版本、目录末项与终页、抽样图像核验'
      sample_idx=sorted(set([0,min(4,n-1),min(6,n-1),n//2,max(0,n-3),n-1]))
      detail={'audit_id':ident,'checked_at':r['checked_at'],'outline':outline,'links':links,'geometry':geometry,'text_checks':[{'page':i+1,'chars':len(t),'cjk':len(re.findall(r'[\u4e00-\u9fff]',t)),'excerpt':t[:900] if i<8 or i>=n-3 else t[:200]} for i,t in enumerate(texts)],'sample_page_numbers':[i+1 for i in sample_idx]}
      dpath=folder/'parse-evidence.json';dpath.write_text(json.dumps(detail,ensure_ascii=False,indent=2),encoding='utf-8');r['evidence_paths'].append(str(dpath))
      for i in sample_idx:
        prefix=folder/('page-%03d'%(i+1))
        cmd=['pdftoppm','-f',str(i+1),'-l',str(i+1),'-r','110','-singlefile','-png',str(p),str(prefix)]
        cp=subprocess.run(cmd,capture_output=True,timeout=35)
        if cp.returncode==0:r['evidence_paths'].append(str(prefix)+'.png')
        else:r.setdefault('render_errors',[]).append({'page':i+1,'error':cp.stderr.decode('utf8','replace')[:400]})
      try:
        from PIL import Image,ImageOps,ImageDraw
        thumbs=[]
        for i in sample_idx:
          ip=folder/('page-%03d.png'%(i+1))
          if not ip.exists():continue
          im=Image.open(ip).convert('RGB');im.thumbnail((480,660))
          cell=Image.new('RGB',(500,700),'#dddddd');cell.paste(im,((500-im.width)//2,28));ImageDraw.Draw(cell).text((12,8),f'{ident} / PDF page {i+1}',fill='black');thumbs.append(cell)
        sheet=Image.new('RGB',(1500,700*((len(thumbs)+2)//3)),'white')
        for k,im in enumerate(thumbs):sheet.paste(im,((k%3)*500,(k//3)*700))
        sheetpath=folder/'contact-sheet.jpg';sheet.save(sheetpath,quality=91);r['evidence_paths'].append(str(sheetpath));r['contact_sheet']=str(sheetpath)
      except Exception as e:r['contact_sheet_error']=str(e)
    except Exception as e:
      r['error']=type(e).__name__+': '+str(e);r['recommendation_reason']='实际GET/解析未成功；不推断永久失效'
      if r.get('pdf_header_valid'):r['download_status']='PDF已取得，但解析异常待核（非网络失败）'
      if isinstance(e,urllib.error.HTTPError):
        r['http_status']=e.code
        r['download_status']='需登录或访问受限' if e.code in [401,403] else ('失效HTTP404' if e.code==404 else 'HTTP错误未获得PDF')
    r['elapsed_seconds']=round(time.monotonic()-started,2)
    return r

def main():
    queue=[]
    for arg in sys.argv[1:]:
      x=json.loads(pathlib.Path(arg).read_text(encoding='utf-8-sig'));queue+=x if isinstance(x,list) else x.get('candidates',[])
    path=OUT/'audit-results.json'
    old=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'schema_version':'1.0','producer':'audit','rules':RULES,'results':[]}
    done={x['candidate_id'] for x in old['results']};queue=[x for x in queue if x['candidate_id'] not in done]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
      jobs={ex.submit(inspect,c):c for c in queue}
      for f in concurrent.futures.as_completed(jobs):
        try:result=f.result()
        except Exception as e:result={**jobs[f],'checked_at':NOW(),'download_status':'审查脚本异常，需重核','recommendation':'D','complete_pdf':False,'version_verified':False,'error':type(e).__name__+': '+str(e)}
        old['results'].append(result);old['updated_at']=NOW();path.write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:result.get(k) for k in ['candidate_id','download_status','pages','bytes','bookmark_count','error']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
