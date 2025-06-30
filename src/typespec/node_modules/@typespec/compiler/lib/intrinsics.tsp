import "../dist/src/lib/intrinsic-decorators.js";

// This file contains all the intrinsic types of typespec. Everything here will always be loaded
namespace TypeSpec;

/**
 * Represent a byte array
 */
scalar bytes;

/**
 * A numeric type
 */
scalar numeric;

/**
 * A whole number. This represent any `integer` value possible.
 * It is commonly represented as `BigInteger` in some languages.
 */
scalar integer extends numeric;

/**
 * A number with decimal value
 */
scalar float extends numeric;

/**
 * A 64-bit integer. (`-9,223,372,036,854,775,808` to `9,223,372,036,854,775,807`)
 */
scalar int64 extends integer;

/**
 * A 32-bit integer. (`-2,147,483,648` to `2,147,483,647`)
 */
scalar int32 extends int64;

/**
 * A 16-bit integer. (`-32,768` to `32,767`)
 */
scalar int16 extends int32;

/**
 * A 8-bit integer. (`-128` to `127`)
 */
scalar int8 extends int16;

/**
 * A 64-bit unsigned integer (`0` to `18,446,744,073,709,551,615`)
 */
scalar uint64 extends integer;

/**
 * A 32-bit unsigned integer (`0` to `4,294,967,295`)
 */
scalar uint32 extends uint64;

/**
 * A 16-bit unsigned integer (`0` to `65,535`)
 */
scalar uint16 extends uint32;

/**
 * A 8-bit unsigned integer (`0` to `255`)
 */
scalar uint8 extends uint16;

/**
 * An integer that can be serialized to JSON (`−9007199254740991 (−(2^53 − 1))` to `9007199254740991 (2^53 − 1)` )
 */
scalar safeint extends int64;

/**
 * A 32 bit floating point number. (`±1.5 x 10^−45` to `±3.4 x 10^38`)
 */
scalar float64 extends float;

/**
 * A 32 bit floating point number. (`±5.0 × 10^−324` to `±1.7 × 10^308`)
 */
scalar float32 extends float64;

/**
 * A decimal number with any length and precision. This represent any `decimal` value possible.
 * It is commonly represented as `BigDecimal` in some languages.
 */
scalar decimal extends numeric;

/**
 * A 128-bit decimal number.
 */
scalar decimal128 extends decimal;

/**
 * A sequence of textual characters.
 */
scalar string;

/**
 * A date on a calendar without a time zone, e.g. "April 10th"
 */
scalar plainDate {
  /**
   * Create a plain date from an ISO 8601 string.
   * @example
   *
   * ```tsp
   * const time = plainTime.fromISO("2024-05-06");
   * ```
   */
  init fromISO(value: string);
}

/**
 * A time on a clock without a time zone, e.g. "3:00 am"
 */
scalar plainTime {
  /**
   * Create a plain time from an ISO 8601 string.
   * @example
   *
   * ```tsp
   * const time = plainTime.fromISO("12:34");
   * ```
   */
  init fromISO(value: string);
}

/**
 * An instant in coordinated universal time (UTC)"
 */
scalar utcDateTime {
  /**
   * Create a date from an ISO 8601 string.
   * @example
   *
   * ```tsp
   * const time = utcDateTime.fromISO("2024-05-06T12:20-12Z");
   * ```
   */
  init fromISO(value: string);
}

/**
 * A date and time in a particular time zone, e.g. "April 10th at 3:00am in PST"
 */
scalar offsetDateTime {
  /**
   * Create a date from an ISO 8601 string.
   * @example
   *
   * ```tsp
   * const time = offsetDateTime.fromISO("2024-05-06T12:20-12-0700");
   * ```
   */
  init fromISO(value: string);
}

/**
 * A duration/time period. e.g 5s, 10h
 */
scalar duration {
  /**
   * Create a duration from an ISO 8601 string.
   * @example
   *
   * ```tsp
   * const time = duration.fromISO("P1Y1D");
   * ```
   */
  init fromISO(value: string);
}

/**
 * Boolean with `true` and `false` values.
 */
scalar boolean;

/**
 * @dev Array model type, equivalent to `Element[]`
 * @template Element The type of the array elements
 */
@indexer(integer, Element)
model Array<Element> {}

/**
 * @dev Model with string properties where all the properties have type `Property`
 * @template Element The type of the properties
 */
@indexer(string, Element)
model Record<Element> {}
