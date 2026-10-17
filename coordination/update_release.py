"""Update the controller-owned release summary from verified frozen receipts."""
import datetime
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
receipt = json.loads((REPO / 'catalog/workbook-build-receipt.json').read_text(encoding='utf-8-sig'))
validation = json.loads((REPO / 'coordination/delivery-validation.json').read_text(encoding='utf-8-sig'))
book = next((REPO / 'catalog').glob('*.xlsx'))
assert hashlib.sha256(book.read_bytes()).hexdigest() == validation['xlsx_sha256']
assert receipt['coverage'] == validation['coverage']
generated = datetime.datetime.fromisoformat(receipt['generated_at'].replace('Z', '+00:00'))
beijing = generated.astimezone(datetime.timezone(datetime.timedelta(hours=8)))
c = receipt['coverage']
release = {'generated_at': receipt['generated_at'], 'generated_at_beijing': beijing.isoformat(),
           'xlsx': str(book.relative_to(REPO)), 'xlsx_sha256': validation['xlsx_sha256'],
           'coverage': c, 'verification': 'coordination/delivery-validation.json',
           'limits': '初步身份不等于确认正式标准，不是全集；目录不是规范全文；正式完整与内容完整草案分计；完整性不确认现行性。'}
(REPO / 'coordination/current-release.json').write_text(json.dumps(release, ensure_ascii=False, indent=2), encoding='utf-8')
readme = REPO / 'README.md'
text = readme.read_text(encoding='utf-8')
start = text.index('## 首批交付') if '## 首批交付' in text else text.index('## 当前交付快照')
end = text.index('## 任务范围', start)
summary = f'''## 当前交付快照

[下载 CECS 可下载 PDF 总表（Excel）](catalog/CECS可下载PDF总表.xlsx)；[机器索引](catalog/cecs-master.json)；[主控独立交付检查](coordination/delivery-validation.json)；[机器可读版本信息](coordination/current-release.json)。

快照生成于 {beijing.strftime('%Y-%m-%d %H:%M:%S')}（北京时间）：{c['registered_standard_versions']}个初步身份条目、{c['registered_links']}条链接、全部{c['baseline_records_registered']}条基线映射、{c['independent_audit_results']}条独立审查；正式标准{c['verified_complete_pdf_links']}条已验完整链接对应{c['verified_complete_unique_sha256']}份不同PDF、{c['verified_complete_standard_versions']}个规范版本。另有{c.get('verified_complete_draft_pdf_links', 0)}条内容完整草案链接，独立列出，不混入正式数。完整版本与备用同hash链接分别计数；历史版本、草案和未核状态均保留，身份条目数不代表全国CECS总数。

Excel含规范总表、已验完整PDF、完整草案PDF（有内容完整草案时）、链接明细、原始映射、待查与问题、状态与来源依据、检索记录、说明与覆盖、变更记录。质量推荐以表内证据为准，不用书签数量代替完整性或内容质量。后续增量先由角色继续核验，再按主控检查点回灌。PDF原件不在本仓库，现行性不因PDF完整而自动确认。

'''
readme.write_text(text[:start] + summary + text[end:], encoding='utf-8')
print(json.dumps({'generated_at': release['generated_at_beijing'], 'coverage': c}))
