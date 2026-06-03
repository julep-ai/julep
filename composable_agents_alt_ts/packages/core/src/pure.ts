import type { Json } from './types.js';

export type PureFn = (input: Json) => Json;
export type PredicateFn = (input: Json) => boolean;

const pures: Record<string, PureFn | PredicateFn> = {};

export function registerPure(name: string, fn: PureFn | PredicateFn): void {
  if (!/^[a-zA-Z_][a-zA-Z0-9_./:-]*$/.test(name)) {
    throw new Error(`Invalid pure name: ${name}`);
  }
  pures[name] = fn;
}

export function getPure(name: string): PureFn | PredicateFn {
  const fn = pures[name];
  if (!fn) throw new Error(`Pure not registered: ${name}`);
  return fn;
}

export function hasPure(name: string): boolean {
  return Boolean(pures[name]);
}

export function listPures(): string[] {
  return Object.keys(pures).sort();
}

registerPure('alwaysTrue', () => true);
registerPure('alwaysFalse', () => false);
registerPure('identity', (x) => x);
registerPure('critiqueConverged', (x) => {
  if (x && typeof x === 'object' && !Array.isArray(x)) {
    const obj = x as Record<string, Json>;
    return obj.converged === true || obj.done === true;
  }
  return false;
});
