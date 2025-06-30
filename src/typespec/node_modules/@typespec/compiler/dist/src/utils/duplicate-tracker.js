/**
 * Helper class to track duplicate instance
 */
export class DuplicateTracker {
    #entries = new Map();
    /**
     * Track usage of K.
     * @param k key that is being checked for duplicate.
     * @param v value that map to the key
     */
    track(k, v) {
        const existing = this.#entries.get(k);
        if (existing === undefined) {
            this.#entries.set(k, [v]);
        }
        else {
            existing.push(v);
        }
    }
    /**
     * Return iterator of all the duplicate entries.
     */
    *entries() {
        for (const [k, v] of this.#entries.entries()) {
            if (v.length > 1) {
                yield [k, v];
            }
        }
    }
}
//# sourceMappingURL=duplicate-tracker.js.map