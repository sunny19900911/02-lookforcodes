"""Add native XLSX hyperlinks, a capability absent from artifact-tool's public API.

The workbook's values, tables, formats, and sheets are authored by artifact-tool.
This narrow OpenXML pass adds only hyperlink relationships and verifies the ZIP.
"""
import json
import pathlib
import sys
import zipfile
import xml.etree.ElementTree as ET

book = pathlib.Path(sys.argv[1])
links = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
rels_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
office_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
ET.register_namespace("", ns)
ET.register_namespace("r", office_ns)
with zipfile.ZipFile(book) as archive:
    data = {info.filename: (info, archive.read(info.filename)) for info in archive.infolist()}
grouped = {}
for link in links:
    grouped.setdefault(link["sheet"], []).append(link)
for sheet, entries in grouped.items():
    name = f"xl/worksheets/sheet{sheet}.xml"
    rel_name = f"xl/worksheets/_rels/sheet{sheet}.xml.rels"
    doc = ET.fromstring(data[name][1])
    rel_doc = ET.fromstring(data[rel_name][1]) if rel_name in data else ET.Element(f"{{{rels_ns}}}Relationships")
    hyperlinks = doc.find(f"{{{ns}}}hyperlinks")
    if hyperlinks is None:
        hyperlinks = ET.Element(f"{{{ns}}}hyperlinks")
        following = {"printOptions", "pageMargins", "pageSetup", "headerFooter", "rowBreaks", "colBreaks", "customProperties", "cellWatches", "ignoredErrors", "smartTags", "drawing", "legacyDrawing", "legacyDrawingHF", "picture", "oleObjects", "controls", "webPublishItems", "tableParts", "extLst"}
        index = next((i for i, child in enumerate(doc) if child.tag.split("}")[-1] in following), len(doc))
        doc.insert(index, hyperlinks)
    for i, link in enumerate(entries, 1):
        rid = f"rIdCecsNative{i}"
        ET.SubElement(rel_doc, f"{{{rels_ns}}}Relationship", {"Id": rid, "Type": f"{office_ns}/hyperlink", "Target": link["url"], "TargetMode": "External"})
        ET.SubElement(hyperlinks, f"{{{ns}}}hyperlink", {"ref": link["cell"], f"{{{office_ns}}}id": rid, "tooltip": link["url"][:250]})
    data[name] = (data[name][0], ET.tostring(doc, encoding="utf-8", xml_declaration=True))
    data[rel_name] = (data[rel_name][0] if rel_name in data else rel_name, ET.tostring(rel_doc, encoding="utf-8", xml_declaration=True))
temporary = book.with_suffix(".hyperlinks.tmp.xlsx")
with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
    for name, (info, blob) in data.items():
        archive.writestr(info, blob)
with zipfile.ZipFile(temporary) as archive:
    assert archive.testzip() is None
temporary.replace(book)
print(json.dumps({"native_hyperlinks_added": len(links), "sheets": len(grouped)}))
