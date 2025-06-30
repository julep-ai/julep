import { getSourceLocation } from "../diagnostics.js";
export function getLocationContext(program, type) {
    const sourceLocation = getSourceLocation(type);
    if (sourceLocation.isSynthetic) {
        return { type: "synthetic" };
    }
    return program.getSourceFileLocationContext(sourceLocation.file);
}
//# sourceMappingURL=location-context.js.map