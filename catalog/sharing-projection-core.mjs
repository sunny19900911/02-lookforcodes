const temporaryQuery=/(\?|&(?:amp;)?)(uhash|access_token|auth_token|session_token|jsessionid|phpsessid|x-amz-signature|x-amz-security-token|x-amz-credential|x-amz-expires)=([^&#\s"'<>]*)/gi;

export function cleanSharingExternal(external){
  const changes=[];
  function walk(value,pointer,record){
    if(typeof value==='string'){
      temporaryQuery.lastIndex=0;
      const cleaned=value.replace(temporaryQuery,(_,separator)=>separator==='?'?'?':'').replace(/\?&/g,'?').replace(/[?&]$/,'');
      if(cleaned!==value){changes.push({path:pointer,candidate_id:record?.candidate_id??null});if(record){record.temporary_route_redacted=true;record.temporary_route_source_file=record._catalog_source?.path??null;record.temporary_route_source_sha256=record._catalog_source?.sha256??null;}return cleaned;}
      return value;
    }
    if(Array.isArray(value))return value.map((item,i)=>walk(item,`${pointer}/${i}`,item?.candidate_id?item:record));
    if(value&&typeof value==='object'){
      const current=value.candidate_id?value:record;
      for(const key of Object.keys(value))value[key]=walk(value[key],`${pointer}/${key.replace(/~/g,'~0').replace(/\//g,'~1')}`,current);
    }
    return value;
  }
  walk(external,'/external',null);
  return changes;
}
