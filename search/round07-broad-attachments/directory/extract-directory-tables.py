import io,json,re,urllib.request
from pathlib import Path
from datetime import datetime,timezone,timedelta
import pdfplumber
BASE=Path(r"C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017/search/round07-broad-attachments/directory/")
sources=json.loads((BASE/"page-extraction.json").read_text(encoding="utf-8"))["sources"]
allrows=[];failures=[]
for source in [sources[0],sources[2]]:
    selected=[p["pdf_page_one_based"] for p in source["cecs_pages"]] if source["source_id"].startswith("HUBEI") else [21,23,38,47,51,52,53]
    try:
        with urllib.request.urlopen(urllib.request.Request(source["url"],headers={"User-Agent":"Mozilla/5.0"}),timeout=25) as r: body=r.read()
        with pdfplumber.open(io.BytesIO(body)) as pdf:
            for page1 in selected:
                page=pdf.pages[page1-1]
                footer=page.crop((0,page.height*0.92,page.width,page.height)).extract_text() or ""
                tables=page.extract_tables()
                for table in tables:
                    for row in table:
                        if any(cell and "CECS" in cell for cell in row):
                            allrows.append({"source_id":source["source_id"],"source_pdf":source["url"],"pdf_page_one_based":page1,"footer_text":footer,"raw_cells":row})
                if source["source_id"].startswith("HUBEI") and page1 in [20,21,24,37,38]:
                    page.to_image(resolution=90).save(BASE/f"local-qa-hubei-p{page1}.png")
        print(json.dumps({"source":source["source_id"],"selected_pages":selected,"cumulative_cecs_rows":len(allrows)},ensure_ascii=False),flush=True)
    except Exception as e: failures.append({"source":source["source_id"],"error":str(e)})
out={"checked_at":datetime.now(timezone(timedelta(hours=8))).isoformat(),"note":"原PDF仅内存读取，原件未落盘；local-qa PNG仅本地目视，不上传。table rows是目录元数据。","rows":allrows,"failures":failures}
(BASE/"table-rows.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"rows":len(allrows),"failures":failures},ensure_ascii=False),flush=True)

