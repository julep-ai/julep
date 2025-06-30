import type { DiagnosticCreator, DiagnosticMap, DiagnosticMessages } from "./types.js";
/**
 * Create a new diagnostics creator.
 * @param diagnostics Map of the potential diagnostics.
 * @param libraryName Optional name of the library if in the scope of a library.
 * @returns @see DiagnosticCreator
 */
export declare function createDiagnosticCreator<T extends {
    [code: string]: DiagnosticMessages;
}>(diagnostics: DiagnosticMap<T>, libraryName?: string): DiagnosticCreator<T>;
//# sourceMappingURL=diagnostic-creator.d.ts.map