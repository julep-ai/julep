import type { Doc, ParserOptions } from "prettier";
import { DecoratorExpressionNode } from "../../core/types.js";
export interface TypeSpecPrettierOptions extends ParserOptions {
}
export type PrettierChildPrint = (path: any) => Doc;
export interface DecorableNode {
    decorators: readonly DecoratorExpressionNode[];
}
//# sourceMappingURL=types.d.ts.map