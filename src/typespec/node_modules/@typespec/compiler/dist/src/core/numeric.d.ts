export interface Numeric {
    /**
     * Return the value as JavaScript number or null if it cannot be represented without loosing precision.
     */
    asNumber(): number | null;
    asBigInt(): bigint | null;
    toString(): string;
    equals(value: Numeric): boolean;
    gt(value: Numeric): boolean;
    lt(value: Numeric): boolean;
    gte(value: Numeric): boolean;
    lte(value: Numeric): boolean;
    readonly isInteger: boolean;
}
export declare class InvalidNumericError extends Error {
    readonly code = "InvalidNumeric";
}
/**
 * Check if the given arg is a Numeric
 */
export declare function isNumeric(arg: unknown): arg is Numeric;
/**
 * Represent any possible numeric value
 */
export declare function Numeric(stringValue: string): Numeric;
//# sourceMappingURL=numeric.d.ts.map