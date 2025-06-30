import { mutate } from "../utils/misc.js";
/**
 * Create a new diagnostics creator.
 * @param diagnostics Map of the potential diagnostics.
 * @param libraryName Optional name of the library if in the scope of a library.
 * @returns @see DiagnosticCreator
 */
export function createDiagnosticCreator(diagnostics, libraryName) {
    const errorMessage = libraryName
        ? `It must match one of the code defined in the library '${libraryName}'`
        : "It must match one of the code defined in the compiler.";
    function createDiagnostic(diagnostic) {
        const diagnosticDef = diagnostics[diagnostic.code];
        if (!diagnosticDef) {
            const codeStr = Object.keys(diagnostics)
                .map((x) => ` - ${x}`)
                .join("\n");
            const code = String(diagnostic.code);
            throw new Error(`Unexpected diagnostic code '${code}'. ${errorMessage}. Defined codes:\n${codeStr}`);
        }
        const message = diagnosticDef.messages[diagnostic.messageId ?? "default"];
        if (!message) {
            const codeStr = Object.keys(diagnosticDef.messages)
                .map((x) => ` - ${x}`)
                .join("\n");
            const messageId = String(diagnostic.messageId);
            const code = String(diagnostic.code);
            throw new Error(`Unexpected message id '${messageId}'. ${errorMessage} for code '${code}'. Defined codes:\n${codeStr}`);
        }
        const messageStr = typeof message === "string" ? message : message(diagnostic.format);
        const result = {
            code: libraryName ? `${libraryName}/${String(diagnostic.code)}` : diagnostic.code.toString(),
            severity: diagnosticDef.severity,
            message: messageStr,
            target: diagnostic.target,
        };
        if (diagnosticDef.url) {
            mutate(result).url = diagnosticDef.url;
        }
        if (diagnostic.codefixes) {
            mutate(result).codefixes = diagnostic.codefixes;
        }
        return result;
    }
    function reportDiagnostic(program, diagnostic) {
        const diag = createDiagnostic(diagnostic);
        program.reportDiagnostic(diag);
    }
    return {
        diagnostics,
        createDiagnostic,
        reportDiagnostic,
    };
}
//# sourceMappingURL=diagnostic-creator.js.map