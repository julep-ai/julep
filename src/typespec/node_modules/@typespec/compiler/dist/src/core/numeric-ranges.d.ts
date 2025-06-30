import { Numeric } from "./numeric.js";
/**
 * Set of known numeric ranges
 */
export declare const numericRanges: {
    readonly int64: [Numeric, Numeric, {
        readonly int: true;
        readonly isJsNumber: false;
    }];
    readonly int32: [Numeric, Numeric, {
        readonly int: true;
        readonly isJsNumber: true;
    }];
    readonly int16: [Numeric, Numeric, {
        readonly int: true;
        readonly isJsNumber: true;
    }];
    readonly int8: [Numeric, Numeric, {
        readonly int: true;
        readonly isJsNumber: true;
    }];
    readonly uint64: [Numeric, Numeric, {
        readonly int: true;
        readonly isJsNumber: false;
    }];
    readonly uint32: [Numeric, Numeric, {
        readonly int: true;
        readonly isJsNumber: true;
    }];
    readonly uint16: [Numeric, Numeric, {
        readonly int: true;
        readonly isJsNumber: true;
    }];
    readonly uint8: [Numeric, Numeric, {
        readonly int: true;
        readonly isJsNumber: true;
    }];
    readonly safeint: [Numeric, Numeric, {
        readonly int: true;
        readonly isJsNumber: true;
    }];
    readonly float32: [Numeric, Numeric, {
        readonly int: false;
        readonly isJsNumber: true;
    }];
    readonly float64: [Numeric, Numeric, {
        readonly int: false;
        readonly isJsNumber: true;
    }];
};
//# sourceMappingURL=numeric-ranges.d.ts.map