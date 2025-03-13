import "@typespec/http";
import "@typespec/openapi";

using TypeSpec.Http;
using TypeSpec.OpenAPI;

@service({
    name: "responses-api",
    title: "Responses API",
})
@info({
    title: "Responses API",
    version: "1.0.0",
    termsOfService: "https://openai.com/terms",
    contact: {
        name: "OpenAI",
        url: "https://openai.com",
        email: "developers@openai.com",
    },
    license: {
        name: "OpenAI License",
        url: "https://openai.com/license",
    },
})
@server(
    "https://api.openai.com/v1",
    "The OpenAI Responses API endpoint"
)
@useAuth(
    ApiKeyAuth<ApiKeyLocation.header, "Authorization">
)
namespace ResponsesApi {
    import "./responses/endpoints.tsp";
    import "./responses/models.tsp";
}
