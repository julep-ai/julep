export function createFileSystemCache({ fileService, log, }) {
    const cache = new Map();
    let changes = [];
    return {
        async get(path) {
            for (const change of changes) {
                const path = await fileService.fileURLToRealPath(change.uri);
                log({
                    level: "trace",
                    message: `FileSystemCache entry with key '${path}' removed`,
                });
                cache.delete(path);
            }
            changes = [];
            const r = cache.get(path);
            if (!r) {
                let callstack;
                try {
                    const target = {};
                    // some browser doesn't support Error.captureStackTrace (i.e. Firefox)
                    if (typeof Error.captureStackTrace === "function") {
                        Error.captureStackTrace(target);
                        callstack = target.stack.substring("Error\n".length);
                    }
                }
                catch {
                    // just ignore the error, we don't want tracing error to impact normal functionality
                }
                log({ level: "trace", message: `FileSystemCache miss for ${path}`, detail: callstack });
            }
            return r;
        },
        set(path, entry) {
            cache.set(path, entry);
        },
        async setData(path, data) {
            const entry = await this.get(path);
            if (entry) {
                entry.data = data;
            }
        },
        notify(events) {
            changes.push(...events);
        },
    };
}
//# sourceMappingURL=file-system-cache.js.map