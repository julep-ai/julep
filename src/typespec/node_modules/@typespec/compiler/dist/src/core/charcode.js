import { nonAsciiIdentifierMap } from "./nonascii.js";
export function utf16CodeUnits(codePoint) {
    return codePoint >= 0x10000 ? 2 : 1;
}
export function isHighSurrogate(ch) {
    return ch >= 0xd800 && ch <= 0xdbff;
}
export function isLowSurrogate(ch) {
    return ch >= 0xdc00 && ch <= 0xdfff;
}
export function isLineBreak(ch) {
    return ch === 10 /* CharCode.LineFeed */ || ch === 13 /* CharCode.CarriageReturn */;
}
export function isAsciiWhiteSpaceSingleLine(ch) {
    return (ch === 32 /* CharCode.Space */ ||
        ch === 9 /* CharCode.Tab */ ||
        ch === 11 /* CharCode.VerticalTab */ ||
        ch === 12 /* CharCode.FormFeed */);
}
export function isNonAsciiWhiteSpaceSingleLine(ch) {
    return (ch === 133 /* CharCode.NextLine */ || // not considered a line break
        ch === 8206 /* CharCode.LeftToRightMark */ ||
        ch === 8207 /* CharCode.RightToLeftMark */ ||
        ch === 8232 /* CharCode.LineSeparator */ ||
        ch === 8233 /* CharCode.ParagraphSeparator */);
}
export function isWhiteSpace(ch) {
    return isWhiteSpaceSingleLine(ch) || isLineBreak(ch);
}
export function isWhiteSpaceSingleLine(ch) {
    return (isAsciiWhiteSpaceSingleLine(ch) ||
        (ch > 127 /* CharCode.MaxAscii */ && isNonAsciiWhiteSpaceSingleLine(ch)));
}
export function trim(str) {
    let start = 0;
    let end = str.length - 1;
    if (!isWhiteSpace(str.charCodeAt(start)) && !isWhiteSpace(str.charCodeAt(end))) {
        return str;
    }
    while (isWhiteSpace(str.charCodeAt(start))) {
        start++;
    }
    while (isWhiteSpace(str.charCodeAt(end))) {
        end--;
    }
    return str.substring(start, end + 1);
}
export function isDigit(ch) {
    return ch >= 48 /* CharCode._0 */ && ch <= 57 /* CharCode._9 */;
}
export function isHexDigit(ch) {
    return (isDigit(ch) || (ch >= 65 /* CharCode.A */ && ch <= 70 /* CharCode.F */) || (ch >= 97 /* CharCode.a */ && ch <= 102 /* CharCode.f */));
}
export function isBinaryDigit(ch) {
    return ch === 48 /* CharCode._0 */ || ch === 49 /* CharCode._1 */;
}
export function isLowercaseAsciiLetter(ch) {
    return ch >= 97 /* CharCode.a */ && ch <= 122 /* CharCode.z */;
}
export function isAsciiIdentifierStart(ch) {
    return ((ch >= 65 /* CharCode.A */ && ch <= 90 /* CharCode.Z */) ||
        (ch >= 97 /* CharCode.a */ && ch <= 122 /* CharCode.z */) ||
        ch === 36 /* CharCode.$ */ ||
        ch === 95 /* CharCode._ */);
}
export function isAsciiIdentifierContinue(ch) {
    return ((ch >= 65 /* CharCode.A */ && ch <= 90 /* CharCode.Z */) ||
        (ch >= 97 /* CharCode.a */ && ch <= 122 /* CharCode.z */) ||
        (ch >= 48 /* CharCode._0 */ && ch <= 57 /* CharCode._9 */) ||
        ch === 36 /* CharCode.$ */ ||
        ch === 95 /* CharCode._ */);
}
export function isIdentifierStart(codePoint) {
    return (isAsciiIdentifierStart(codePoint) ||
        (codePoint > 127 /* CharCode.MaxAscii */ && isNonAsciiIdentifierCharacter(codePoint)));
}
export function isIdentifierContinue(codePoint) {
    return (isAsciiIdentifierContinue(codePoint) ||
        (codePoint > 127 /* CharCode.MaxAscii */ && isNonAsciiIdentifierCharacter(codePoint)));
}
export function isNonAsciiIdentifierCharacter(codePoint) {
    return lookupInNonAsciiMap(codePoint, nonAsciiIdentifierMap);
}
export function codePointBefore(text, pos) {
    if (pos <= 0 || pos > text.length) {
        return { char: undefined, size: 0 };
    }
    const ch = text.charCodeAt(pos - 1);
    if (!isLowSurrogate(ch) || !isHighSurrogate(text.charCodeAt(pos - 2))) {
        return { char: ch, size: 1 };
    }
    return { char: text.codePointAt(pos - 2), size: 2 };
}
function lookupInNonAsciiMap(codePoint, map) {
    // Perform binary search in one of the Unicode range maps
    let lo = 0;
    let hi = map.length;
    let mid;
    while (lo + 1 < hi) {
        mid = lo + (hi - lo) / 2;
        // mid has to be even to catch a range's beginning
        mid -= mid % 2;
        if (map[mid] <= codePoint && codePoint <= map[mid + 1]) {
            return true;
        }
        if (codePoint < map[mid]) {
            hi = mid;
        }
        else {
            lo = mid + 2;
        }
    }
    return false;
}
//# sourceMappingURL=charcode.js.map