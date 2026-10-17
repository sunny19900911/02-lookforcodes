import concurrent.futures, json, pathlib, subprocess
from PIL import Image, ImageDraw
from pypdf import PdfReader

ROOT = pathlib.Path(__file__).resolve().parent
TEMP = ROOT.parent / 'downloads-temp'
PAGES = {
    'AUD-PUBLIC-001': [8,9,10,11,12,50,52,96,97,99],
    'AUD-PUBLIC-002': [8,9,10,11,12,13,14,15,70,191],
    'AUD-PUBLIC-003': [4,6,34,35,36,60,61],
    'AUD-PUBLIC-004': [6,42,43],
    'R01-G3-003': [1,3,4,5,6,7,30,59,60,61],
    'R01-G4-005': [1,2,3,4,5,6,7,8,9,10,11,12],
}

def render(ident, pages):
    directory = ROOT / ident
    directory.mkdir(exist_ok=True)
    cells=[]
    for page in pages:
        path = directory / f'page-{page:03d}.png'
        if not path.exists():
            run=subprocess.run(['pdftoppm','-f',str(page),'-l',str(page),'-r','110','-singlefile','-png',str(TEMP/(ident+'.pdf')),str(path.with_suffix(''))],capture_output=True,timeout=35)
            if run.returncode: raise RuntimeError(run.stderr.decode('utf-8','replace'))
        im=Image.open(path).convert('RGB'); im.thumbnail((480,660))
        cell=Image.new('RGB',(500,700),'#dddddd');cell.paste(im,((500-im.width)//2,28))
        ImageDraw.Draw(cell).text((12,8),f'{ident} PDF {page}',fill='black');cells.append(cell)
    sheet=Image.new('RGB',(1500,700*((len(cells)+2)//3)),'white')
    for k,cell in enumerate(cells):sheet.paste(cell,((k%3)*500,(k//3)*700))
    out=directory/'supplement-contact.jpg';sheet.save(out,quality=92)
    return str(out)

def footers(ident):
    reader=PdfReader(TEMP/(ident+'.pdf'))
    cells=[]
    for i,page in enumerate(reader.pages):
        images=list(page.images)
        if not images: continue
        im=max((x.image for x in images),key=lambda x:x.width*x.height).convert('RGB')
        box=im.crop((int(im.width*.08),int(im.height*.87),int(im.width*.92),im.height))
        box.thumbnail((400,115))
        cell=Image.new('RGB',(420,145),'#eeeeee');cell.paste(box,((420-box.width)//2,25))
        ImageDraw.Draw(cell).text((10,6),f'PDF {i+1}',fill='black');cells.append(cell)
    batch_size=60
    for offset in range(0,len(cells),batch_size):
        subset=cells[offset:offset+batch_size]
        sheet=Image.new('RGB',(2100,145*((len(subset)+4)//5)),'white')
        for k,cell in enumerate(subset):sheet.paste(cell,((k%5)*420,(k//5)*145))
        path=ROOT/ident/f'footer-continuity-{offset+1:03d}.jpg';sheet.save(path,quality=95)
        print(str(path),flush=True)

def link_check():
    ident='AUD-PUBLIC-003';reader=PdfReader(TEMP/(ident+'.pdf'));results=[]
    for i,page in enumerate(reader.pages):
        for ref in page.get('/Annots',[]):
            a=ref.get_object()
            if a.get('/Subtype')!='/Link':continue
            action=a.get('/A',{});dest=a.get('/Dest') or action.get('/D')
            target=None;error=None
            try:
                if isinstance(dest,str):
                    resolved=reader.named_destinations.get(dest)
                    target=None if resolved is None else reader.get_destination_page_number(resolved)+1
                elif dest:
                    target=reader.get_page_number(dest[0].get_object())+1
            except Exception as e:error=str(e)
            results.append({'source_pdf_page':i+1,'rect':str(a.get('/Rect')),'action':str(action.get('/S')),'destination':str(dest),'target_pdf_page':target,'valid_internal_target':target is not None and 1<=target<=len(reader.pages),'error':error})
    (ROOT/ident/'link-target-evidence.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'links':len(results),'valid':sum(x['valid_internal_target'] for x in results),'toc_links':[x for x in results if x['source_pdf_page']==5]},ensure_ascii=False),flush=True)
    # Extracted short passages only, for copy accuracy comparison with rendered originals.
    for n in [5,6,34,35,36,60,61]:
        print(f'PDF {n}: '+reader.pages[n-1].extract_text()[:240],flush=True)

if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(lambda item:render(*item),PAGES.items()):print(result,flush=True)
    link_check()
    for ident in ['AUD-PUBLIC-001','AUD-PUBLIC-002']:footers(ident)
