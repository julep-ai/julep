import "../../common";

using Common;

namespace Tools;

alias BrowserbaseSessionMethod = (
    /** Get live URLs from the browserbase context */
    | "get_live_urls"

    /** List the sessions in the browserbase context */
    | "list_sessions"

    /** Create a new session in the browserbase context */
    | "create_session"

    /** Get a session from the browserbase context */
    | "get_session"

    /** Update a session in the browserbase context */
    | "update_session"

    // TODO: Implement these
    | "create_context"
    | "upload_extension"
    | "get_extension"
    | "delete_extension"
    | "create_session_uploads"
    | "get_session_downloads"
    | "get_logs"
    | "get_recordings"
);

alias BrowserbaseSessionIntegrationDef =
    | BrowserbaseListSessionsIntegrationDef
    | BrowserbaseCreateSessionIntegrationDef
    | BrowserbaseGetSessionIntegrationDef
    | BrowserbaseUpdateSessionIntegrationDef
    | BrowserbaseGetSessionLiveUrlsIntegrationDef;
//
// TODO: Implement these
// | BrowserbaseCreateContextIntegrationDef
// | BrowserbaseUploadExtensionIntegrationDef
// | BrowserbaseGetExtensionIntegrationDef
// | BrowserbaseDeleteExtensionIntegrationDef
// | BrowserbaseCreateSessionUploadsIntegrationDef
// | BrowserbaseGetSessionDownloadsIntegrationDef
// | BrowserbaseGetLogsIntegrationDef
// | BrowserbaseGetRecordingsIntegrationDef

alias BrowserbaseSessionArguments =
    | BrowserbaseListSessionsArguments
    | BrowserbaseCreateSessionArguments
    | BrowserbaseGetSessionArguments
    | BrowserbaseUpdateSessionArguments
    | BrowserbaseGetSessionLiveUrlsArguments;
//
// TODO: Implement these
// | BrowserbaseCreateContextArguments
// | BrowserbaseUploadExtensionArguments
// | BrowserbaseGetExtensionArguments
// | BrowserbaseDeleteExtensionArguments
// | BrowserbaseCreateSessionUploadsArguments
// | BrowserbaseGetSessionDownloadsArguments
// | BrowserbaseGetLogsArguments
// | BrowserbaseGetRecordingsArguments

alias BrowserbaseSessionOutput =
    | BrowserbaseListSessionsOutput
    | BrowserbaseCreateSessionOutput
    | BrowserbaseGetSessionOutput
    | BrowserbaseUpdateSessionOutput
    | BrowserbaseGetSessionLiveUrlsOutput;
//
// TODO: Implement these
// | BrowserbaseCreateContextOutput
// | BrowserbaseUploadExtensionOutput
// | BrowserbaseGetExtensionOutput
// | BrowserbaseDeleteExtensionOutput
// | BrowserbaseCreateSessionUploadsOutput
// | BrowserbaseGetSessionDownloadsOutput
// | BrowserbaseGetLogsOutput
// | BrowserbaseGetRecordingsOutput

/** browserbase list sessions integration definition */
model BrowserbaseListSessionsIntegrationDef
    extends BaseBrowserbaseIntegrationDef {
    /** The specific method of the integration to call */
    method: "list_sessions" = "list_sessions";

    /** The arguments for the method */
    arguments?: BrowserbaseListSessionsArguments;
}

model BrowserbaseListSessionsArguments {
    /** The status of the sessions to list (Available options: RUNNING, ERROR, TIMED_OUT, COMPLETED) */
    status?: "RUNNING" | "ERROR" | "TIMED_OUT" | "COMPLETED";
}

alias BrowserbaseListSessionsOutput = {
    id: string;
    createdAt: string;
    updatedAt: string;
    projectId: string;
    startedAt: string;
    endedAt: string;
    expiresAt: string;
    status: "RUNNING" | "ERROR" | "TIMED_OUT" | "COMPLETED";
    proxyBytes: uint64;
    avgCpuUsage: uint64;
    memoryUsage: uint64;
    keepAlive: boolean;
    contextId?: string;
}[];

/** browserbase create session integration definition */
model BrowserbaseCreateSessionIntegrationDef
    extends BaseBrowserbaseIntegrationDef {
    method: "create_session" = "create_session";

    /** The arguments for the method */
    arguments: BrowserbaseCreateSessionArguments;
}

model BrowserbaseCreateSessionArguments {
    /** The Project ID. Can be found in Settings. */
    projectId: string;

    /** The uploaded Extension ID. See Upload Extension. */
    extensionId?: string;

    /** Browser settings */
    browserSettings?: Record<unknown>;

    /** Duration in seconds after which the session will automatically end. Defaults to the Project's defaultTimeout. */
    timeout?: uint16;

    /** Set to true to keep the session alive even after disconnections. This is available on the Startup plan only. */
    keepAlive?: boolean;

    /** Proxy configuration. Can be true for default proxy, or an array of proxy configurations. */
    proxies?: boolean | Record<unknown>[];
}

model BrowserbaseCreateSessionOutput {
    id: string;
    createdAt: string;
    updatedAt: string;
    projectId: string;
    startedAt: string;
    endedAt: string;
    expiresAt: string;
    status: "RUNNING" | "ERROR" | "TIMED_OUT" | "COMPLETED";
    proxyBytes: uint64;
    avgCpuUsage: uint64;
    memoryUsage: uint64;
    keepAlive: boolean;
    contextId?: string;
}

/** browserbase get session integration definition */
model BrowserbaseGetSessionIntegrationDef
    extends BaseBrowserbaseIntegrationDef {
    method: "get_session" = "get_session";
    arguments: BrowserbaseGetSessionArguments;
}

model BrowserbaseGetSessionArguments {
    id: string;
}

model BrowserbaseGetSessionOutput {
    id: string;
    createdAt: string;
    updatedAt: string;
    projectId: string;
    startedAt: string;
    endedAt: string;
    expiresAt: string;
    status: "RUNNING" | "ERROR" | "TIMED_OUT" | "COMPLETED";
    proxyBytes: uint64;
    avgCpuUsage: uint64;
    memoryUsage: uint64;
    keepAlive: boolean;
    contextId?: string;
}

/** browserbase update session integration definition */
model BrowserbaseUpdateSessionIntegrationDef
    extends BaseBrowserbaseIntegrationDef {
    method: "update_session" = "update_session";
    arguments: BrowserbaseUpdateSessionArguments;
}

model BrowserbaseUpdateSessionArguments {
    id: string;
    status: "REQUEST_RELEASE";
}

model BrowserbaseUpdateSessionOutput {
    id: string;
    createdAt: string;
    updatedAt: string;
    projectId: string;
    startedAt: string;
    endedAt: string;
    expiresAt: string;
    status: "RUNNING" | "ERROR" | "TIMED_OUT" | "COMPLETED";
    proxyBytes: uint64;
    avgCpuUsage: uint64;
    memoryUsage: uint64;
    keepAlive: boolean;
    contextId?: string;
}

/** browserbase get session live urls integration definition */
model BrowserbaseGetSessionLiveUrlsIntegrationDef
    extends BaseBrowserbaseIntegrationDef {
    method: "get_live_urls" = "get_live_urls";
    arguments: BrowserbaseGetSessionLiveUrlsArguments;
}

model BrowserbaseGetSessionLiveUrlsArguments {
    id: string;
}

model BrowserbaseGetSessionLiveUrlsOutput {
    debuggerFullscreenUrl?: url;
    debuggerUrl?: url;
    wsUrl?: url;
    pages: {
        id?: string;
        url?: url;
        faviconUrl?: url;
        title?: string;
        debuggerUrl?: url;
        debuggerFullscreenUrl?: url;
    }[] = #[];
}
