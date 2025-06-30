import { createDiagnostic } from "../../messages.js";
import { NoTarget } from "../../types.js";
import { installVsix } from "../install-vsix.js";
import { run } from "../utils.js";
export async function installVSCodeExtension(host, options) {
    return await installVsix(host, "typespec-vscode", (vsixPaths) => runCode(host, ["--install-extension", vsixPaths[0]], options.insiders));
}
export async function uninstallVSCodeExtension(host, options) {
    return runCode(host, ["--uninstall-extension", "microsoft.typespec-vscode"], options.insiders);
}
function runCode(host, codeArgs, insiders) {
    try {
        run(host, insiders ? "code-insiders" : "code", codeArgs, {
            // VS Code's CLI emits node warnings that we can't do anything about. Suppress them.
            extraEnv: { NODE_NO_WARNINGS: "1" },
            allowNotFound: true,
        });
        return [];
    }
    catch (error) {
        if (error.code === "ENOENT") {
            host.logger.trace(error.stack);
            return [
                createDiagnostic({
                    code: "vscode-in-path",
                    messageId: process.platform === "darwin" ? "osx" : "default",
                    target: NoTarget,
                }),
            ];
        }
        throw error;
    }
}
//# sourceMappingURL=vscode.js.map