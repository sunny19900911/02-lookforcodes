import io,json,urllib.request
from pathlib import Path
import pdfplumber
BASE=Path(r"C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017/search/round08-public-expansion/directory2/")
d=json.loads((BASE/"directory-round08.json").read_text(encoding="utf-8"))
with urllib.request.urlopen(urllib.request.Request(d["source"]["source_pdf"],headers={"User-Agent":"Mozilla/5.0"}),timeout=25) as r: body=r.read()
targets={53:["[01].6.2-20"],62:["[02].1.3.1-55"],165:["[02].13.3.2-35","[02].13.3.2-36"]}
regions=[]
with pdfplumber.open(io.BytesIO(body)) as pdf:
    for page1,ids in targets.items():
        page=pdf.pages[page1-1];boxes=[];matched=[]
        for table in page.find_tables():
            rows=table.extract()
            for i,cells in enumerate(rows):
                if cells and cells[0] and cells[0].strip() in ids:
                    boxes.append(table.rows[i].bbox);matched.append(cells)
        if not boxes:raise ValueError(f"no exact target row at page{page1}")
        bbox=(max(0,min(b[0] for b in boxes)-7),max(0,min(b[1] for b in boxes)-12),min(page.width,max(b[2] for b in boxes)+7),min(page.height,max(b[3] for b in boxes)+12))
        out=BASE/f"local-only-conflict-r08-p{page1}.png"
        page.crop(bbox).to_image(resolution=160).save(out)
        regions.append({"pdf_page_one_based":page1,"crop_pdf_points":list(bbox),"source_row_ids":ids,"raw_cells":matched,"local_image":str(out),"local_only_do_not_upload":True})
(BASE/"conflict-visual-regions-r08.json").write_text(json.dumps({"regions":regions,"original_pdf_saved":False},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"regions":[{"page":x["pdf_page_one_based"],"file":x["local_image"],"bbox":x["crop_pdf_points"]} for x in regions]},ensure_ascii=False))

