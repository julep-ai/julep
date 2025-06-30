import type { Parser, SupportLanguage } from "prettier";
import { Node } from "../core/types.js";
export declare const defaultOptions: {};
export declare const languages: SupportLanguage[];
export declare const parsers: {
    typespec: Parser<any>;
};
export declare const printers: {
    "typespec-format": import("prettier").Printer<Node>;
};
//# sourceMappingURL=index.d.ts.map