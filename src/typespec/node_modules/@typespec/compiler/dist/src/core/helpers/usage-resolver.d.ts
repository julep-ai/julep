import { Enum, Interface, Model, Namespace, Operation, Tuple, Union } from "../types.js";
export declare enum UsageFlags {
    None = 0,
    Input = 2,
    Output = 4
}
export type TrackableType = Model | Enum | Union | Tuple;
export interface UsageTracker {
    readonly types: readonly TrackableType[];
    isUsedAs(type: TrackableType, usage: UsageFlags): boolean;
}
export type OperationContainer = Namespace | Interface | Operation;
/**
 * Resolve usage(input, output or both) of various types in the given namespace.
 * Will recursively scan all namespace, interfaces and operations contained inside the namespace.
 * @param types Entrypoint(s) namespace, interface or operations to get usage from.
 * @returns Map of types to usage.
 */
export declare function resolveUsages(types: OperationContainer | OperationContainer[]): UsageTracker;
//# sourceMappingURL=usage-resolver.d.ts.map