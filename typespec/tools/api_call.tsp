namespace Tools;

//
// API CALL MODELS
//

/** A valid HTTP method */
alias httpMethod = "GET" | "POST" | "PUT" | "DELETE" | "PATCH" | "HEAD" | "OPTIONS";

/** API call definition */
model ApiCallDef {
    /** The HTTP method to use */
    method: httpMethod;

    /** The URL to call */
    url: url;

    /** The headers to send with the request */
    headers?: Record<string>;

    /** The content as base64 to send with the request */
    content?: string;

    /** The data to send as form data */
    data?: Record<unknown>;

    /** JSON body to send with the request */
    json?: Record<unknown>;

    /** Cookies */
    cookies?: Record<string>;

    /** The parameters to send with the request */
    params?: string | Record<unknown>;

    /** Follow redirects */
    follow_redirects?: boolean = false;

    /** The timeout for the request */
    timeout?: uint8;
}
