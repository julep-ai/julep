import { resolvePath } from "../../core/path-utils.js";
import { InvalidModuleSpecifierError, InvalidPackageTargetError, isUrl, } from "./utils.js";
/** Implementation of PACKAGE_TARGET_RESOLVE https://github.com/nodejs/node/blob/main/doc/api/esm.md */
export async function resolvePackageTarget(context, { target, patternMatch, isImports }) {
    const { packageUrl } = context;
    const packageUrlWithTrailingSlash = packageUrl.endsWith("/") ? packageUrl : `${packageUrl}/`;
    // 1. If target is a String, then
    if (typeof target === "string") {
        // 1.i If target does not start with "./", then
        if (!target.startsWith("./")) {
            // 1.i.a If isImports is false, or if target starts with "../" or "/", or if target is a valid URL, then
            if (!isImports || target.startsWith("../") || target.startsWith("/") || isUrl(target)) {
                // 1.i.a.a Throw an Invalid Package Target error.
                throw new InvalidPackageTargetError(context, `Invalid mapping: "${target}".`);
            }
            // 1.i.b If patternMatch is a String, then
            if (typeof patternMatch === "string") {
                // 1.i.b.a Return PACKAGE_RESOLVE(target with every instance of "*" replaced by patternMatch, packageURL + "/")
                return await context.resolveId(target.replace(/\*/g, patternMatch), packageUrlWithTrailingSlash);
            }
            // 1.i.c Return PACKAGE_RESOLVE(target, packageURL + "/").
            return await context.resolveId(target, packageUrlWithTrailingSlash);
        }
        // 1.ii If target split on "/" or "\"
        checkInvalidSegment(context, target);
        // 1.iii Let resolvedTarget be the URL resolution of the concatenation of packageURL and target.
        const resolvedTarget = resolvePath(packageUrlWithTrailingSlash, target);
        // 1.iv Assert: resolvedTarget is contained in packageURL.
        if (!resolvedTarget.startsWith(packageUrl)) {
            throw new InvalidPackageTargetError(context, `Resolved to ${resolvedTarget} which is outside package ${packageUrl}`);
        }
        // 1.v If patternMatch is null, then
        if (!patternMatch) {
            // Return resolvedTarget.
            return resolvedTarget;
        }
        // 1.vi If patternMatch split on "/" or "\" contains invalid segments
        if (includesInvalidSegments(patternMatch.split(/\/|\\/), context.moduleDirs)) {
            // throw an Invalid Module Specifier error.
            throw new InvalidModuleSpecifierError(context);
        }
        // 1.vii Return the URL resolution of resolvedTarget with every instance of "*" replaced with patternMatch.
        return resolvedTarget.replace(/\*/g, patternMatch);
    }
    // 3. Otherwise, if target is an Array, then
    if (Array.isArray(target)) {
        // 3.i If _target.length is zero, return null.
        if (target.length === 0) {
            return null;
        }
        let lastError = null;
        // 3.ii For each item in target, do
        for (const item of target) {
            // Let resolved be the result of PACKAGE_TARGET_RESOLVE of the item
            // continuing the loop on any Invalid Package Target error.
            try {
                const resolved = await resolvePackageTarget(context, {
                    target: item,
                    patternMatch,
                    isImports,
                });
                // If resolved is undefined, continue the loop.
                // Else Return resolved.
                if (resolved !== undefined) {
                    return resolved;
                }
            }
            catch (error) {
                if (!(error instanceof InvalidPackageTargetError)) {
                    throw error;
                }
                else {
                    lastError = error;
                }
            }
        }
        // Return or throw the last fallback resolution null return or error
        if (lastError) {
            throw lastError;
        }
        return null;
    }
    // 2. Otherwise, if target is a non-null Object, then
    if (target && typeof target === "object") {
        // 2.ii For each property of target
        for (const [key, value] of Object.entries(target)) {
            // 2.ii.a If key equals "default" or conditions contains an entry for the key, then
            if ((key === "default" && !context.ignoreDefaultCondition) ||
                context.conditions.includes(key)) {
                // Let targetValue be the value of the property in target.
                // Let resolved be the result of PACKAGE_TARGET_RESOLVE of the targetValue
                const resolved = await resolvePackageTarget(context, {
                    target: value,
                    patternMatch,
                    isImports,
                });
                // If resolved is equal to undefined, continue the loop.
                // Return resolved.
                if (resolved !== undefined) {
                    return resolved;
                }
            }
        }
        // Return undefined.
        return undefined;
    }
    // Otherwise, if target is null, return null.
    if (target === null) {
        return null;
    }
    // Otherwise throw an Invalid Package Target error.
    throw new InvalidPackageTargetError(context, `Invalid exports field.`);
}
/**
 * Check for invalid path segments
 */
function includesInvalidSegments(pathSegments, moduleDirs) {
    const invalidSegments = ["", ".", "..", ...moduleDirs];
    // contains any "", ".", "..", or "node_modules" segments, including percent encoded variants
    return pathSegments.some((v) => invalidSegments.includes(v) || invalidSegments.includes(decodeURI(v)));
}
function checkInvalidSegment(context, target) {
    const pathSegments = target.split(/\/|\\/);
    // after the first "." segment
    const firstDot = pathSegments.indexOf(".");
    firstDot !== -1 && pathSegments.slice(firstDot);
    if (firstDot !== -1 &&
        firstDot < pathSegments.length - 1 &&
        includesInvalidSegments(pathSegments.slice(firstDot + 1), context.moduleDirs)) {
        throw new InvalidPackageTargetError(context, `Invalid mapping: "${target}".`);
    }
}
//# sourceMappingURL=resolve-package-target.js.map