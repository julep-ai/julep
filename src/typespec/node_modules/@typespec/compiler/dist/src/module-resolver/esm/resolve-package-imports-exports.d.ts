import { Exports } from "../../types/package-json.js";
import { EsmResolutionContext } from "./utils.js";
interface ResolvePackageImportsExportsOptions {
    readonly matchKey: string;
    readonly matchObj: Record<string, Exports>;
    readonly isImports?: boolean;
}
/** Implementation of PACKAGE_IMPORTS_EXPORTS_RESOLVE https://github.com/nodejs/node/blob/main/doc/api/esm.md */
export declare function resolvePackageImportsExports(context: EsmResolutionContext, { matchKey, matchObj, isImports }: ResolvePackageImportsExportsOptions): Promise<string | null | undefined>;
export {};
//# sourceMappingURL=resolve-package-imports-exports.d.ts.map