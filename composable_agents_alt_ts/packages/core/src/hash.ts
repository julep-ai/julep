import { createHash } from 'node:crypto';
import { stableStringify } from './stable.js';

export function sha256Hex(value: unknown): string {
  return createHash('sha256').update(stableStringify(value)).digest('hex');
}

export function shortHash(value: unknown, chars = 10): string {
  return sha256Hex(value).slice(0, chars);
}
