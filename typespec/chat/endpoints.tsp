import "@typespec/http";

import "../common";
import "../sessions";
import "./models.tsp";

using TypeSpec.Http;

using Common;
using Sessions;

namespace Chat;

//
// CHAT ENDPOINTS
//

interface Endpoints {
    @post
    @doc("Generate a response from the model")
    generate(
        @path
        @doc("The session ID")
        id: uuid;

        @header
        @doc("Custom API key")
        "X-Custom-Api-Key"?: string;

        @bodyRoot
        @doc("Request to generate a response from the model")
        body: ChatInput;
    ): {
        @statusCode _: "200";

        @bodyRoot
        @doc("Response from the model")
        body: ChatResponse;
    } | {
        @statusCode _: "200";
        
        @header
        @doc("Content type for streaming responses")
        "content-type": "text/event-stream";

        @bodyRoot
        @doc("Streaming response from the model")
        body: ChunkChatResponse;
    };
}

interface RenderEndpoints {
    @post
    @doc("Render system prompt for the session")
    render(
        @path
        @doc("The session ID")
        id: uuid;

        @bodyRoot
        @doc("Request to render the system prompt for the session")
        body: ChatInput;
    ): {
        @statusCode _: "200";

        @bodyRoot
        @doc("Response from the model")
        body: RenderResponse;
    };
}
