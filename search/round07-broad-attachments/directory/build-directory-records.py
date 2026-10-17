import json,re
from pathlib import Path
from datetime import datetime,timezone,timedelta
BASE=Path(r"C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017/search/round07-broad-attachments/directory/")
tabledata=json.loads((BASE/"table-rows.json").read_text(encoding="utf-8"))
previous_path=BASE.parents[1]/"baseline-external-routes"/"directory-round02.json"
previous=json.loads(previous_path.read_text(encoding="utf-8"))
previous_by_key={x["standard_number"]:x for x in previous["records"]}
previous_keys=set(previous_by_key)
records=[];gaps=[];seen=set()
for row in tabledata["rows"]:
    hb=row["source_id"].startswith("HUBEI")
    cells=row["raw_cells"]; ni=1 if hb else 2
    if len(cells)<=ni or cells[ni] is None: continue
    original=cells[ni]
    raw=re.sub(r"\s+","",original).replace("∕","/").replace("／","/")
    match=re.fullmatch(r"((?:T/)?CECS(?:-CBIMU)?)(\d+)[—:-](\d{4})",raw)
    if not match:
        if "CECS" in raw and raw not in ["CECS","T/CECS"]:
            gaps.append(dict(row,reason="编号或年份不完整/格式不清楚，不能补猜"))
        continue
    fam,num,year=match.groups();num=str(int(num));key=f"{fam} {num}-{year}"
    sourcekey=(row["source_id"],cells[0])
    if sourcekey in seen: continue
    seen.add(sourcekey)
    title=(cells[2] if hb else cells[1]) or ""
    name=re.sub(r"\s*\n\s*","",title).strip()
    partial=hb and cells[0]=="3.1.2-61"
    if partial:
        # Physical PDF pages 20 and 21 were both visually inspected.
        name += "料选用标准"
    record={
        "standard_number":key,"number":num,"year":year,"standard_family":fam,
        "name":name,"name_status":"目录原文；正式封面名尚未逐条核对" if not partial else "目录原名跨PDF物理20/21页，已目视相邻原格拼接；未逐条核正式封面",
        "source_id":row["source_id"]+":row-"+cells[0],"source_directory_id":row["source_id"],"source_row_id":cells[0],
        "source_page":"https://zjt.hubei.gov.cn/zfxxgk/zc/zcjd/202212/t20221229_4469403.shtml" if hb else None,
        "source_pdf":row["source_pdf"],"page":row["pdf_page_one_based"],"page_kind":"PDF物理页（1-based），直接逐页解析得到，未作偏移推算",
        "pdf_page_one_based":row["pdf_page_one_based"],"source_printed_page":int(row["footer_text"]) if row["footer_text"].isdigit() else None,
        "printed_page_evidence":row["footer_text"],"directory_stage":"2022年发布目录，前言称收录截止2022-05，包含晚于截止日期行" if hb else "2023年框架目录修订版征求意见稿；不是各标准草案",
        "source_publication_date":"2022-12-29" if hb else None,
        "historical_status_raw":cells[4] if hb else {"current_column":cells[3],"drafting_column":cells[4],"proposed_column":cells[5]},
        "status":"未知（仅历史目录证据，未核2026现行性）",
        "standard_version_stage":"目录列示已编号标准；未据目录草案状态推断本标准为草案",
        "date_cell_raw":cells[3] if hb else None,"date_cell_note":"原目录实施日期/任务下达日期格，不作为已核法定实施日" if hb else None,
        "raw_standard_number":original,"raw_cells":cells,"download_url":None,"download_status":"目录元数据，不是规范全文",
        "evidence_type":"原文事实（直接政府PDF表格解析）",
        "check_method":"匿名GET原PDF只读入内存；pdfplumber表格解析；湖北PDF物理20/21/38页额外目视",
        "page_image_visually_checked":hb and row["pdf_page_one_based"] in [20,21,38],
        "seen_in_round02":key in previous_keys
    }
    records.append(record)
    if partial:
        record["continuation_pdf_page_one_based"]=21
        record["cross_page_name_evidence"]=["物理20页末行：民用建筑绿色装修设计材", "物理21页首行：料选用标准；两页均已目视"]
corrections=[]
def comparable(s):return re.sub(r"[\s\-—－]+","",s)
for record in records:
    old=previous_by_key.get(record["standard_number"])
    if old and comparable(old["name"])!=comparable(record["name"]):
        corrections.append({"standard_number":record["standard_number"],"old_file_read_only":str(previous_path),"old_name":old["name"],"new_direct_pdf_name":record["name"],"source_pdf":record["source_pdf"],"pdf_page_one_based":record["pdf_page_one_based"],"source_printed_page":record["source_printed_page"],"source_row_id":record["source_row_id"],"reason":"直接PDF原格与前轮搜索索引解析不一致，catalog应保留更正记录并优先直接原件依据；未改冻结文件"})
stats={"record_count":len(records),"unique_number_year_count":len({r["standard_number"] for r in records}),"hubei_record_count":sum(r["source_directory_id"].startswith("HUBEI") for r in records),"xinjiang_record_count":sum(r["source_directory_id"].startswith("XINJIANG") for r in records),"all_records_have_physical_page":all(isinstance(r["page"],int) and r["page"]>0 for r in records),"not_in_round02_unique_count":len({r["standard_number"] for r in records}-previous_keys),"round02_name_corrections":len(corrections),"full_standard_pdf_count_added":0}
output={"schema_version":1,"checked_at":datetime.now(timezone(timedelta(hours=8))).isoformat(),"producer":"search-directory-round07","scope":"直接政府PDF目录首批补页。湖北抽取所有本轮检测到的CECS表格页；新疆只处理21/23/38/47/51/52/53物理页，其余尚未审完。不认定全目录无漏项。","coverage":stats,"records":records,"gaps":gaps+[{"source_id":"QINGDAO-GOODHOUSING-20251121","reason":"本轮匿名GET TLS UNEXPECTED_EOF；未新增任何无页码青岛条目"}],"notes":["page为直接PDF物理页，source_printed_page为实际页脚文本，二者明确区分。","湖北621-2019已目视物理20/21页相邻原格，拼接跨页名称。","原PDF未保存；local-qa-hubei-*.png是本地目录目视辅助，不能上传GitHub。","不修改round02冻结记录；更正单独写corrections-round02.json。","目录发布日期、收录状态与各标准现行性分开；新疆目录为草案不等于列出的标准为草案。"]}
(BASE/"directory-round07.json").write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
(BASE/"corrections-round02.json").write_text(json.dumps({"checked_at":output["checked_at"],"corrections":corrections,"note":"新增证据更正，不改旧文件；全部有政府PDF物理页码"},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(stats,ensure_ascii=False))
print(json.dumps({"corrections":[{k:c[k] for k in ["standard_number","old_name","new_direct_pdf_name"]} for c in corrections]},ensure_ascii=False))

