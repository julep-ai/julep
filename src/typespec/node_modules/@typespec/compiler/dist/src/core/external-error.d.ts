import { LibraryMetadata } from "./types.js";
export type Colors = "reset" | "bold" | "dim" | "italic" | "underline" | "inverse" | "hidden" | "strikethrough" | "black" | "red" | "green" | "yellow" | "blue" | "magenta" | "cyan" | "white" | "gray" | "bgBlack" | "bgRed" | "bgGreen" | "bgYellow" | "bgBlue" | "bgMagenta" | "bgCyan" | "bgWhite";
export interface ExternalErrorInfo {
    kind: "emitter" | "validator";
    error: unknown;
    metadata: LibraryMetadata;
}
export type ColorFunction = (text: string, color: Colors) => string;
export declare class ExternalError extends Error {
    info: ExternalErrorInfo;
    constructor(info: ExternalErrorInfo);
    render(color: ColorFunction): string;
}
//# sourceMappingURL=external-error.d.ts.map