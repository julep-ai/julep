/**
 * Helper class to track duplicate instance
 */
export declare class DuplicateTracker<K, V> {
    #private;
    /**
     * Track usage of K.
     * @param k key that is being checked for duplicate.
     * @param v value that map to the key
     */
    track(k: K, v: V): void;
    /**
     * Return iterator of all the duplicate entries.
     */
    entries(): Iterable<[K, V[]]>;
}
//# sourceMappingURL=duplicate-tracker.d.ts.map