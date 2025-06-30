import { createDiagnosticCollector } from "../../diagnostics.js";
import { createDiagnostic } from "../../messages.js";
import { joinPaths } from "../../path-utils.js";
import { NoTarget } from "../../types.js";
import { installVsix } from "../install-vsix.js";
import { run } from "../utils.js";
const VSIX_ALREADY_INSTALLED = 1001;
const VSIX_NOT_INSTALLED = 1002;
const VSIX_USER_CANCELED = 2005;
const VS_SUPPORTED_VERSION_RANGE = "[17.0,)";
export async function installVSExtension(host) {
    const diagnostics = createDiagnosticCollector();
    const vsixInstaller = diagnostics.pipe(getVsixInstallerPath());
    if (vsixInstaller === undefined) {
        return diagnostics.diagnostics;
    }
    if (!isVSInstalled(host, VS_SUPPORTED_VERSION_RANGE)) {
        return [
            createDiagnostic({
                code: "no-compatible-vs-installed",
                target: NoTarget,
            }),
        ];
    }
    await installVsix(host, "typespec-vs", (vsixPaths) => {
        for (const vsix of vsixPaths) {
            // eslint-disable-next-line no-console
            console.log(`Installing extension for Visual Studio...`);
            run(host, vsixInstaller, [vsix], {
                allowedExitCodes: [VSIX_ALREADY_INSTALLED, VSIX_USER_CANCELED],
            });
        }
    });
    return diagnostics.diagnostics;
}
export async function uninstallVSExtension(host) {
    const [vsixInstaller, diagnostics] = getVsixInstallerPath();
    if (vsixInstaller === undefined) {
        return diagnostics;
    }
    run(host, vsixInstaller, ["/uninstall:88b9492f-c019-492c-8aeb-f325a7e4cf23"], {
        allowedExitCodes: [VSIX_NOT_INSTALLED, VSIX_USER_CANCELED],
    });
    return diagnostics;
}
function getVsixInstallerPath() {
    return getVSInstallerPath("resources/app/ServiceHub/Services/Microsoft.VisualStudio.Setup.Service/VSIXInstaller.exe");
}
function getVSWherePath() {
    return getVSInstallerPath("vswhere.exe");
}
function getVSInstallerPath(relativePath) {
    if (process.platform !== "win32") {
        return [undefined, [createDiagnostic({ code: "vs-extension-windows-only", target: NoTarget })]];
    }
    return [
        joinPaths(process.env["ProgramFiles(x86)"] ?? "", "Microsoft Visual Studio/Installer", relativePath),
        [],
    ];
}
function isVSInstalled(host, versionRange) {
    const [vswhere] = getVSWherePath();
    if (vswhere === undefined) {
        return false;
    }
    const proc = run(host, vswhere, ["-property", "instanceid", "-prerelease", "-version", versionRange], {
        stdio: [null, "pipe", "inherit"],
        allowNotFound: true,
    });
    return proc.status === 0 && proc.stdout;
}
//# sourceMappingURL=vs.js.map