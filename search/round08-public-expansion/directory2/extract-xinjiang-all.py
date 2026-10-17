from __future__ import annotations
import io,json,re,hashlib,urllib.request,time
from pathlib import Path
from datetime import datetime,timezone,timedelta
from pypdf import PdfReader
import pdfplumber
BASE=Path(r"C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017/search/round08-public-expansion/directory2/")
PREV=Path(r"C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017/search/round07-broad-attachments/directory")
SOURCE=json.loads((PREV/"page-extraction.json").read_text(encoding="utf-8"))["sources"][2]
previous=json.loads((PREV/"directory-round07.json").read_text(encoding="utf-8"))
previous_rows={r["source_row_id"]:r for r in previous["records"] if r["source_directory_id"].startswith("XINJIANG")}
previous_pages={21,23,38,47,51,52,53}
pattern=re.compile(r"((?:T/)?CECS(?:-CBIMU|-CREA)?)(\d+)[—:\-](\d{4})")
def compact(s):return re.sub(r"\s+","",s or "").replace("∕","/").replace("／","/").replace("：",":")
def clean_name(s):return re.sub(r"\s*\n\s*","",s or "").strip()
def now():return datetime.now(timezone(timedelta(hours=8))).isoformat()
BASE.mkdir(parents=True,exist_ok=True)
start=time.monotonic()
with urllib.request.urlopen(urllib.request.Request(SOURCE["url"],headers={"User-Agent":"Mozilla/5.0"}),timeout=30) as response:
    body=response.read(45_000_000); final_url=response.url;content_type=response.headers.get("Content-Type")
if not body.startswith(b"%PDF-"):raise ValueError("not PDF")
reader=PdfReader(io.BytesIO(body))
cecs_pages=[];page_hits=[];front_matter=[]
for index,page in enumerate(reader.pages):
    txt=page.extract_text(extraction_mode="layout") or ""
    if index<7:front_matter.append({"pdf_page_one_based":index+1,"text":txt[:700]})
    lines=txt.splitlines()
    hits=[line.strip() for line in lines if "CECS" in line]
    if hits:
        cecs_pages.append(index+1);page_hits.append({"pdf_page_one_based":index+1,"cecs_line_count":len(hits),"footer_lines":lines[-4:]})
print(json.dumps({"pdf_pages":len(reader.pages),"cecs_hit_pages":len(cecs_pages),"seconds":round(time.monotonic()-start,2)},ensure_ascii=False),flush=True)
raw_rows=[];records=[];gaps=[];links=[];parse_issues=[];seen=set()
with pdfplumber.open(io.BytesIO(body)) as pdf:
    for page1 in cecs_pages:
        page=pdf.pages[page1-1]
        footer=(page.crop((0,page.height*.92,page.width,page.height)).extract_text() or "").strip()
        printed=int(footer) if footer.isdigit() else None
        table_count=0;valid_at_page=0
        for ti,table in enumerate(page.extract_tables(),1):
            table_count+=1
            for ri,cells in enumerate(table,1):
                if not any(cell and "CECS" in cell for cell in cells):continue
                raw={"source_directory_id":"XINJIANG-FRAMEWORK-DRAFT-2023","source_pdf":SOURCE["url"],"pdf_page_one_based":page1,"source_printed_page":printed,"footer_text":footer,"table_index":ti,"row_index_in_table":ri,"raw_cells":cells}
                raw_rows.append(raw)
                ci=next((i for i,c in enumerate(cells) if c and "CECS" in c),None)
                if ci is None:continue
                rawnum=cells[ci];numbertext=compact(rawnum);matches=list(pattern.finditer(numbertext))
                rowid=clean_name(cells[0])
                if not rowid.startswith("["):
                    gaps.append(dict(raw,reason="不是可确认的目录标准行或row_id不完整；保留原格，不当新标准"))
                    continue
                name=clean_name(cells[1]) if len(cells)>1 else None
                if not matches:
                    gaps.append(dict(raw,source_row_id=rowid,name=name,reason="编号或四位年份缺失/不清楚，不补猜，不计完整编号版本"))
                    continue
                if ci!=2:parse_issues.append(dict(raw,reason="标准号不在预期第3列，请人工核对名称列；仍保留原格"))
                for match in matches:
                    fam,num,year=match.groups();num=str(int(num));key=f"{fam} {num}-{year}"
                    source_row_key=(rowid,key)
                    if source_row_key in seen:
                        links.append({"source_row_id":rowid,"standard_number":key,"pdf_page_one_based":page1,"note":"同源同row_id重复抽取，不重复计记录"});continue
                    seen.add(source_row_key)
                    source_id=f"XINJIANG-FRAMEWORK-DRAFT-2023:row-{rowid}"
                    stage_raw={"current_column":cells[ci+1] if len(cells)>ci+1 else None,"drafting_column":cells[ci+2] if len(cells)>ci+2 else None,"proposed_column":cells[ci+3] if len(cells)>ci+3 else None}
                    record={"standard_number":key,"number":num,"year":year,"standard_family":fam,"name":name,"name_status":"政府目录草案原文，未逐一核对各标准正式封面；不纠正目录原写法","source_id":source_id,"source_directory_id":"XINJIANG-FRAMEWORK-DRAFT-2023","source_row_id":rowid,"source_pdf":SOURCE["url"],"source_page":None,"page":page1,"page_kind":"PDF物理页1-based，直接逐页枚举，不按偏移推算","pdf_page_one_based":page1,"source_printed_page":printed,"printed_page_evidence":footer,"table_index":ti,"row_index_in_table":ri,"directory_stage":"2023年《住房和城乡建设标准体系框架》修订版征求意见稿，目录为草案，不表示每项标准为草案","source_publication_date":None,"historical_status_raw":stage_raw,"status":"未知（仅2023目录草案历史收录，未核2026现行性）","raw_standard_number":rawnum,"raw_cells":cells,"metadata_evidence":[{"source_pdf":SOURCE["url"],"pdf_page_one_based":page1,"source_printed_page":printed,"source_row_id":rowid,"evidence_type":"直接政府PDF原格"}],"download_url":None,"download_status":"标准体系目录元数据，不是该标准全文下载","seen_in_round07":rowid in previous_rows,"seen_on_round07_page":page1 in previous_pages}
                    records.append(record);valid_at_page+=1
        if not table_count and page1 not in [13,186]:
            parse_issues.append({"pdf_page_one_based":page1,"reason":"文本发现CECS但默认表格提取没有表格，未默认为已完成"})
        print(json.dumps({"page":page1,"valid_numbered_rows":valid_at_page,"raw_cecs_rows":len(raw_rows)},ensure_ascii=False),flush=True)
old_links=[{"standard_number":r["standard_number"],"source_id":r["source_id"],"source_row_id":r["source_row_id"],"pdf_page_one_based":r["pdf_page_one_based"],"previous_file":str(PREV/"directory-round07.json"),"handling":"同源原row_id已在R07列示，本轮只作重核链接，不重复投递新增"} for r in records if r["seen_in_round07"]]
new_records=[r for r in records if not r["seen_in_round07"]]
previous_versions={(r["number"],r["year"]) for r in previous_rows.values()}
all_versions={(r["number"],r["year"]) for r in records}
conflicts=[]
for version in sorted(all_versions):
    items=[r for r in records if (r["number"],r["year"])==version]
    if len({r["name"] for r in items})>1:
        conflicts.append({"number":version[0],"year":version[1],"type":"目录内部同编号年份多名称，不选择哪条为正式名称","variants":[{"standard_number":r["standard_number"],"name":r["name"],"pdf_page_one_based":r["page"],"source_printed_page":r["source_printed_page"],"source_row_id":r["source_row_id"],"raw_cells":r["raw_cells"]} for r in items]})
        for r in items:r["directory_number_name_conflict"]=True
stats={"pdf_physical_pages_scanned":len(reader.pages),"cecs_text_hit_pages":len(cecs_pages),"raw_cecs_table_rows":len(raw_rows),"numbered_source_records_all":len(records),"unique_number_year_all":len(all_versions),"new_source_records_vs_round07":len(new_records),"unique_number_year_in_new_source_records":len({(r["number"],r["year"]) for r in new_records}),"new_unique_number_year_vs_round07":len(all_versions-previous_versions),"round07_link_records":len(old_links),"all_new_have_direct_physical_page":all(r["page"]>0 for r in new_records),"raw_gap_rows":len(gaps),"parse_issue_count":len(parse_issues),"directory_number_name_conflict_count":len(conflicts),"standard_full_pdf_added":0}
result={"schema_version":1,"checked_at":now(),"producer":"search-round08-directory2","scope":"新疆186页PDF全部页文本已内存扫描，对命中CECS的43页作默认表格提取；有CECS但未能定位标准行/完整年份者记gap，不宣称人工逐186页核完或全网穷尽。","coverage":stats,"source":{"source_id":"XINJIANG-FRAMEWORK-DRAFT-2023","source_pdf":SOURCE["url"],"final_url":final_url,"content_type":content_type,"sha256":hashlib.sha256(body).hexdigest(),"bytes":len(body),"pdf_pages":len(reader.pages),"directory_stage":"政府发布的2023年框架修订版征求意见稿附件；目录草案不等于各标准草案","source_publication_date":None,"original_saved":False,"screenshot_saved":False},"records":new_records,"round07_reverified_links":old_links,"gaps":gaps,"parse_issues":parse_issues,"page_scan":page_hits,"notes":["每条新增都有直接PDF物理页page、source_id、source_row_id与raw_cells。","旧round07及freeze只读，未修改。","标准编号原年号不静默校正；缺年份不猜；historical_status仅保存目录格。","原PDF与截图均未落盘/上传。","raw-cells.json只含CECS命中目录行，不含PDF二进制。"]}
(BASE/"directory-round08.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
(BASE/"raw-cells.json").write_text(json.dumps({"checked_at":result["checked_at"],"rows":raw_rows},ensure_ascii=False,indent=2),encoding="utf-8")
(BASE/"directory-conflicts.json").write_text(json.dumps({"checked_at":result["checked_at"],"scope":"政府目录内部原文矛盾，不能静默归并或当各标准已核正式名","conflicts":conflicts},ensure_ascii=False,indent=2),encoding="utf-8")
(BASE/"front-matter-evidence.json").write_text(json.dumps({"checked_at":result["checked_at"],"scope":"只为目录标题/草案状态定位，非完整PDF","pages":front_matter},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(stats,ensure_ascii=False),flush=True)

