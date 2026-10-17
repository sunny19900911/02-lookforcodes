import json,hashlib
from pathlib import Path
BASE=Path(r"C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017/search/round08-public-expansion/directory2/")
p=BASE/"directory-round08.json"
d=json.loads(p.read_text(encoding="utf-8"))
d["source"]["cover_month_raw"]="2023年11月"
d["source"]["cover_month_evidence"]={"pdf_page_one_based":1,"note":"封面写2023年11月；不能据此把URL目录2023-12当精确发布日期"}
d["source"]["foreword_evidence"]={"pdf_page_one_based":2,"note":"前言写修订工作2022年11月至2023年12月、2023年11月通过审查；保留原文时间边界，不认定每项标准2026现行"}
d["conflicts_file"]="directory-conflicts.json"
d["canonical_update_policy"]="有directory_number_name_conflict的行仅作来源矛盾，不可静默覆盖规范主表正式名称"
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
r=d["records"]
check={"new_source_records":len(r),"unique_number_year_in_new_source_records":len({(x["number"],x["year"]) for x in r}),"genuinely_new_unique_number_year_vs_round07":d["coverage"]["new_unique_number_year_vs_round07"],"physical_pages_valid":all(isinstance(x["page"],int) and 1<=x["page"]<=186 for x in r),"all_have_raw_cells":all(bool(x["raw_cells"]) for x in r),"all_have_source_id":all(bool(x["source_id"]) for x in r),"duplicate_source_ids":len(r)-len({x["source_id"] for x in r}),"round07_links":len(d["round07_reverified_links"]),"unresolved_standard_rows":sum(bool(x.get("source_row_id")) for x in d["gaps"]),"nonstandard_code_rows":sum(not bool(x.get("source_row_id")) for x in d["gaps"]),"conflict_groups":d["coverage"]["directory_number_name_conflict_count"],"original_pdf_saved":False,"screenshots_saved":False}
for name in ["directory-round08.json","directory-conflicts.json","raw-cells.json","front-matter-evidence.json"]:
    check[name+"_sha256"]=hashlib.sha256((BASE/name).read_bytes()).hexdigest()
(BASE/"validation-summary.json").write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(check,ensure_ascii=False,indent=2))

