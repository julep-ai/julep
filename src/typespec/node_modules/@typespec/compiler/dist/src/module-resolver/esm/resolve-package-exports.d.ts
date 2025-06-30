import { Exports } from "../../types/package-json.js";
import { EsmResolutionContext } from "./utils.js";
/** Implementation of PACKAGE_EXPORTS_RESOLVE https://github.com/nodejs/node/blob/main/doc/api/esm.md */
export declare function resolvePackageExports(context: EsmResolutionContext, subpath: string, exports: Exports): Promise<string | null | undefined>;
/**
 * Mappings is an export object where all keys start with '.
 */
export declare function isMappings(exports: Exports): exports is Record<string, Exports>;
//# sourceMappingURL=resolve-package-exports.d.ts.map