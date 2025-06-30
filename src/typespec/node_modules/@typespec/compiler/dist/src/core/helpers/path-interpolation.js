const VariableInterpolationRegex = /{([a-zA-Z-_.]+)}(\/|\.?)/g;
/**
 * Interpolate a path template
 * @param pathTemplate Path template
 * @param predefinedVariables Variables that can be used in the path template.
 * @returns
 */
export function interpolatePath(pathTemplate, predefinedVariables) {
    return pathTemplate.replace(VariableInterpolationRegex, (match, expression, suffix) => {
        const isPathSegment = suffix === "/" || suffix === ".";
        const resolved = resolveExpression(predefinedVariables, expression);
        if (resolved) {
            return isPathSegment ? `${resolved}${suffix}` : resolved;
        }
        return "";
    });
}
function resolveExpression(predefinedVariables, expression) {
    const segments = expression.split(".");
    let resolved = predefinedVariables;
    for (const segment of segments) {
        resolved = resolved[segment];
        if (resolved === undefined) {
            return undefined;
        }
    }
    if (typeof resolved === "string") {
        return resolved;
    }
    else {
        return undefined;
    }
}
//# sourceMappingURL=path-interpolation.js.map