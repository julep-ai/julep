import { FileEvent } from "vscode-languageserver";
import { SourceFile } from "../core/types.js";
import { FileService } from "./file-service.js";
import { ServerLog } from "./types.js";
export interface FileSystemCache {
    get(path: string): Promise<CachedFile | CachedError | undefined>;
    set(path: string, entry: CachedFile | CachedError): void;
    setData(path: string, data: any): Promise<void>;
    notify(changes: FileEvent[]): void;
}
export interface CachedFile {
    type: "file";
    file: SourceFile;
    version?: number;
    data?: any;
}
export interface CachedError {
    type: "error";
    error: unknown;
    data?: any;
    version?: undefined;
}
export declare function createFileSystemCache({ fileService, log, }: {
    fileService: FileService;
    log: (log: ServerLog) => void;
}): FileSystemCache;
//# sourceMappingURL=file-system-cache.d.ts.map