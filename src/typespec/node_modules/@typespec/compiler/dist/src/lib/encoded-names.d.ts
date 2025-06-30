import type { Program } from "../core/program.js";
import type { DecoratorContext, Type } from "../core/types.js";
export declare function $encodedName(context: DecoratorContext, target: Type, mimeType: string, name: string): void;
/**
 * Resolve the encoded name for the given type when serialized to the given mime type.
 * If a specific value was provided by `@encodedName` decorator for that mime type it will return that otherwise it will return the name of the type.
 *
 * @example
 *
 * For the given
 * ```tsp
 * model Certificate {
 *   @encodedName("application/json", "exp")
 *   @encodedName("application/xml", "expiry")
 *   expireAt: utcDateTime;
 *
 * }
 * ```
 *
 * ```ts
 * resolveEncodedName(program, type, "application/json") // exp
 * resolveEncodedName(program, type, "application/merge-patch+json") // exp
 * resolveEncodedName(program, type, "application/xml") // expireAt
 * resolveEncodedName(program, type, "application/yaml") // expiry
 * ```
 */
export declare function resolveEncodedName(program: Program, target: Type & {
    name: string;
}, mimeType: string): string;
//# sourceMappingURL=encoded-names.d.ts.map