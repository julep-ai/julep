import { SourceFile } from "../core/types.js";
export interface YamlScript {
    readonly kind: "yaml-script";
    readonly file: SourceFile;
    /** Value of the yaml script. */
    readonly value: unknown;
}
/**
 * Represent the location of a value in a yaml script.
 */
export interface YamlPathTarget {
    kind: "path-target";
    script: YamlScript;
    path: string[];
}
export type YamlDiagnosticTargetType = "value" | "key";
//# sourceMappingURL=types.d.ts.map