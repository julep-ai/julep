import type { CapabilityToolOverride, McpToolAnnotationHints, ToolContract } from './types.js';

export const conservativeContract: ToolContract = { effect: 'write', idempotency: 'none', approval: 'none', asserted: false };

export function defaultContractFromMcpAnnotations(ann?: McpToolAnnotationHints): ToolContract {
  let effect: ToolContract['effect'] = 'write';
  if (ann?.readOnlyHint === true) effect = 'read';
  else if (ann?.destructiveHint === true) effect = 'dangerous';
  else if (ann?.openWorldHint === true) effect = 'external';

  const idempotency: ToolContract['idempotency'] = ann?.idempotentHint === true ? 'native' : 'none';
  return { effect, idempotency, approval: effect === 'dangerous' ? 'required' : 'none', asserted: false };
}

export function contractFromOverride(base: ToolContract, override?: CapabilityToolOverride): ToolContract {
  if (!override) return base;
  const asserted = override.asserted ?? (
    override.effect !== undefined || override.idempotency !== undefined || override.approval !== undefined
  );
  return {
    effect: override.effect ?? base.effect,
    idempotency: override.idempotency ?? base.idempotency,
    approval: override.approval ?? base.approval,
    asserted: asserted || base.asserted
  };
}

export function isRaceSafe(contract: ToolContract): boolean {
  return contract.effect === 'read' || contract.idempotency === 'native' || contract.idempotency === 'required';
}
