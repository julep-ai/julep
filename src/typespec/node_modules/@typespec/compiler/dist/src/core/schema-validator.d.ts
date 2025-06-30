import { JSONSchemaType, JSONSchemaValidator } from "./types.js";
export interface JSONSchemaValidatorOptions {
    coerceTypes?: boolean;
    strict?: boolean;
}
export declare function createJSONSchemaValidator<T>(schema: JSONSchemaType<T>, options?: JSONSchemaValidatorOptions): JSONSchemaValidator;
/**
 * Converts a json pointer into a array of reference tokens
 */
export declare function parseJsonPointer(pointer: string): string[];
//# sourceMappingURL=schema-validator.d.ts.map