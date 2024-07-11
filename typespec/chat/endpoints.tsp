import "@typespec/http";
import "@typespec/openapi";

import "../common";
import "../sessions";
import "./models.tsp";

using TypeSpec.Http;
using TypeSpec.OpenAPI;

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
        @header contentType: yaml | json;

        @body
        @doc("Request to generate a response from the model")
        body: ChatInput;
    ): {
        @statusCode _: "200";

        @body
        @doc("Response from the model")
        body: ChatResponse;
    };
}
