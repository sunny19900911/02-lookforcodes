from __future__ import annotations
import io,json,re,time,hashlib,urllib.request,concurrent.futures
from pathlib import Path
from datetime import datetime,timezone,timedelta
from pypdf import PdfReader
BASE=Path(r"C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017/search/round07-broad-attachments/directory/")
SOURCES=[
{"source_id":"HUBEI-ENERGY-2022","url":"https://zjt.hubei.gov.cn/zfxxgk/zc/gfxwj/202212/P020221229428659512527.pdf","directory_stage":"正式发布的2022年目录，历史收录截止2022-05存在后续日期行","publication_date":"2022-12-29"},
{"source_id":"QINGDAO-GOODHOUSING-20251121","url":"https://www.qingdao.gov.cn/zwgk/xxgk/cxjs/gkml/gwfg/202511/P020251121604645725245.pdf","directory_stage":"2025-11-21发布标准体系，附件2含CECS目录","publication_date":"2025-11-21"},
{"source_id":"XINJIANG-FRAMEWORK-DRAFT-2023","url":"https://zjt.xinjiang.gov.cn/xjzjt/c114248/202312/b86ed50a759d4d95891f4a5f2f77affe/files/%E3%80%8A%E4%BD%8F%E6%88%BF%E5%92%8C%E5%9F%8E%E4%B9%A1%E5%BB%BA%E8%AE%BE%E6%A0%87%E5%87%86%E4%BD%93%E7%B3%BB%E6%A1%86%E6%9E%B6%E3%80%8B%E4%BF%AE%E8%AE%A2%E7%89%88%E5%BE%81%E6%B1%82%E6%84%8F%E8%A7%81%E7%A8%BF.pdf","directory_stage":"2023年目录征求意见稿，不代表所列各标准为草案","publication_date":None}
]
def fetch(s):
    started=time.monotonic(); result=dict(s)
    try:
        req=urllib.request.Request(s["url"],headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=28) as response:
            content=response.read(45_000_000)
            result["final_url"]=response.url
            result["content_type"]=response.headers.get("Content-Type")
        if not content.startswith(b"%PDF-"): raise ValueError("not PDF magic; original not saved")
        reader=PdfReader(io.BytesIO(content)); pages=[]
        result["sha256"]=hashlib.sha256(content).hexdigest()
        result["bytes"]=len(content);result["pages"]=len(reader.pages)
        for index,page in enumerate(reader.pages):
            text=page.extract_text(extraction_mode="layout") or ""
            if re.search(r"CECS",text,re.I):
                lines=text.splitlines(); hits=[]
                for n,line in enumerate(lines):
                    if re.search("CECS",line,re.I):
                        hits.append({"line":n+1,"text":line.strip(),"context_before":lines[max(0,n-2):n],"context_after":lines[n+1:n+3]})
                pages.append({"pdf_page_one_based":index+1,"footer_lines":lines[-4:],"hits":hits})
        result["cecs_pages"]=pages; result["status"]="parsed_in_memory_original_not_saved"
    except Exception as exc:
        result["status"]="fetch_or_parse_failed";result["error"]=str(exc)
    result["seconds"]=round(time.monotonic()-started,2)
    print(json.dumps({"source_id":result["source_id"],"status":result["status"],"pages":result.get("pages"),"cecs_pages":len(result.get("cecs_pages",[])),"error":result.get("error")},ensure_ascii=False),flush=True)
    return result
if __name__=="__main__":
    BASE.mkdir(parents=True,exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: results=list(pool.map(fetch,SOURCES))
    payload={"checked_at":datetime.now(timezone(timedelta(hours=8))).isoformat(),"scope":"Public PDF bodies fetched into memory only; no PDF originals saved. CECS line context is metadata extraction, not standard full text.","sources":results}
    (BASE/"page-extraction.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")

