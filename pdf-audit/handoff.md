# PDF 独立审查交接

日期：2026-10-17（Asia/Shanghai）。生产者：旧 Agent3 `/root/audit`。当前批次已结束，旧 Agent 停止写入，接手对话可独占继续。

## 已保存

- `audit-results.json`：7条逐链接结果，schema_version=1.0。包含原URL/重定向最终URL、实际GET时间、大小/页数/hash、文件头/EOF/严格解析、文本层/汉字比例、原生书签/目标有效性、Link注释、页面旋转/裁切、目视结论、完整性和推荐理由。不得把 `C` 列入完整PDF。
- `audit_pdf.py`：只读PDF审查脚本。最多2并发，每连接18秒，GET总预算130秒，95MiB上限；不执行PDF脚本、不自动OCR/加书签。接收候选JSON的 `candidates` 数组或裸数组，按candidate_id跳过已审项，运行会追加audit-results。
- `candidates-own-round01.json`：审查侧自主发现的4条公开机构附件及原域1条。
- 每候选目录：`parse-evidence.json`，6页抽样PNG和contact-sheet.jpg。PDF原件仅在 `../downloads-temp/`。
- `finalize_handoff.py`：本次交接最后补入人工目视结论的脚本，不要重复运行覆盖接手的新结论。

## 本批实测结果

| candidate_id | 结果 | 仍须核验 |
|---|---|---|
| AUD-S001-HTTPS | knowledge.tjad.cloud TLS握手18秒超时；本次网络失败未验证 | 不应逐81条重试同一超时；换网络后再试 |
| AUD-PUBLIC-001 | 福建文旅官方附件 T/CECS896-2021，100页，60,294,767字节；封面匹配、扫描清楚，无正文文本层/原生书签 | 看PDF8目录末项、PDF99打印页90；确认完整后可B（缺书签） |
| AUD-PUBLIC-002 | 福建文旅官方附件 T/CECS1140-2022，192页，31,415,177字节；封面匹配、扫描清楚，无文本/书签 | 看目录所有页、末项E.4对应终页打印178；加抽1页表图及页码连续性 |
| AUD-PUBLIC-003 | 国管局官方附件 T/CECS935-2021，61页，1,072,229字节；矢量清楚，中文文本层，0书签、76Link | 检查目录Link实际指向；末页打印55公式(1)是否自然结束，避免把截断文件当完整 |
| AUD-PUBLIC-004 | 交通部官方附件 T/CECS G:K50-30-2018，46页，3,525,765字节；矢量清楚，0书签；中文复制严重乱码 | 目录PDF6末项与PDF43终页闭环；44-46是空白尾页 |
| R01-G1-001 | 2024锚杆URL实际返回HTML，84,455字节，非PDF | 搜索新的合法公开附件 |
| R01-G1-002 | antpedia旧锚杆文件仅3页封面/扉页/版权页；确定不是全文 | 别列入完整PDF，搜索其他源 |

四份官方附件目前均为C“可下载，完整性待核”，审查未完成前不得为了交付凑成完整数。原生书签均0；CECS935的可点击目录仍须验Link，书签与目录不能混同。

## 接手后顺序

1. 读pdf技能和audit-results。先把四份已下载文件的目录/终页问题核实，免得重新下载；补充PNG只渲染必要页，目视后把完整性/理由/证据及history增量写回。
2. 处理 `../search/candidates-round02.json`：已由search落盘，但旧Agent尚未GET。须逐条区分直接PDF/介绍页/受限。
3. 把候选ID与seed_ids或编号年份交catalog合并，维持status现行性与可下载性独立。
4. S009原种子796-2020与公告摘要796-2021有冲突，必须查PDF封面与公告，保留两种证据。
5. 每10分钟向主控、检索和总表agent交流新证据/质疑/试验；Git/Excel只由主控/catalog操作。

## 运行示例

```powershell
& 'C:\Users\mj528\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\mj528\Documents\004 工作\web-demo\outputs\cecs-master-20261017\pdf-audit\audit_pdf.py' 'C:\Users\mj528\Documents\004 工作\web-demo\outputs\cecs-master-20261017\search\candidates-round02.json'
```

## 同步边界

PDF原件、页面PNG、接触表、完整文本不得推GitHub；建议只同步结构化核验记录、方法脚本和本交接说明（证据图/原件保留本地路径）。原始seed只读，不改工作台源码，不操作Git，不读取凭据。接手须对JSON中的本地绝对路径保留本地引用，不误当公网可下载地址。
