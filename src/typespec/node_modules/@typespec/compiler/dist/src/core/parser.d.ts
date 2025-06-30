import { Diagnostic, Expression, IdentifierContext, IdentifierNode, ImportStatementNode, Node, ParseOptions, PositionDetail, SourceFile, TextRange, TypeReferenceNode, TypeSpecScriptNode } from "./types.js";
export declare function parse(code: string | SourceFile, options?: ParseOptions): TypeSpecScriptNode;
export declare function parseStandaloneTypeReference(code: string | SourceFile): [TypeReferenceNode, readonly Diagnostic[]];
export type NodeCallback<T> = (c: Node) => T;
export declare function exprIsBareIdentifier(expr: Expression): expr is TypeReferenceNode & {
    target: IdentifierNode;
    arguments: [];
};
export declare function visitChildren<T>(node: Node, cb: NodeCallback<T>): T | undefined;
/**
 * check whether a position belongs to a range (excluding the start and end pos)
 * i.e. <range.pos>{<start to return true>...<end to return true>}<range.end>
 *
 * remark: if range.pos is -1 means no start point found, so return false
 *         if range.end is -1 means no end point found, so return true if position is greater than range.pos
 */
export declare function positionInRange(position: number, range: TextRange): boolean;
export declare function getNodeAtPositionDetail(script: TypeSpecScriptNode, position: number, filter?: (node: Node, flag: "cur" | "pre" | "post") => boolean): PositionDetail;
/**
 * Resolve the node in the syntax tree that that is at the given position.
 * @param script TypeSpec Script node
 * @param position Position
 * @param filter Filter if wanting to return a parent containing node early.
 */
export declare function getNodeAtPosition(script: TypeSpecScriptNode, position: number, filter?: (node: Node) => boolean): Node | undefined;
export declare function getNodeAtPosition<T extends Node>(script: TypeSpecScriptNode, position: number, filter: (node: Node) => node is T): T | undefined;
export declare function hasParseError(node: Node): number | true;
export declare function isImportStatement(node: Node): node is ImportStatementNode;
export declare function getFirstAncestor(node: Node, test: NodeCallback<boolean>, includeSelf?: boolean): Node | undefined;
export declare function getIdentifierContext(id: IdentifierNode): IdentifierContext;
//# sourceMappingURL=parser.d.ts.map