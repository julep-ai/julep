import { DocumentSymbol, Range, SymbolKind } from "vscode-languageserver";
import { SyntaxKind } from "../core/types.js";
import { isArray, isDefined } from "../utils/misc.js";
export function getSymbolStructure(ast) {
    const file = ast.file;
    const fileNamespace = findFileNamespace(ast);
    if (fileNamespace === undefined) {
        return getForStatements(ast.statements);
    }
    const fileNamespaceSymbol = getForNamespace(fileNamespace);
    fileNamespaceSymbol.children = getForStatements(ast.statements.filter((x) => x !== fileNamespace));
    return [fileNamespaceSymbol];
    function findFileNamespace(ast) {
        const firstNamespace = ast.statements.find((x) => x.kind === SyntaxKind.NamespaceStatement);
        if (firstNamespace === undefined) {
            return undefined;
        }
        let current = firstNamespace;
        while (current.statements !== undefined &&
            !isArray(current.statements) &&
            current.statements?.kind === SyntaxKind.NamespaceStatement) {
            current = current.statements;
        }
        return current.statements === undefined ? firstNamespace : undefined;
    }
    function getDocumentSymbolsForNode(node) {
        switch (node.kind) {
            case SyntaxKind.NamespaceStatement:
                return getForNamespace(node);
            case SyntaxKind.ModelStatement:
                return getForModel(node);
            case SyntaxKind.ModelProperty:
                return createDocumentSymbol(node, getName(node.id), SymbolKind.Property);
            case SyntaxKind.ModelSpreadProperty:
                return getForModelSpread(node);
            case SyntaxKind.UnionStatement:
                return getForUnion(node);
            case SyntaxKind.UnionVariant:
                return node.id === undefined
                    ? undefined
                    : createDocumentSymbol(node, getName(node.id), SymbolKind.EnumMember);
            case SyntaxKind.EnumStatement:
                return getForEnum(node);
            case SyntaxKind.EnumMember:
                return createDocumentSymbol(node, getName(node.id), SymbolKind.EnumMember);
            case SyntaxKind.EnumSpreadMember:
                return getForEnumSpread(node);
            case SyntaxKind.InterfaceStatement:
                return getForInterface(node);
            case SyntaxKind.OperationStatement:
                return createDocumentSymbol(node, node.id.sv, SymbolKind.Function);
            case SyntaxKind.AliasStatement:
                return createDocumentSymbol(node, node.id.sv, SymbolKind.Variable);
            default:
                return undefined;
        }
    }
    function getForStatements(statements) {
        return statements.map(getDocumentSymbolsForNode).filter(isDefined);
    }
    function getForNamespace(namespace) {
        const names = [namespace.id.sv];
        let current = namespace;
        while (current.statements !== undefined &&
            !isArray(current.statements) &&
            current.statements?.kind === SyntaxKind.NamespaceStatement) {
            current = current.statements;
            names.push(current.id.sv);
        }
        const statementSymbols = current.statements ? getForStatements(current.statements) : [];
        return createDocumentSymbol(namespace, names.join("."), SymbolKind.Namespace, statementSymbols);
    }
    function createDocumentSymbol(node, name, kind, symbols) {
        const start = file.getLineAndCharacterOfPosition(node.pos);
        const end = file.getLineAndCharacterOfPosition(node.end);
        const range = Range.create(start, end);
        return DocumentSymbol.create(name, undefined, kind, range, range, symbols);
    }
    function getName(id) {
        return id.kind === SyntaxKind.Identifier ? id.sv : id.value;
    }
    function getForModel(node) {
        const properties = [...node.properties.values()]
            .map(getDocumentSymbolsForNode)
            .filter(isDefined);
        return createDocumentSymbol(node, node.id.sv, SymbolKind.Struct, properties);
    }
    function getForModelSpread(node) {
        const target = node.target.target;
        if (target.kind === SyntaxKind.Identifier) {
            return createDocumentSymbol(node, target.sv, SymbolKind.Property);
        }
        return getDocumentSymbolsForNode(target);
    }
    function getForEnum(node) {
        const members = [...node.members.values()]
            .map(getDocumentSymbolsForNode)
            .filter(isDefined);
        return createDocumentSymbol(node, node.id.sv, SymbolKind.Enum, members);
    }
    function getForEnumSpread(node) {
        const target = node.target.target;
        if (target.kind === SyntaxKind.Identifier) {
            return createDocumentSymbol(node, target.sv, SymbolKind.EnumMember);
        }
        return getDocumentSymbolsForNode(target);
    }
    function getForInterface(node) {
        const operations = [...node.operations.values()]
            .map(getDocumentSymbolsForNode)
            .filter(isDefined);
        return createDocumentSymbol(node, node.id.sv, SymbolKind.Interface, operations);
    }
    function getForUnion(node) {
        const variants = [...node.options.values()]
            .map(getDocumentSymbolsForNode)
            .filter(isDefined);
        return createDocumentSymbol(node, node.id.sv, SymbolKind.Enum, variants);
    }
}
//# sourceMappingURL=symbol-structure.js.map