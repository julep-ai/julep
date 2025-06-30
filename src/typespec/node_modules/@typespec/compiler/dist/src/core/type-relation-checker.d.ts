import { Checker } from "./checker.js";
import { Program } from "./program.js";
import { Diagnostic, Entity, IndeterminateEntity, Model, Node, Scalar, Type, Value } from "./types.js";
export interface TypeRelation {
    isTypeAssignableTo(source: Entity | IndeterminateEntity, target: Entity, diagnosticTarget: Entity | Node): [boolean, readonly Diagnostic[]];
    isValueOfType(source: Value, target: Type, diagnosticTarget: Entity | Node): [boolean, readonly Diagnostic[]];
    isReflectionType(type: Type): type is Model & {
        name: ReflectionTypeName;
    };
    areScalarsRelated(source: Scalar, target: Scalar): boolean;
}
/**
 * Mapping from the reflection models to Type["kind"] value
 */
declare const ReflectionNameToKind: {
    readonly Enum: "Enum";
    readonly EnumMember: "EnumMember";
    readonly Interface: "Interface";
    readonly Model: "Model";
    readonly ModelProperty: "ModelProperty";
    readonly Namespace: "Namespace";
    readonly Operation: "Operation";
    readonly Scalar: "Scalar";
    readonly TemplateParameter: "TemplateParameter";
    readonly Tuple: "Tuple";
    readonly Union: "Union";
    readonly UnionVariant: "UnionVariant";
};
type ReflectionTypeName = keyof typeof ReflectionNameToKind;
export declare function createTypeRelationChecker(program: Program, checker: Checker): TypeRelation;
export {};
//# sourceMappingURL=type-relation-checker.d.ts.map