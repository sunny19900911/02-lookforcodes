// Region means the evidenced download source, never a standard's applicability.
// No network, directory-page inference, IP geolocation or PDF-quality changes.
const text = value => typeof value === 'string' && value.trim() ? value.trim() : null;
const unique = values => [...new Set(values.filter(value => value !== null && value !== undefined))];

function publicUrl(value) {
  try {
    const url = new URL(value);
    if (!['http:', 'https:'].includes(url.protocol)) return null;
    url.hash = ''; // A PDF page fragment does not identify a different resource.
    return url;
  } catch { return null; }
}

function exactHost(value) {
  const raw = text(value);
  if (!raw || /[/?#@\s]/.test(raw)) return null;
  const url = publicUrl('https://' + raw);
  return url?.host ?? null;
}

function prepareEvidence(row) {
  return {
    row,
    hosts: new Set((row.match_hosts ?? []).map(exactHost).filter(Boolean)),
    urls: new Set((row.download_urls ?? []).map(publicUrl).filter(Boolean).map(url => url.href)),
  };
}

function locate(link, prepared, sourceId) {
  const urls = ['requested_url', 'final_url'].flatMap(field => {
    const url = publicUrl(link[field]); return url ? [{ field, url }] : [];
  });
  const basis = [];
  for (const { row, hosts, urls: explicitUrls } of prepared) {
    const matches = [];
    for (const { field, url } of urls) {
      if (hosts.has(url.host)) matches.push({ field, match_type: 'exact_host', host: url.host });
      if (explicitUrls.has(url.href)) matches.push({ field, match_type: 'explicit_download_url', host: url.host });
    }
    if (!matches.length) continue;
    basis.push({
      region_evidence_id: row.region_evidence_id,
      registry_source_id: sourceId,
      province: text(row.province), city: text(row.city), source_entity: text(row.source_entity),
      proof_url: row.proof_url ?? null, proof_excerpt: row.proof_excerpt ?? null,
      statement_type: row.statement_type ?? null, checked_at: row.checked_at ?? null,
      matches,
    });
  }
  const provinces = unique(basis.map(e => e.province)), cities = unique(basis.map(e => e.city));
  const conflict = provinces.length > 1 || cities.length > 1;
  const province = !conflict && provinces.length === 1 ? provinces[0] : null;
  const city = !conflict && cities.length === 1 ? cities[0] : null;
  return {
    region_status: conflict || (!province && !city) ? '待核' : province && city ? '已核实' : '部分核实',
    province, city,
    source_entity: conflict ? null : unique(basis.map(e => e.source_entity)).join('；') || null,
    region_evidence_ids: unique(basis.map(e => e.region_evidence_id)),
    region_basis: basis,
  };
}

function groupSummary(group) {
  const region = group.region_status === '待核' ? '来源地区待核'
    : group.province && group.city ? (group.province === group.city ? group.province : group.province + ' / ' + group.city)
      : group.province ? group.province + '（城市待核）' : group.city + '（省份待核）';
  return region + '（' + group.link_ids.length + '条链接）';
}

/** Mutate only region annotations, their coverage counts and the supplied registry. */
export function applyDownloadSourceRegions(model, registry) {
  const prepared = (registry.evidence ?? []).map(prepareEvidence);
  const links = new Map((model.links ?? []).map(link => [link.link_id, link]));
  for (const link of links.values()) link.download_source_region = locate(link, prepared, registry.source_id);

  let standardsWithLinks = 0;
  for (const standard of model.standards ?? []) {
    const groups = new Map();
    for (const linkId of unique(standard.link_ids ?? [])) {
      const region = links.get(linkId)?.download_source_region;
      if (!region) continue;
      const key = JSON.stringify([region.region_status, region.province, region.city]);
      if (!groups.has(key)) groups.set(key, {
        region_status: region.region_status, province: region.province, city: region.city,
        source_entities: [], link_ids: [], evidence_ids: [],
      });
      const group = groups.get(key);
      group.link_ids.push(linkId);
      group.source_entities = unique([...group.source_entities, ...region.region_basis.map(e => e.source_entity)]);
      group.evidence_ids = unique([...group.evidence_ids, ...region.region_evidence_ids]);
    }
    standard.download_source_regions = [...groups.values()];
    standard.download_source_region_summary = groups.size ? [...groups.values()].map(groupSummary).join('；') : '尚无下载来源';
    if (groups.size) standardsWithLinks++;
  }

  const regions = [...links.values()].map(link => link.download_source_region);
  model.coverage ??= {};
  model.coverage.download_source_region_counts = {
    total_links: regions.length,
    province_evidenced_links: regions.filter(r => r.province !== null).length,
    city_evidenced_links: regions.filter(r => r.city !== null).length,
    fully_identified_links: regions.filter(r => r.region_status === '已核实').length,
    partial_links: regions.filter(r => r.region_status === '部分核实').length,
    pending_links: regions.filter(r => r.region_status === '待核').length,
    standards_with_download_links: standardsWithLinks,
  };
  model.external ??= {};
  model.external.download_source_region_registry = registry;
  return model;
}
