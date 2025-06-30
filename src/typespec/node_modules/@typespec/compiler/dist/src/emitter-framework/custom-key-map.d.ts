/**
 * This is a map type that allows providing a custom keyer function. The keyer
 * function returns a string that is used to look up in the map. This is useful
 * for implementing maps that look up based on an arbitrary number of keys.
 *
 * For example, to look up in a map with a [ObjA, ObjB)] tuple, such that tuples
 * with identical values (but not necessarily identical tuples!) create an
 * object keyer for each of the objects:
 *
 *     const aKeyer = CustomKeyMap.objectKeyer();
 *     const bKeyer = CUstomKeyMap.objectKeyer();
 *
 * And compose these into a tuple keyer to use when instantiating the custom key
 * map:
 *
 *     const tupleKeyer = ([a, b]) => `${aKeyer.getKey(a)}-${bKeyer.getKey(b)}`;
 *     const map = new CustomKeyMap(tupleKeyer);
 *
 */
export declare class CustomKeyMap<K extends readonly any[], V> {
    #private;
    constructor(keyer: (args: K) => string);
    get(items: K): V | undefined;
    set(items: K, value: V): void;
    static objectKeyer(): {
        getKey(o: object): number | undefined;
    };
}
//# sourceMappingURL=custom-key-map.d.ts.map