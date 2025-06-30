/**
 * Run script given by relative path from @typespec/compiler package root.
 * Prefer local install resolved from cwd over current package.
 *
 * Prevents loading two conflicting copies of TypeSpec modules from global and
 * local package locations.
 */
export declare function runScript(relativePath: string, backupPath: string): Promise<void>;
//# sourceMappingURL=runner.d.ts.map