import "../dist/src/decorators.js";

using TypeSpec.Reflection;

namespace TypeSpec.Versioning;

/**
 * Identifies that the decorated namespace is versioned by the provided enum.
 * @param versions The enum that describes the supported versions.
 *
 * @example
 *
 * ```tsp
 * @versioned(Versions)
 * namespace MyService;
 * enum Versions {
 *   v1,
 *   v2,
 *   v3,
 * }
 * ```
 */
extern dec versioned(target: Namespace, versions: Enum);

/**
 * Identifies that a namespace or a given versioning enum member relies upon a versioned package.
 * @param versionRecords The dependent library version(s) for the target namespace or version.
 *
 * @example Select a single version of `MyLib` to use
 *
 * ```tsp
 * @useDependency(MyLib.Versions.v1_1)
 * namespace NonVersionedService;
 * ```
 *
 * @example Select which version of the library match to which version of the service.
 *
 * ```tsp
 * @versioned(Versions)
 * namespace MyService1;
 * enum Version {
 *   @useDependency(MyLib.Versions.v1_1) // V1 use lib v1_1
 *   v1,
 *   @useDependency(MyLib.Versions.v1_1) // V2 use lib v1_1
 *   v2,
 *   @useDependency(MyLib.Versions.v2) // V3 use lib v2
 *   v3,
 * }
 * ```
 */
extern dec useDependency(target: EnumMember | Namespace, ...versionRecords: EnumMember[]);

/**
 * Identifies when the target was added.
 * @param version The version that the target was added in.
 *
 * @example
 *
 * ```tsp
 * @added(Versions.v2)
 * op addedInV2(): void;
 *
 * @added(Versions.v2)
 * model AlsoAddedInV2 {}
 *
 * model Foo {
 *   name: string;
 *
 *   @added(Versions.v3)
 *   addedInV3: string;
 * }
 * ```
 */
extern dec added(
  target:
    | Model
    | ModelProperty
    | Operation
    | Enum
    | EnumMember
    | Union
    | UnionVariant
    | Scalar
    | Interface,
  version: EnumMember
);

/**
 * Identifies when the target was removed.
 * @param version The version that the target was removed in.
 *
 * @example
 * ```tsp
 * @removed(Versions.v2)
 * op removedInV2(): void;
 *
 * @removed(Versions.v2)
 * model AlsoRemovedInV2 {}
 *
 * model Foo {
 *   name: string;
 *
 *   @removed(Versions.v3)
 *   removedInV3: string;
 * }
 * ```
 */
extern dec removed(
  target:
    | Model
    | ModelProperty
    | Operation
    | Enum
    | EnumMember
    | Union
    | UnionVariant
    | Scalar
    | Interface,
  version: EnumMember
);

/**
 * Identifies when the target has been renamed.
 * @param version The version that the target was renamed in.
 * @param oldName The previous name of the target.
 *
 * @example
 * ```tsp
 * @renamedFrom(Versions.v2, "oldName")
 * op newName(): void;
 * ```
 */
extern dec renamedFrom(
  target:
    | Model
    | ModelProperty
    | Operation
    | Enum
    | EnumMember
    | Union
    | UnionVariant
    | Scalar
    | Interface,
  version: EnumMember,
  oldName: valueof string
);

/**
 * Identifies when a target was made optional.
 * @param version The version that the target was made optional in.
 *
 * @example
 *
 * ```tsp
 * model Foo {
 *   name: string;
 *   @madeOptional(Versions.v2)
 *   nickname?: string;
 * }
 * ```
 */
extern dec madeOptional(target: ModelProperty, version: EnumMember);

/**
 * Identifies when a target was made required.
 * @param version The version that the target was made required in.
 *
 * @example
 *
 * ```tsp
 * model Foo {
 *   name: string;
 *   @madeRequired(Versions.v2)
 *   nickname: string;
 * }
 * ```
 */
extern dec madeRequired(target: ModelProperty, version: EnumMember);

/**
 * Identifies when the target type changed.
 * @param version The version that the target type changed in.
 * @param oldType The previous type of the target.
 */
extern dec typeChangedFrom(target: ModelProperty, version: EnumMember, oldType: unknown);

/**
 * Identifies when the target type changed.
 * @param version The version that the target type changed in.
 * @param oldType The previous type of the target.
 */
extern dec returnTypeChangedFrom(target: Operation, version: EnumMember, oldType: unknown);
