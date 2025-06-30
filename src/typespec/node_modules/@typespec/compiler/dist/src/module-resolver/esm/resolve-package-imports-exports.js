import { resolvePackageTarget } from "./resolve-package-target.js";
import { InvalidModuleSpecifierError } from "./utils.js";
/** Implementation of PACKAGE_IMPORTS_EXPORTS_RESOLVE https://github.com/nodejs/node/blob/main/doc/api/esm.md */
export async function resolvePackageImportsExports(context, { matchKey, matchObj, isImports }) {
    // If matchKey is a key of matchObj and does not contain "*", then
    if (!matchKey.includes("*") && matchKey in matchObj) {
        // Let target be the value of matchObj[matchKey].
        const target = matchObj[matchKey];
        // Return the result of PACKAGE_TARGET_RESOLVE(packageURL, target, null, isImports, conditions).
        const resolved = await resolvePackageTarget(context, { target, patternMatch: "", isImports });
        return resolved;
    }
    // Let expansionKeys be the list of keys of matchObj containing only a single "*"
    const expansionKeys = Object.keys(matchObj)
        // Assert: ends with "/" or contains only a single "*".
        .filter((k) => k.endsWith("/") || k.includes("*"))
        // sorted by the sorting function PATTERN_KEY_COMPARE which orders in descending order of specificity.
        .sort(nodePatternKeyCompare);
    // For each key expansionKey in expansionKeys, do
    for (const expansionKey of expansionKeys) {
        const indexOfAsterisk = expansionKey.indexOf("*");
        // Let patternBase be the substring of expansionKey up to but excluding the first "*" character.
        const patternBase = indexOfAsterisk === -1 ? expansionKey : expansionKey.substring(0, indexOfAsterisk);
        // If matchKey starts with but is not equal to patternBase, then
        if (matchKey.startsWith(patternBase) && matchKey !== patternBase) {
            // Let patternTrailer be the substring of expansionKey from the index after the first "*" character.
            const patternTrailer = indexOfAsterisk !== -1 ? expansionKey.substring(indexOfAsterisk + 1) : "";
            // If patternTrailer has zero length,
            if (patternTrailer.length === 0 ||
                // or if matchKey ends with patternTrailer and the length of matchKey is greater than or equal to the length of expansionKey, then
                (matchKey.endsWith(patternTrailer) && matchKey.length >= expansionKey.length)) {
                // Let target be the value of matchObj[expansionKey].
                const target = matchObj[expansionKey];
                // Let patternMatch be the substring of matchKey starting at the index of the length of patternBase up to the length
                // of matchKey minus the length of patternTrailer.
                const patternMatch = matchKey.substring(patternBase.length, matchKey.length - patternTrailer.length);
                // Return the result of PACKAGE_TARGET_RESOLVE
                const resolved = await resolvePackageTarget(context, {
                    target,
                    patternMatch,
                    isImports,
                });
                return resolved;
            }
        }
    }
    throw new InvalidModuleSpecifierError(context, isImports);
}
/**
 * Implementation of Node's `PATTERN_KEY_COMPARE` function
 */
function nodePatternKeyCompare(keyA, keyB) {
    // Let baseLengthA be the index of "*" in keyA plus one, if keyA contains "*", or the length of keyA otherwise.
    const baseLengthA = keyA.includes("*") ? keyA.indexOf("*") + 1 : keyA.length;
    // Let baseLengthB be the index of "*" in keyB plus one, if keyB contains "*", or the length of keyB otherwise.
    const baseLengthB = keyB.includes("*") ? keyB.indexOf("*") + 1 : keyB.length;
    // if baseLengthA is greater, return -1, if lower 1
    const rval = baseLengthB - baseLengthA;
    if (rval !== 0)
        return rval;
    // If keyA does not contain "*", return 1.
    if (!keyA.includes("*"))
        return 1;
    // If keyB does not contain "*", return -1.
    if (!keyB.includes("*"))
        return -1;
    // If the length of keyA is greater than the length of keyB, return -1.
    // If the length of keyB is greater than the length of keyA, return 1.
    // Else Return 0.
    return keyB.length - keyA.length;
}
//# sourceMappingURL=resolve-package-imports-exports.js.map