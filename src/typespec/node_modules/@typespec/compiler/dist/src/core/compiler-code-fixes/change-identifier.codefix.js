import { defineCodeFix, getSourceLocation } from "../diagnostics.js";
export function createChangeIdentifierCodeFix(node, newIdentifier) {
    return defineCodeFix({
        id: "change-identifier",
        label: `Change ${node.sv} to ${newIdentifier}`,
        fix: (context) => {
            const location = getSourceLocation(node);
            return context.replaceText(location, newIdentifier);
        },
    });
}
//# sourceMappingURL=change-identifier.codefix.js.map