import type { Logger, LogLevel, LogSink } from "../types.js";
export interface LoggerOptions {
    sink: LogSink;
    level?: LogLevel;
}
export declare function createLogger(options: LoggerOptions): Logger;
//# sourceMappingURL=logger.d.ts.map