# CECS PDF 研究中转站

- 本仓库仅保存本任务的 Excel 总表、JSON/JSONL 元数据、方法、审查记录和交流结论。不提交 PDF、页面图、全文摘录、登录资料或密钥，不绕过认证与付费。
- 全网 CECS 为范围；81 条是基线，不是全集。正式、历史、草案分别识别，缺全文仍登记。目录收录、现行性与完整 PDF 三种证据分开管理。
- `coordination/roles.json` 为主控与三个可见对话索引；每 10 分钟交流，讨论必须给出可验证试验。
- 主控是本 checkout 及 Git 唯一写入者，串行提交推送。三个角色写同级输出根中的 `catalog/`、`search/`、`pdf-audit/`；主控审核后同步。不要让角色或子任务直接写此 checkout。
- 当前已审发布分支为 `codex/reviewed-cecs-20261017`，发布checkout为同级 `reviewed-publish-repo/`，普通同步使用 `git push origin HEAD:main`。原 `exchange-repo/` 的旧本地main仅保留未发表原始历史，不推送该分支；不reset、不amend、不强推。
- catalog 为 Excel/主索引唯一写入者。规范版本一对多链接，主备同 hash 分开计链接与文件，不丢备链。保留每次检查时间、最终URL、状态、证据、历史及缺口。
- 审查先实际GET，再核版本与目录/正文/附录/末页。完整性未闭合不得升完整。可搜索文字、Outline书签和目录Link分别检查；逐页文件名书签不能称章节书签。
- 本轮封版先冻结 audit，再合入 catalog 并验证，最后由主控同步；新候选留下一轮，避免同步中途改写。
- 主控同步命令：在仓库根运行 `python coordination/sync_exchange.py`。脚本只复制白名单元数据，排除原件和原始网页响应；同步后审阅 `git diff --stat` 与文件名再提交。
- 交付一致性检查：使用具备 openpyxl 的 bundled Python 运行 `coordination/verify_delivery.py`。它只读源总表与JSON，并将主控校核结果写入 `coordination/delivery-validation.json`。
- 不改结构工作台源码、主分支、remote、正式项目数据或其他三个工作树，不自动部署。沿用用户授权仅向本仓库提交研究成果。
