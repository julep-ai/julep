// FORK of https://github.com/jamestalmage/supports-hyperlinks that work on new windows terminal and some more unix terminals.
// and doesn't include some of the cli flags that won't work with our strict cli.
/**
 * Check if the terminal supports hyperlink.
 */
export function supportsHyperlink(stream) {
    const { CI, TERM, TERM_PROGRAM, TERM_PROGRAM_VERSION, VTE_VERSION, FORCE_HYPERLINK, COLORTERM, TERMINAL_EMULATOR, } = process.env;
    if (FORCE_HYPERLINK) {
        return !(FORCE_HYPERLINK.length > 0 && parseInt(FORCE_HYPERLINK, 10) === 0);
    }
    if (stream && !stream.isTTY) {
        return false;
    }
    if ("WT_SESSION" in process.env) {
        return true;
    }
    if (process.platform === "win32") {
        return false;
    }
    if (CI) {
        return false;
    }
    if (TERM_PROGRAM) {
        const version = parseVersion(TERM_PROGRAM_VERSION || "");
        switch (TERM_PROGRAM) {
            case "iTerm.app":
                if (version.major === 3) {
                    return version.minor >= 1;
                }
                return version.major > 3;
            case "WezTerm":
                return version.major >= 20200620;
            case "vscode":
                return version.major > 1 || (version.major === 1 && version.minor >= 72);
            // No default
        }
    }
    /* cspell:disable-next-line */
    if (TERM && ["xterm-kitty", "alacritty", "alacritty-direct"].includes(TERM)) {
        return true;
    }
    if (COLORTERM === "xfce4-terminal") {
        return true;
    }
    if (TERMINAL_EMULATOR === "JetBrains-JediTerm") {
        return true;
    }
    if (VTE_VERSION) {
        // 0.50.0 was supposed to support hyperlinks, but throws a segfault
        if (VTE_VERSION === "0.50.0") {
            return false;
        }
        const version = parseVersion(VTE_VERSION);
        return version.major > 0 || version.minor >= 50;
    }
    return false;
}
function parseVersion(versionString) {
    if (/^\d{3,4}$/.test(versionString)) {
        // Env var doesn't always use dots. example: 4601 => 46.1.0
        const m = /(\d{1,2})(\d{2})/.exec(versionString) || [];
        return {
            major: 0,
            minor: parseInt(m[1], 10),
            patch: parseInt(m[2], 10),
        };
    }
    const versions = (versionString || "").split(".").map((n) => parseInt(n, 10));
    return {
        major: versions[0],
        minor: versions[1],
        patch: versions[2],
    };
}
//# sourceMappingURL=support-hyperlinks.js.map