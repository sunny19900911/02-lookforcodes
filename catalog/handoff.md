# CECS 总表管理交接

## 本轮最终封版（2026-10-17 13:14，优先于下文）

主控要求将冻结28审查的8条完整链接全部回灌，本轮已完成最后重建并重新冻结。generated_at=`2026-10-17T05:14:07.858Z`。753个初步身份、119链接、652目录行、81原始映射、842证据；28审查为8B/10C/10D。完整8链接=6规范版本=6不同SHA256；69:94与48:93各主备同hash，全部保留且每版有效备用数1。

最终XLSX：450385字节，SHA256=`f6ce838ec33e704fb942bfc63e24c1c641ba177251fb4e62f08e6c50a01b2aac`。master SHA256=`ae68170f97aa448f19c8f3693334268b0fb9a52c2ace5c3da2b437a915ad9256`。输入audit SHA256=`46147add21cc3ab5453f683ac816c8763fddc31a845baa2908adf2e902642f1d`。

9表重开核验通过，2649个原生超链接，0错误单元格；81映射、计数、完整表8条实际URL及SHA多重集与master一致。已目视9表及最后受影响视图。`workbook-validation.json`为最终核验收据。已通知主控独立核对并串行同步，角色未操作Git。

已保留三条1996/2034/2054介绍元数据、8天华Preview身份与英文原名，均未升级全文；22:2005继续C。后续候选与审查进入下一轮，不继续覆盖封版文件。下文13:08及13:10数据属于先前快照。

---

## 独立对话接手后的最新状态（2026-10-17 13:08）

以下覆盖本文旧检查点的待办状态，旧内容保留作历史。

- 已实际生成 `CECS可下载PDF总表.xlsx`（9表），745个初步身份条目、108链接、652官方目录原始行、20独立审查结果。81条种子映射完整；796两编号候选共用冲突组，未认定两个真实版本。CECS-CBIMU独立族、前导零、子系列及稿型均隔离。
- 4份完整PDF均为B：1140、935、G:K50-30、10032；8C、8D。935占位编号异常、10032水印、896缺口和索结构不完整均保留。只以显式`complete_pdf && version_verified`及适用身份确认推荐，不按HTTP或页数升级。
- 递归导入search候选（含G2子目录）、全部备用URL、主控官方目录、796冲突文件及audit-results；新增`maintenance-input.json`维护层，新增/更新/停用须reason/source_id；标准与链接都追加变更记录，history快照保留。
- 已完成artifact recalculate/inspect/9表渲染目视，原始HYPERLINK公式不受运行库支持，改为OpenXML原生超链接。`patch-hyperlinks.py`仅补原生超链接关系，其余工作簿由artifact-tool作者。已独立用bundled Python openpyxl只读重新打开：9表、2530超链接、0错误单元格、81映射及计数/完整PDF必填字段通过，详见`workbook-validation.json`。
- 该快照SHA256：`7acdf658496d65886aa286caebd6fb5c7c9cfa1baa63647caa25a6785012c12a`，424093字节。已通知主控先冻结同步，角色未操作Git。
- 注意：artifact导出进程退出码1，但未给错误诊断且输出成功；不能仅凭此退出码认定文件失败或成功。重建后必须运行`verify-workbook.py`，以保存后ZIP/重新打开核验为准，异常仍需排查。不要重新运行marker，首次作者前已成功运行一次。
- 下一步：主控完成该快照独立核对/同步；再接续审查新增结果，优先同版清晰、无遮挡、正文可复制和原生书签版本。`discussion-1300.md`记录交叉质疑与下一轮试验。不要声称全网穷尽。

---

检查点：2026-10-17，北京时间约 12:57。按主控要求，已停止后续写入，等待独立可见对话接手。

## 已完成

- 已完整阅读 spreadsheets 技能、API_QUICK_START、style_guidelines、create_workflows。必须用 `@oai/artifact-tool` 作者真正 XLSX，不得以 CSV 代替。
- 已读取只读种子 `../cecs-catalog-20261017/CECS目录与下载路径.json`，登记全部 81 条原始记录；77 个不同原文件名。
- 按编号、年份、正式/报批/征求稿及独立修订版标记建立 74 个初步规范版本。这个数量是建模结果，仍待权威证据修正，不代表全国全集。
- 已读取 search/seed-groups.json，复用五主题组（G1~G5 原记录为 15/10/32/15/9）。
- 已合入 search/candidates-round01.json 当时的 2 条地基公开 PDF 候选，仅登记为候选。当前 83 个不同链接，完整 PDF 已核验数为 0。
- 所有现行性保留“未知”。网页标注作废/废止只作原文证据，不作 2026 现行性结论。
- 已建立 immutable history 快照、JSONL 变更记录。原始种子未修改。

## 文件与结构

- `catalog/build-catalog.mjs`：唯一 builder，目前实现 seed + search candidates 机器底座；`--index-only` 可运行，不会生成 XLSX。结尾的 workbook authoring 尚未实现。
- `catalog/seed-index.json`：供检索、质量审查引用；`records` 含 S001~S081、standard_id、原名、标准号、number/year/year_text、稿型、版次、分组、source_id、候选 URL、link_id、识别问题。
- `catalog/cecs-master.json`：顶层 `scope/standards/links/original_records/evidence/issues/external_inputs/external/coverage/change_log`。
- `catalog/change-log.jsonl`：已发生的新增/更新记录。
- `catalog/history/master-*.json`：每次运行的不可变快照。
- `catalog/node_modules`：Windows junction，指向 bundled runtime 的 node_modules，只用于 artifact-tool，不是本地项目依赖。

主表稳定 ID 规则：`CECS-{编号}-{年份或YEAR-UNKNOWN}-{FORMAL/APPROVAL-DRAFT/CONSULT-DRAFT}[-E修订年]`。占位编号为 UNRESOLVED hash。T/CECS、T∕CECS、CECS_T 等书写变体按相同编号年识别，但发布代码仍保留候选原貌。不得按三位编号拆成两位编号与年份。

`standards` 含：稳定 ID、active/maintenance_action、baseline、新旧原名和 seed 映射、编号/名称/年份/稿型/版次、类别/分组/适用范围、current_status、替代关系、状态及元数据 evidence IDs、发布/实施日期、来源页、link_ids/best_link_id/备用数、issues、创建及更新时间。

`links` 含：link_id、多 standard_ids、候选/请求/最终 URL、来源页/类型、发现/检查时间、HTTP及权限/过期状态、下载状态、大小/页数/hash、解析/版本匹配/文本层/复制搜索/书签数与跳转/可点目录/清晰度/页序裁边旋转水印/加密、完整性和 complete_pdf、推荐等级及原因、证据路径/临时文件/check_history。现有候选不得升级为已实测。

## 待接手的工作

1. 适配并合入主控即将生成的 `search/master-authority/authority-directory-records.json`。主控已提取辽宁水利院 2018 官方有效目录 204 条；仅能记当时状态，不能据此确认 2026 现行性。还在收集青岛住建 2025-11~2026-10 月标准清单。
2. 合入 search 后续 candidates JSON、轮次记录和缺项队列。搜索 agent 路径 `/root/search`。
3. 合入 audit 的 `pdf-audit/audit-results.json`。审查 agent 路径 `/root/audit`，承诺保留逐条检查历史；最初在审官方 CECS 896/1140、国管局 CECS 935、交通部 G:K50-30 以及原域有限连接验证。
4. 审查结果唯一决定下载/完整性/质量，不可由 URL、200、HEAD 或多页猜完整。可下载但完整性待核不得进入“已验完整PDF”清单。
5. 完成真实 `catalog/CECS可下载PDF总表.xlsx`，建议输出表：规范总表、已验完整PDF、链接明细、原始映射、待查与问题、状态依据、检索记录、说明与覆盖、变更记录。主视图在左，源证据及说明在右。
6. 写 workbook 作者部分前，先运行 skill 的 `container_tools/mark_artifact_operation_started.mjs --operation-kind create --expected-output-count 1 --output-format xlsx`，本检查点尚未运行，后续首次作者命令前只运行一次。
7. 最终需 artifact recalculation、inspect 关键数据/公式错误、各 sheet 渲染实际看图、export XLSX 和已保存文件核对。没有完成这些，不宣称已交付 Excel。

## 运行环境

- Node：`C:/Users/mj528/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe`
- Python：`C:/Users/mj528/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`
- Artifact node_modules：同 dependencies 下 `node/node_modules`。
- 技能根：`C:/Users/mj528/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.1013.11914/skills/spreadsheets`。
- 所有派生输出仅在 `web-demo/outputs/cecs-master-20261017/catalog`；不修改工作台源码、不提交推送、不下载规范到 Git。

## 已知需修正/验证

- builder 的外部目录及 audit 导入尚未实现；全量运行仍只生成 JSON，没有 XLSX。
- 编号 737 的种子年份原文是 202，保留 YEAR-UNKNOWN；名称解析可能残留 202 前缀，需通过证据修正，不能补猜年份。
- CECS 77:96 暂按 1996 登记并带待核问题；需要权威目录复核。
- 同版异源必须保留全部有效 URL，最佳链接仅作为选择，不可删除备选。
- 当前 master 没有人工输入维护层，后续若允许用户直接增删，需将新增/更新/停用写入独立 catalog/maintenance-input.json 再合并，不能让重跑 builder 丢人工修改。
- 全国 CECS 全集分母未知；81 种子、2018 目录和当月公告范围各自统计，不能据此计算全国百分比。

## 协作检查点

主控要求每 10 分钟向 search/audit 交换证据和方法，首个检查点北京时间约 13:00。本 agent 已发 schema 与路径，尚未到第一次交流时即接到转移要求。后续独立对话应延续这个交流节奏，并把讨论输入保存到自己的目录。
