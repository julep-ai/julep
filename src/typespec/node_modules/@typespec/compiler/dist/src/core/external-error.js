import { MANIFEST } from "../manifest.js";
export class ExternalError extends Error {
    info;
    constructor(info) {
        super(renderExternalErrorInfo(info));
        this.info = info;
        this.name = "ExternalError";
    }
    render(color) {
        return renderExternalErrorInfo(this.info, color);
    }
}
function renderExternalErrorInfo(info, color = (x) => x) {
    const { metadata, kind } = info;
    const msg = [
        color(kind === "emitter"
            ? `Emitter "${metadata.name}" crashed! This is a bug.`
            : `Library "${metadata.name}" $onValidate crashed! This is a bug.`, "red"),
    ];
    if (metadata.bugs?.url) {
        msg.push(`Please file an issue at ${color(metadata.bugs?.url, "cyan")}`);
    }
    else {
        msg.push(`Please contact library author to report this issue.`);
    }
    msg.push("");
    msg.push(color(getInnerError(info), "gray"));
    msg.push("");
    msg.push(getReportInfo(metadata, color));
    return msg.join("\n");
}
function getInnerError({ error }) {
    if (typeof error === "object" &&
        error !== null &&
        "stack" in error &&
        typeof error.stack === "string") {
        return error.stack;
    }
    else {
        return String(error);
    }
}
function getReportInfo(metadata, color) {
    const details = {
        "Library Version": metadata.version ?? "?",
        "TypeSpec Compiler Version": MANIFEST.version,
    };
    return [
        "-".repeat(50),
        ...Object.entries(details).map(([k, v]) => `${k.padEnd(30)} ${color(v, "yellow")}`),
        "-".repeat(50),
    ].join("\n");
}
//# sourceMappingURL=external-error.js.map