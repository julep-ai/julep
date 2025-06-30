import { DiagnosticHandler } from "./diagnostics.js";
import { CompilerHost } from "./types.js";
/**
 * Resolve the path to the main file
 * @param path path to the entrypoint of the program. Can be the main.tsp, folder containing main.tsp or a project/library root.
 * @returns Absolute path to the entrypoint.
 */
export declare function resolveTypeSpecEntrypoint(host: CompilerHost, path: string, reportDiagnostic: DiagnosticHandler): Promise<string | undefined>;
export declare function resolveTypeSpecEntrypointForDir(host: CompilerHost, dir: string, reportDiagnostic: DiagnosticHandler): Promise<string>;
//# sourceMappingURL=entrypoint-resolution.d.ts.map