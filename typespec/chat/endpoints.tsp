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
    };
}
