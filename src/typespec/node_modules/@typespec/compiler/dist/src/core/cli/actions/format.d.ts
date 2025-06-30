import { CliCompilerHost } from "../types.js";
export interface FormatArgs {
    include: string[];
    exclude?: string[];
    debug?: boolean;
    check?: boolean;
}
export declare function formatAction(host: CliCompilerHost, args: FormatArgs): Promise<void>;
//# sourceMappingURL=format.d.ts.map