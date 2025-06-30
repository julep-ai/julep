import { Interface, Namespace, Operation } from "../types.js";
export interface ListOperationOptions {
    /**
     * If the container is a namespace look for operation in sub namespaces.
     * @default true
     */
    recursive?: boolean;
}
/**
 * List operations in the given container. Will list operation recursively by default(Check subnamespaces.)
 * @param container Container.
 * @param options Options.
 */
export declare function listOperationsIn(container: Namespace | Interface, options?: ListOperationOptions): Operation[];
//# sourceMappingURL=operation-utils.d.ts.map