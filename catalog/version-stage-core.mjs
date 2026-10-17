const FORMAL = '正式文本候选';
const UNKNOWN_DRAFT = '草案（阶段待核）';
const clean = value => String(value ?? '').normalize('NFKC').trim();
const clauses = value => clean(value).split(/[，,；;。！？\n]/).filter(Boolean);

// A stage observation belongs to the file, while a denial or an unresolved
// comparison is only a limitation. Never turn "未见草案" into a draft label.
function negatedPrefix(prefix) {
  return /(?:未见|未发现|未标明|未标|未注明|没有|尚无|并非|不是|不属于|不能认定为|不认定为|不作为|不能证明为|不证明为|不确定是否|是否|非|无|不)[^，,；;。！？\n]{0,8}$/.test(prefix);
}

function uncertainPhase(clause) {
  return /(?:稿型|阶段|身份|状态)\s*(?:尚|仍|均|各|均尚)?\s*(?:待核|待确认|待定|未核|未知|不明)/.test(clause);
}

function positivePhases(value) {
  const stages = new Set();
  for (const clause of clauses(value)) {
    if (uncertainPhase(clause)) continue;
    for (const match of clause.matchAll(/征求意见(?:稿)?|报批(?:稿)?|送审(?:稿)?/g)) {
      if (negatedPrefix(clause.slice(0, match.index))) continue;
      stages.add(match[0].startsWith('征求意见') ? '征求意见稿' : match[0].startsWith('报批') ? '报批稿' : '送审稿');
    }
  }
  return stages;
}

function affirmedFormal(value) {
  return clauses(value).some(clause => [...clause.matchAll(/(?:标称)?正式(?=编号|历史|版本|版|文本|标准|候选|发布|$|[（(])/g)]
    .some(match => !negatedPrefix(clause.slice(0, match.index))));
}

function draftSignal(value) {
  return clauses(value).some(clause => {
    // Conflicting or unverified phase names establish only an unresolved draft.
    if (uncertainPhase(clause) && /征求意见|报批|送审|草案/.test(clause)) return true;
    return [...clause.matchAll(/草案/g)].some(match => !negatedPrefix(clause.slice(0, match.index)));
  });
}

function onePhase(value) {
  const phases = positivePhases(value);
  return phases.size === 1 ? [...phases][0] : phases.size > 1 ? UNKNOWN_DRAFT : null;
}

export function inferVersionStage({text, explicitStage, versionClass} = {}) {
  // The audit's short classification outranks the explanatory stage field.
  const classified = onePhase(versionClass);
  if (classified) return classified;
  if (affirmedFormal(versionClass)) return FORMAL;
  if (draftSignal(versionClass)) return UNKNOWN_DRAFT;

  const explicit = onePhase(explicitStage);
  if (explicit) return explicit;
  if (draftSignal(explicitStage)) return UNKNOWN_DRAFT;
  if (affirmedFormal(explicitStage)) return FORMAL;

  const named = onePhase(text);
  if (named) return named;
  if (draftSignal(text) || /(?:20\dX|20XX|X{2,}|×{2,})/i.test(clean(text))) return UNKNOWN_DRAFT;
  return FORMAL;
}
