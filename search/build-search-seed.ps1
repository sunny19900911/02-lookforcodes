$root = 'C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-master-20261017/search'
$seedPath = 'C:/Users/mj528/Documents/004 工作/web-demo/outputs/cecs-catalog-20261017/CECS目录与下载路径.json'
$seeds = (Get-Content -Raw -LiteralPath $seedPath | ConvertFrom-Json).items
$groups = @(
 @{id='G1';name='地基基础与岩土';ids=@(2,18,19,20,21,23,24,25,26,27,28,29,30,31,63)},
 @{id='G2';name='混凝土与装配式结构';ids=@(3,4,32,33,34,35,36,37,64,65)},
 @{id='G3';name='钢结构、组合结构与抗震';ids=@(12,13,14,15,16,17,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,57,58,60,61,62,66,68,73,79,80,81)},
 @{id='G4';name='材料、检测与修复';ids=@(7,10,11,22,38,39,55,56,59,69,70,71,72,74,75)},
 @{id='G5';name='通用、绿色建筑与其他';ids=@(1,5,6,8,9,67,76,77,78)}
)
$records = foreach($g in $groups) { foreach($i in $seeds) { if($i.序号 -in $g.ids) { [ordered]@{seed_id=('S{0:D3}' -f $i.序号);seed_ordinal=$i.序号;original_name=$i.文件名;source_id=$i.source_id;topic_group=$g.id;topic_group_name=$g.name;classification_basis='AI推断：按名称与原始目录的专业主题归组；并非适用地区或规范分类结论';raw_key=$i.编号年份_初步识别;original_source_candidate=('https://knowledge.tjad.cloud'+$i.相对下载路径);source_network_status='本次网络未验证；源站此前TLS/连接超时；未据此判永久失效'} } } }
[ordered]@{generated_at=(Get-Date).ToString('o');baseline_note='81条文件记录，不是全国CECS全集；重复、旧版、草案均保留';classification='按专业主题分5组，地区无权威依据不分类';groups=$groups;records=@($records)} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $root 'seed-groups.json') -Encoding utf8
