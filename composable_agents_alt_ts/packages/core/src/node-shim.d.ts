declare module 'node:crypto' {
  export function createHash(algorithm: string): { update(input: string): { digest(encoding: 'hex'): string } };
}
