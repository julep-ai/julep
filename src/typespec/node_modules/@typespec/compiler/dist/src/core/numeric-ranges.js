import { Numeric } from "./numeric.js";
/**
 * Set of known numeric ranges
 */
export const numericRanges = {
    int64: [
        Numeric("-9223372036854775808"),
        Numeric("9223372036854775807"),
        { int: true, isJsNumber: false },
    ],
    int32: [Numeric("-2147483648"), Numeric("2147483647"), { int: true, isJsNumber: true }],
    int16: [Numeric("-32768"), Numeric("32767"), { int: true, isJsNumber: true }],
    int8: [Numeric("-128"), Numeric("127"), { int: true, isJsNumber: true }],
    uint64: [Numeric("0"), Numeric("18446744073709551615"), { int: true, isJsNumber: false }],
    uint32: [Numeric("0"), Numeric("4294967295"), { int: true, isJsNumber: true }],
    uint16: [Numeric("0"), Numeric("65535"), { int: true, isJsNumber: true }],
    uint8: [Numeric("0"), Numeric("255"), { int: true, isJsNumber: true }],
    safeint: [
        Numeric(Number.MIN_SAFE_INTEGER.toString()),
        Numeric(Number.MAX_SAFE_INTEGER.toString()),
        { int: true, isJsNumber: true },
    ],
    float32: [Numeric("-3.4e38"), Numeric("3.4e38"), { int: false, isJsNumber: true }],
    float64: [
        Numeric(`${-Number.MAX_VALUE}`),
        Numeric(Number.MAX_VALUE.toString()),
        { int: false, isJsNumber: true },
    ],
};
//# sourceMappingURL=numeric-ranges.js.map