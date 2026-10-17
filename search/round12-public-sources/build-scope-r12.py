import json, hashlib, pathlib, datetime, collections

BASE = pathlib.Path(r'C:\Users\mj528\Documents\004 工作\web-demo\outputs\cecs-master-20261017')
OUT = BASE / 'search/round12-public-sources'
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')

def read(rel):
    return json.loads((BASE / rel).read_text(encoding='utf-8-sig'))

def sha(rel):
    return hashlib.sha256((BASE / rel).read_bytes()).hexdigest()

def write(name, value):
    p = OUT / name
    assert not p.exists(), str(p)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

RULE = 'USER-20261017-CECS-BUILDING-STRUCTURE-ONLY'
rows = []
def add(identifier, number, name, status, reason, source, url=None, parent=None, quality=None, kind='PDF候选'):
    rows.append(dict(candidate_id=identifier, source_id='SCOPE-R12-' + identifier,
        original_source_id=source, standard_number=number, name=name,
        scope_status=status, scope_reason=reason, scope_rule_source_id=RULE,
        scope_statement_type='AI推断（基于原题名/已有来源的专业范围初判）',
        evidence_statement_type='原文事实（原记录中的题名/链接/审查结果）',
        download_url=url, source_page=parent, route_kind=kind,
        eligible_for_current_structure_queue=status == 'in_scope',
        download_enabled=False, new_network_request_after_scope_change=False,
        quality_observation=quality,
        boundary='范围初判不确认2026现行有效性、版本对应、全文完整性或转载授权。'))

r11 = read('search/round11-public-sources/candidates-r11-root.json')['candidates']
decisions = {
 'R11-31-2017-APEXTRAY': ('excluded', '电缆桥架属于电气工程设备，本条没有房屋承重结构设计直接关系。', '审查v2：主链为验证HTML，备链证书名称失败；不再追查。'),
 'R11-1555-2024-FAIUSR': ('excluded', '碳中和建筑评价，未见与房屋承重结构设计直接相关的专门技术范围。', '审查v2：D，30页浏览版未附所列条文说明；范围排除不改质量记录。'),
 'R11-200-2006-DLSSYHT': ('in_scope', '题名明确建筑钢结构防火，涉及房屋承重钢结构抗火设计；区别于消防设备。', '审查v2：D，96页重排本缺实际条文说明且有单位漏写；保留为缺口/备链问题，不推荐当前文件。'),
 'R11-197-2006-FAIUSR': ('pending', '孔内深层强夯可能用于房屋地基，但本角色尚无适用范围原文证明房屋用途；先待判。', '审查v2：C，34物理页；部分空白页未获独立证明，不增加完整数。'),
 'R11-165-2004-YSJIANZHAN': ('excluded', '城市地下通信管道属于一般市政通信基础设施。', '审查v2：403；停止后续访问。'),
}
for c in r11:
    status, reason, quality = decisions[c['candidate_id']]
    add(c['candidate_id'],c['standard_number'],c['name'],status,reason,c['source_id'],c['download_url'],c['source_page'],quality)
    if c['candidate_id'] == 'R11-31-2017-APEXTRAY':
        add('R11-31-2017-ALTERNATE',c['standard_number'],c['name'],'excluded',reason,
            'pdf-audit/candidates-r11-alt31-share.json',c['alternative_urls'][0],None,
            '备用URL web_pages=null；不继承主链web64页。审查v2证书名称失败。')

inst = read('search/round11-public-sources/instrument-pages/round11-instrument-pages.json')
c=inst['candidates'][0]
add(c['candidate_id'],c['standard_number'],c['standard_name'],'in_scope',
    '混凝土强度检测方法直接服务结构检测鉴定及设计复核；仅保留方法相关性。',c['source_id'],c['download_url'],c['source_page'],
    '审查v2：D，与旧缺说明本同SHA；不重复下载，不增加完整数。')
c=inst['non_pdf_metadata_routes'][0]
add(c['route_id'],c['standard_number'],c['standard_name'],'in_scope',
    '混凝土缺陷检测直接服务结构检测与复核；当前仅有DOC路线题名及签名。',c['source_id'],c['download_url'],c['source_page'],
    'DOC未打开/转换，不计作PDF或完整文本。',kind='DOC元数据')

alt = read('search/round11-public-sources/alternate-route-41-r11.json')
add('R11-ALT-41-2004','CECS 41:2004','建筑给水硬聚氯乙烯管道工程技术规程','excluded',
    '建筑给水管道，属于给排水工程。','search/round11-public-sources/alternate-route-41-r11.json',
    'https://pro5323b5d3-pic11.ysjianzhan.cn/upload/34CECS41-2004JZGSYJLYXGGDGCJSGC.pdf',quality='原备链未GET；停止追查。')

add('R12-28-2012-INDEX','CECS 28:2012','钢管混凝土结构技术规程','in_scope',
    '钢管混凝土承重结构设计直接属于房屋结构设计方向；后续仍需核适用范围及版本。',
    'SEARCH-R12-WEB59-28-2012',None,None,
    '仅公开索引所见封面/题名；政府站点下载链接含不透明参数，未保存或分享参数值，未执行本轮后续GET。',kind='索引元数据，未给可用下载URL')
rows[-1]['source_host_observed']='jncc.jinan.gov.cn'
rows[-1]['indexed_filename']='6f531b872d124585b888c4bcfde0616b.pdf'
add('R12-1009-2022-PAGE','T/CECS 1009-2022','钢结构现场检测技术标准','in_scope',
    '钢结构现场检测直接服务房屋结构检测鉴定和设计复核；具体适用范围待核。',
    'SEARCH-R12-WEB59-1009-2022',None,'https://www.ynjcxh.cn/webinfoynxh/Del.aspx?id=5556',
    '已见协会页面索引；未打开页面提取附件，不能称有实测PDF。',kind='公开页面元数据，附件未提取')
add('R12-291-2011-INDEX','CECS 291:2011','波纹腹板钢结构技术规程','pending',
    '钢结构题名不足以排除桥梁或其他用途；须先确认房屋适用范围，暂停GET。',
    'SEARCH-R12-WEB59-291-2011','https://pro5323b5d3-pic11.ysjianzhan.cn/upload/102CECS291-2011BWFBGJGJSGF.pdf',
    quality='仅新公开索引路线，不将同host其他件403推为本件状态。')
add('R12-80-2006-INDEX','CECS 80:2006','塔桅钢结构工程施工质量验收规程','pending',
    '塔桅通常涉及独立构筑物；尚无房屋承重结构直接适用依据，暂停GET。',
    'SEARCH-R12-WEB59-80-2006','https://img.antpedia.com/standard/files/pdfs_ora/CN-CECS/a47/CECS%2080-2006.pdf',
    quality='仅公开索引，不依其他Antpedia文件的页数推定本件完整性。')

write('scope-queue-r12.json', dict(schema_version=1,source_id='SEARCH-R12-SCOPE-QUEUE-20261017',
    recorded_at=NOW,rule_source_id=RULE,projection_scope='仅R11及R12根角色已见路线，非全量主索引清理',
    rows=rows,counts=dict(collections.Counter(r['scope_status'] for r in rows)),
    global_in_scope_total=None,global_complete_formal_total=None,new_scope_coverage=None,
    all_current_downloads_disabled=True,notes=['纳入表示进入结构范围问题/来源队列，不能作为质量合格推荐。','pending和excluded不计当前结构范围分母；本投影不替代catalog全量筛选。','旧冻结与主索引、Excel及审查评级未修改。']))

selection='pdf-audit/audit-round09-publication-selection-1450.json'
sel=read(selection)
refs=[selection,'pdf-audit/'+sel['selected_audit_snapshot']['path'],
      'pdf-audit/'+sel['selected_audit_receipt'],
      'pdf-audit/'+sel['current_alternate_share_projection']['path']]
expected={refs[1]:sel['selected_audit_snapshot']['sha256'],refs[3]:sel['current_alternate_share_projection']['sha256']}
checks=[dict(path=p,sha256=sha(p),expected_sha256=expected.get(p),matches_expected=(sha(p)==expected[p]) if p in expected else None) for p in refs]
assert all(x['matches_expected'] is not False for x in checks)
write('receipt-audit-1450-selection-r12.json',dict(source_id='SEARCH-R12-AUDIT-SELECTION-20261017',recorded_at=NOW,
    statement_type='原文事实（只读路径/哈希核对）',selected=checks,
    excluded_as_current=['pdf-audit/candidates-r11-alt31.json','pdf-audit/audit-pending-round09-freeze-1450.json'],
    note='只选v2及备链share投影；备用URL不继承主web64页。7审查记录为旧广范围批次，不能直接作为新范围总数。',
    changed_audit_ratings=False,changed_canonical_audit=False))

transport='search/round12-public-sources/transport/excluded-transport-closeout.json'
products='search/round12-public-sources/material-products/round12-house-structure-scope.json'
write('scope-closeout-receipt-r12.json',dict(source_id='SEARCH-R12-SUBAGENT-CLOSEOUT-20261017',recorded_at=NOW,
    statement_type='原文事实（子代理本地收尾回执）',files=[dict(path=p,sha256=sha(p)) for p in [transport,products]],
    transport=dict(status='已停止，无在途工具',isolated_records=5,current_candidates=0,
        source_ids=['SEARCH-R12-TRANSPORT-EXCLUDED-%03d'%n for n in range(1,6)],
        refined_exclusion_reason={'001':'公路CECS，排除','002':'地方公路标准，非CECS且排除',
            '003':'地方标准草案，非CECS；不从被引用CECS推为CECS全文，不沿用笼统交通适用结论',
            '004':'桥梁检查项目文件，非CECS正文','005':'科技奖名单，非CECS正文'}),
    products=dict(status='已停止',formal_candidates=0,pending_structural_drafts=1,
        draft_id='R12-STRUCT-DRAFT-001',download_enabled=False,
        boundary='五位占位2022征求意见稿不得改挂T/CECS10300-2023正式号；房屋适用边界待判。'),
    post_stop_new_searches=0,post_stop_new_gets=0,post_stop_new_downloads=0,
    old_frozen_inputs_modified=False))

print(json.dumps({'output_directory':str(OUT),'root_rows':len(rows),'scope_counts':dict(collections.Counter(r['scope_status'] for r in rows)),'audit_selection_hashes_match':True},ensure_ascii=False))
