import { isArray } from "../../utils/misc.js";
// prettier-ignore
export var UsageFlags;
(function (UsageFlags) {
    UsageFlags[UsageFlags["None"] = 0] = "None";
    UsageFlags[UsageFlags["Input"] = 2] = "Input";
    UsageFlags[UsageFlags["Output"] = 4] = "Output";
})(UsageFlags || (UsageFlags = {}));
/**
 * Resolve usage(input, output or both) of various types in the given namespace.
 * Will recursively scan all namespace, interfaces and operations contained inside the namespace.
 * @param types Entrypoint(s) namespace, interface or operations to get usage from.
 * @returns Map of types to usage.
 */
export function resolveUsages(types) {
    const usages = new Map();
    if (isArray(types)) {
        for (const item of types) {
            addUsagesInContainer(item, usages);
        }
    }
    else {
        addUsagesInContainer(types, usages);
    }
    return {
        types: [...usages.keys()],
        isUsedAs: (type, usage) => {
            const used = usages.get(type);
            if (used === undefined) {
                return false;
            }
            return Boolean(used & usage);
        },
    };
}
function addUsagesInContainer(type, usages) {
    switch (type.kind) {
        case "Namespace":
            addUsagesInNamespace(type, usages);
            break;
        case "Interface":
            addUsagesInInterface(type, usages);
            break;
        case "Operation":
            addUsagesInOperation(type, usages);
            break;
    }
}
function trackUsage(usages, type, usage) {
    const existingFlag = usages.get(type) ?? UsageFlags.None;
    usages.set(type, existingFlag | usage);
}
function addUsagesInNamespace(namespace, usages) {
    for (const subNamespace of namespace.namespaces.values()) {
        addUsagesInNamespace(subNamespace, usages);
    }
    for (const Interface of namespace.interfaces.values()) {
        addUsagesInInterface(Interface, usages);
    }
    for (const operation of namespace.operations.values()) {
        addUsagesInOperation(operation, usages);
    }
}
function addUsagesInInterface(Interface, usages) {
    for (const operation of Interface.operations.values()) {
        addUsagesInOperation(operation, usages);
    }
}
function addUsagesInOperation(operation, usages) {
    navigateReferencedTypes(operation.parameters, (type) => trackUsage(usages, type, UsageFlags.Input));
    navigateReferencedTypes(operation.returnType, (type) => trackUsage(usages, type, UsageFlags.Output));
}
function navigateReferencedTypes(type, callback, visited = new Set()) {
    if (visited.has(type)) {
        return;
    }
    visited.add(type);
    switch (type.kind) {
        case "Model":
            callback(type);
            navigateIterable(type.properties, callback, visited);
            navigateIterable(type.derivedModels, callback, visited);
            type.indexer?.value && navigateReferencedTypes(type.indexer.value, callback, visited);
            break;
        case "ModelProperty":
            navigateReferencedTypes(type.type, callback, visited);
            break;
        case "Union":
            callback(type);
            navigateIterable(type.variants, callback, visited);
            break;
        case "UnionVariant":
            navigateReferencedTypes(type.type, callback, visited);
            break;
        case "Enum":
        case "Tuple":
            callback(type);
            break;
    }
}
function navigateIterable(map, callback, visited = new Set()) {
    for (const type of map.values()) {
        navigateReferencedTypes(type, callback, visited);
    }
}
//# sourceMappingURL=usage-resolver.js.map