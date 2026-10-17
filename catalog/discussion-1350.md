# 发布分享投影修正

主控TEMP_QUERY检查指出唯一当前机器底座路径`/external/search/43/redirect_entry`含瞬时参数。对应候选G2-R02-117-2017-315368-ZIP，原来源`search/g2-public-routes/round02-candidates.json`，SHA256 `c74bf7bafad8492bc055426a7b66340b14db42c00727cf574a06e4f45da64cf0`。未打印参数值，未修改原冻结来源。

分享machine仅去该路径的瞬时query并添加temporary_route_redacted、原来源路径/SHA；规范、链接、证据及change-log不搬入临时值。新machine SHA256 `4f66c453fdaafe58878d696fc8fd6d4802d9fc4b235785f51b8642ee6ed9a2c1`，原generated_at仍2026-10-17T05:37:51.370Z。811身份/127链接/33审查/9完整7版本7hash均不变。

XLSX未变，SHA256 `05da49e829a2ac73232bd9205ae750090f6fe26ffba33fd1e4ae3a3d129e2414`，重开校验仍通过。sharing-validation.json验证瞬时query零命中、清理幂等、原来源SHA未变；分享source副本为catalog/share-inputs/g2-round02-candidates.share.json（4候选不变），原始source及旧raw master历史只留本地，不直接出版。

builder今后调用sharing-projection-core.mjs自动清外部投影。两项独立语义验证通过：删除临时query仍保留file_id及fragment、正常稳定query完全不变；用合成示例，不使用或输出真实临时值。分享操作收据为sharing-projection-receipt.json。

R07及草案质量仍在下一批审查，当前canonical33和本轮Excel不追加新结果。评级/完整性结论属于AI基于实测的判断，不当作发布方认证。Git及干净发布树均由主控操作，本角色未调用Git。
