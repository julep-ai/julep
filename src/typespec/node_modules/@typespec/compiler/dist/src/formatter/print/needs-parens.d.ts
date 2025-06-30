import type { AstPath } from "prettier";
import { Node } from "../../core/types.js";
import { TypeSpecPrettierOptions } from "./types.js";
/**
 * Check if the current path should be wrapped in parentheses
 * @param path Prettier print path.
 * @param options Prettier options
 */
export declare function needsParens(path: AstPath<Node>, options: TypeSpecPrettierOptions): boolean;
//# sourceMappingURL=needs-parens.d.ts.map