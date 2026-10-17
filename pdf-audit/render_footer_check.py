import concurrent.futures, pathlib, subprocess, sys
from PIL import Image, ImageDraw

ROOT=pathlib.Path(__file__).resolve().parent
def run(ident):
    directory=ROOT/ident/'continuity-render';directory.mkdir(exist_ok=True)
    result=subprocess.run(['pdftoppm','-r','72','-png',str(ROOT.parent/'downloads-temp'/(ident+'.pdf')),str(directory/'page')],capture_output=True,timeout=100)
    (directory/'render-errors.txt').write_text(result.stderr.decode('utf-8','replace'),encoding='utf-8')
    cells=[]
    for path in sorted(directory.glob('page-*.png')):
        im=Image.open(path).convert('RGB');box=im.crop((0,int(im.height*.88),im.width,im.height));box.thumbnail((400,100))
        cell=Image.new('RGB',(420,130),'#eeeeee');cell.paste(box,((420-box.width)//2,25));ImageDraw.Draw(cell).text((10,6),path.stem,fill='black');cells.append(cell)
    for offset in range(0,len(cells),60):
        subset=cells[offset:offset+60];sheet=Image.new('RGB',(2100,130*((len(subset)+4)//5)),'white')
        for k,cell in enumerate(subset):sheet.paste(cell,((k%5)*420,(k//5)*130))
        out=ROOT/ident/f'rendered-footers-{offset+1:03d}.jpg';sheet.save(out,quality=95);print(str(out),flush=True)
    print(ident, result.returncode,len(cells),flush=True)

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    list(executor.map(run,sys.argv[1:]))
