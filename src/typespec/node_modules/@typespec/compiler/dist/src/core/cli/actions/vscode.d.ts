import { Diagnostic } from "../../types.js";
import { CliCompilerHost } from "../types.js";
export interface InstallVSCodeExtensionOptions {
    insiders: boolean;
}
export declare function installVSCodeExtension(host: CliCompilerHost, options: InstallVSCodeExtensionOptions): Promise<readonly Diagnostic[]>;
export interface UninstallVSCodeExtensionOptions {
    insiders: boolean;
}
export declare function uninstallVSCodeExtension(host: CliCompilerHost, options: UninstallVSCodeExtensionOptions): Promise<readonly Diagnostic[]>;
//# sourceMappingURL=vscode.d.ts.map