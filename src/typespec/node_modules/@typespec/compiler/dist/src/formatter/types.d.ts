import { IdentifierNode, NamespaceStatementNode } from "../core/types.js";
/**
 * Extended namespace type that will flatten namespace nodes when defined as `namespace Foo.Bar;` as a single node.
 * This is due to the fact that the namespace node for `Foo` and `Bar` have the same `pos` and `end` and this cause prettier to not be able to resolve where comments belong.
 */
export interface FlattenedNamespaceStatementNode extends NamespaceStatementNode {
    ids: IdentifierNode[];
}
//# sourceMappingURL=types.d.ts.map