import "./base.tsp";

using Tools;

namespace Tools;

// AIDEV-NOTE: Standalone API call definition extracted from models.tsp.

/** API call definition */
model ApiCallDef {
    /** The HTTP method to use */
    method: httpMethod;

    /** The URL to call */
    url: url;

    /** The schema of the response */
    schema?: Record<unknown>;

    /** The headers to send with the request */
    headers?: Record<string>;

    /** Secret references to use in templates (available only at setup time, not during execution) */
    secrets?: Record<SecretRef>;

    /** The content as base64 to send with the request */
    content?: string;

    /** The data to send as form data */
    data?: Record<unknown>;

    /** The data to send as files data */
    files?: Record<unknown>;

    /** JSON body to send with the request */
    json?: Record<unknown>;

    /** Cookies */
    cookies?: Record<string>;

    /** The parameters to send with the request */
    params?: string | Record<unknown>;

    /** Follow redirects */
    follow_redirects?: boolean;

    /** The timeout for the request */
    timeout?: uint8;

    /** Whether to include the content in the response */
    include_response_content?: boolean = true;
}
