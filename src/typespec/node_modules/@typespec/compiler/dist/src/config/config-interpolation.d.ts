import { Diagnostic } from "../core/types.js";
import { TypeSpecConfig } from "./types.js";
export interface ExpandConfigOptions {
    readonly cwd: string;
    readonly outputDir?: string;
    readonly env?: Record<string, string | undefined>;
    readonly args?: Record<string, string>;
}
export declare function expandConfigVariables(config: TypeSpecConfig, expandOptions: ExpandConfigOptions): [TypeSpecConfig, readonly Diagnostic[]];
export declare function resolveValues<T extends Record<string, unknown>>(values: T, predefinedVariables?: Record<string, string | Record<string, string>>): [T, readonly Diagnostic[]];
//# sourceMappingURL=config-interpolation.d.ts.map