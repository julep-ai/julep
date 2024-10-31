import "../../common";

using Common;

namespace Tools;

alias BrowserbaseSessionMethod =
    | /** Get live URLs from the browserbase context */
      "get_live_urls"
    | /** List the sessions in the browserbase context */
      "list_sessions"
    | /** Create a new session in the browserbase context */
      "create_session"
    | /** Get a session from the browserbase context */
      "get_session"
    | /** Complete a session in the browserbase context */
      "complete_session"
    | /** Get the connection URL for a session */
      "get_connect_url"
    | // TODO: Implement these
      "get_session_downloads"
    | "get_logs"
    | "get_recordings";

alias BrowserbaseSessionIntegrationDef =
    | BrowserbaseListSessionsIntegrationDef
    | BrowserbaseCreateSessionIntegrationDef
    | BrowserbaseGetSessionIntegrationDef
    | BrowserbaseCompleteSessionIntegrationDef
    | BrowserbaseGetSessionLiveUrlsIntegrationDef
    | BrowserbaseGetSessionConnectUrlIntegrationDef;
//
// TODO: Implement these
// | BrowserbaseCreateSessionUploadsIntegrationDef
// | BrowserbaseGetSessionDownloadsIntegrationDef
// | BrowserbaseGetLogsIntegrationDef
// | BrowserbaseGetRecordingsIntegrationDef

alias BrowserbaseSessionArguments =
    | BrowserbaseListSessionsArguments
    | BrowserbaseCreateSessionArguments
    | BrowserbaseGetSessionArguments
    | BrowserbaseCompleteSessionArguments
    | BrowserbaseGetSessionLiveUrlsArguments
    | BrowserbaseGetSessionConnectUrlArguments;
//
// TODO: Implement these
// | BrowserbaseCreateSessionUploadsArguments
// | BrowserbaseGetSessionDownloadsArguments
// | BrowserbaseGetLogsArguments
// | BrowserbaseGetRecordingsArguments

alias BrowserbaseSessionOutput =
    | BrowserbaseListSessionsOutput
    | BrowserbaseCreateSessionOutput
    | BrowserbaseGetSessionOutput
    | BrowserbaseCompleteSessionOutput
    | BrowserbaseGetSessionLiveUrlsOutput
    | BrowserbaseGetSessionConnectUrlOutput;
//
// TODO: Implement these
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
    createdAt?: string;
    updatedAt?: string;
    projectId?: string;
    startedAt?: string;
    endedAt?: string;
    expiresAt?: string;
    status?: "RUNNING" | "ERROR" | "TIMED_OUT" | "COMPLETED";
    proxyBytes?: uint64;
    avgCpuUsage?: uint64;
    memoryUsage?: uint64;
    keepAlive?: boolean;
    contextId?: string;
}[];

/** browserbase create session integration definition */
model BrowserbaseCreateSessionIntegrationDef
    extends BaseBrowserbaseIntegrationDef {
    method: "create_session" = "create_session";

    /** The arguments for the method */
    arguments?: BrowserbaseCreateSessionArguments;
}

model BrowserbaseCreateSessionArguments {
    /** The Project ID. Can be found in Settings. */
    projectId?: string;

    /** The installed Extension ID. See Install Extension from GitHub. */
    extensionId?: string;

    /** Browser settings */
    browserSettings?: Record<unknown> = #{};

    /** Duration in seconds after which the session will automatically end. Defaults to the Project's defaultTimeout. */
    timeout?: uint16 = 3600;

    /** Set to true to keep the session alive even after disconnections. This is available on the Startup plan only. */
    keepAlive?: boolean = false;

    /** Proxy configuration. Can be true for default proxy, or an array of proxy configurations. */
    proxies?: boolean | Record<unknown>[] = false;
}

model BrowserbaseCreateSessionOutput {
    id: string;
    createdAt?: string;
    projectId?: string;
    startedAt?: string;
    endedAt?: string;
    expiresAt?: string;
    status?: "RUNNING" | "ERROR" | "TIMED_OUT" | "COMPLETED";
    proxyBytes?: uint64;
    avgCpuUsage?: uint64;
    memoryUsage?: uint64;
    keepAlive?: boolean;
    contextId?: string;
}

/** browserbase get session integration definition */
model BrowserbaseGetSessionIntegrationDef
    extends BaseBrowserbaseIntegrationDef {
    method: "get_session" = "get_session";
    arguments?: BrowserbaseGetSessionArguments;
}

model BrowserbaseGetSessionArguments {
    id: string;
}

model BrowserbaseGetSessionOutput {
    id: string;
    createdAt?: string;
    projectId?: string;
    startedAt?: string;
    endedAt?: string;
    expiresAt?: string;
    status?: "RUNNING" | "ERROR" | "TIMED_OUT" | "COMPLETED";
    proxyBytes?: uint64;
    avgCpuUsage?: uint64;
    memoryUsage?: uint64;
    keepAlive?: boolean;
    contextId?: string;
}

/** browserbase complete session integration definition */
model BrowserbaseCompleteSessionIntegrationDef
    extends BaseBrowserbaseIntegrationDef {
    method: "complete_session" = "complete_session";
    arguments?: BrowserbaseCompleteSessionArguments;
}

model BrowserbaseCompleteSessionArguments {
    id: string;
    status?: "REQUEST_RELEASE" = "REQUEST_RELEASE";
}

model BrowserbaseCompleteSessionOutput {
    success: boolean;
}

/** browserbase get session live urls integration definition */
model BrowserbaseGetSessionLiveUrlsIntegrationDef
    extends BaseBrowserbaseIntegrationDef {
    method: "get_live_urls" = "get_live_urls";
    arguments?: BrowserbaseGetSessionLiveUrlsArguments;
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

/** browserbase get session connect url integration definition */
model BrowserbaseGetSessionConnectUrlIntegrationDef
    extends BaseBrowserbaseIntegrationDef {
    method: "get_connect_url" = "get_connect_url";
    arguments?: BrowserbaseGetSessionConnectUrlArguments;
}

model BrowserbaseGetSessionConnectUrlArguments {
    id: string;
}

model BrowserbaseGetSessionConnectUrlOutput {
    url: url;
}
