# 发布分享投影修正

主控TEMP_QUERY检查指出唯一当前机器底座路径`/external/search/43/redirect_entry`含瞬时参数。对应候选G2-R02-117-2017-315368-ZIP，原来源`search/g2-public-routes/round02-candidates.json`，SHA256 `c74bf7bafad8492bc055426a7b66340b14db42c00727cf574a06e4f45da64cf0`。未打印参数值，未修改原冻结来源。

分享machine仅去该路径的瞬时query并添加temporary_route_redacted、原来源路径/SHA；规范、链接、证据及change-log不搬入临时值。新machine SHA256 `4f66c453fdaafe58878d696fc8fd6d4802d9fc4b235785f51b8642ee6ed9a2c1`，原generated_at仍2026-10-17T05:37:51.370Z。811身份/127链接/33审查/9完整7版本7hash均不变。

XLSX未变，SHA256 `05da49e829a2ac73232bd9205ae750090f6fe26ffba33fd1e4ae3a3d129e2414`，重开校验仍通过。sharing-validation.json验证瞬时query零命中、清理幂等、原来源SHA未变；分享source副本为catalog/share-inputs/g2-round02-candidates.share.json（4候选不变），原始source及旧raw master历史只留本地，不直接出版。

builder今后调用sharing-projection-core.mjs自动清外部投影。两项独立语义验证通过：删除临时query仍保留file_id及fragment、正常稳定query完全不变；用合成示例，不使用或输出真实临时值。分享操作收据为sharing-projection-receipt.json。

最终独立只读分享复核零违规：machine与分享source均无瞬时query，来源路径/SHA和回执一致，811/127/33/81与9完整双门槛、102/796无回归，Excel SHA未变。search另外提供round02-candidates-share.json及freeze-inputs-g2-round02-share-1350.json，已独立复核，redirect_entry置null而去参数route明确未验；发布源可优先采用search该语义更明确的投影，原冻结输入仅本地保留。

R07及草案质量仍在下一批审查，当前canonical33和本轮Excel不追加新结果。评级/完整性结论属于AI基于实测的判断，不当作发布方认证。Git及干净发布树均由主控操作，本角色未调用Git。

13:53:57审查角色现已固定round05七GET，catalog复核冻结SHA256为`90081712aea2c2ddb78202101d3e31753828ed6e663af87a139ec9e007e7dcf8`。待主控授权后，预计审查40、正式完整10链接/8版本/8哈希，完整报批稿另1；10025正式完整B、零碳报批稿内容完整B但不入正式集合，41/164仍C，三GET403仅本次失败。回执及草案schema适配要求已列入pending-next-round.md；当前811/127/33与9正式完整仍冻结。
