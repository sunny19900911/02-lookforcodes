import assert from 'node:assert/strict';
import test from 'node:test';
import {cleanSharingExternal} from './sharing-projection-core.mjs';
test('sharing removes temporary query values but preserves stable route and fragment',()=>{
  const data={search:[{candidate_id:'example',redirect_entry:'https://example.invalid/download?uhash=temporary-route&file_id=112#page=2',_catalog_source:{path:'search/example.json',sha256:'source-hash'}}]};
  assert.equal(cleanSharingExternal(data).length,1);
  assert.equal(data.search[0].redirect_entry,'https://example.invalid/download?file_id=112#page=2');
  assert.equal(data.search[0].temporary_route_redacted,true);assert.equal(data.search[0].temporary_route_source_sha256,'source-hash');
  assert.equal(cleanSharingExternal(data).length,0);
});
test('stable download queries remain usable',()=>{
  const data={search:[{candidate_id:'example',download_url:'https://example.invalid/file.pdf?doc=41&v=2004'}]};
  const original=structuredClone(data);assert.equal(cleanSharingExternal(data).length,0);assert.deepEqual(data,original);
});
