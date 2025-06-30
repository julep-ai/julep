import { Exports } from "../../types/package-json.js";
import { EsmResolutionContext } from "./utils.js";
export interface ResolvePackageTargetOptions {
    readonly target: Exports;
    readonly patternMatch?: string;
    readonly isImports?: boolean;
}
/** Implementation of PACKAGE_TARGET_RESOLVE https://github.com/nodejs/node/blob/main/doc/api/esm.md */
export declare function resolvePackageTarget(context: EsmResolutionContext, { target, patternMatch, isImports }: ResolvePackageTargetOptions): Promise<null | undefined | string>;
//# sourceMappingURL=resolve-package-target.d.ts.map