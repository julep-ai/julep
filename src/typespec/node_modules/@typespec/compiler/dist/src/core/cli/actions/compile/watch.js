import { watch } from "fs";
import { pathToFileURL } from "url";
export function createWatcher(onFileChanged) {
    const current = new Map();
    const dupFilter = createDupsFilter();
    return { updateWatchedFiles, close };
    function watchFile(file) {
        const watcher = watch(file, dupFilter((event, _name) => {
            onFileChanged(event, file);
        }));
        return watcher;
    }
    function close() {
        for (const watcher of current.values()) {
            watcher.close();
        }
    }
    function updateWatchedFiles(files) {
        const cleanup = new Set(current.keys());
        for (const file of files) {
            if (!current.has(file)) {
                current.set(file, watchFile(file));
            }
            cleanup.delete(file);
        }
        for (const file of cleanup) {
            current.get(file)?.close();
            current.delete(file);
        }
    }
}
export function createWatchHost(host) {
    let count = 0;
    return {
        ...host,
        forceJSReload,
        getJsImport: (path) => import(pathToFileURL(path).href + `?=${count}`),
    };
    function forceJSReload() {
        count++;
    }
}
function createDupsFilter() {
    let memo = {};
    return function (fn) {
        return function (event, name) {
            if (name === null) {
                return;
            }
            memo[name] = [event, name];
            setTimeout(function () {
                Object.values(memo).forEach((args) => {
                    fn(...args);
                });
                memo = {};
            });
        };
    };
}
//# sourceMappingURL=watch.js.map