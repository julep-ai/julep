import type { Program } from "./program.js";
import { Node, Type } from "./types.js";
/**
 * Provides details on the deprecation of a given type.
 */
export interface DeprecationDetails {
    /**
     * The deprecation message to display when the type is used.
     */
    message: string;
}
/**
 * Check if the given type is deprecated
 * @param program Program
 * @param type Type
 */
export declare function isDeprecated(program: Program, type: Type): boolean;
/**
 * Returns complete deprecation details for the given type or node
 * @param program Program
 * @param typeOrNode A Type or Node to check for deprecation
 */
export declare function getDeprecationDetails(program: Program, typeOrNode: Type | Node): DeprecationDetails | undefined;
/**
 * Mark the given type as deprecated with the provided details.
 * @param program Program
 * @param type Type
 * @param details Details of the deprecation
 */
export declare function markDeprecated(program: Program, type: Type, details: DeprecationDetails): void;
//# sourceMappingURL=deprecation.d.ts.map