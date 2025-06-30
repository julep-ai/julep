import { WatchEventType } from "fs";
import { CompilerHost } from "../../../types.js";
import { CliCompilerHost } from "../../types.js";
export interface ProjectWatcher {
    /** Set the files to watch. */
    readonly updateWatchedFiles: (files: string[]) => void;
    /** Close the watcher. */
    readonly close: () => void;
}
export interface WatchHost extends CompilerHost {
    forceJSReload(): void;
}
export declare function createWatcher(onFileChanged: (event: WatchEventType, name: string) => void): ProjectWatcher;
export declare function createWatchHost(host: CliCompilerHost): WatchHost;
//# sourceMappingURL=watch.d.ts.map