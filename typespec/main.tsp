import "@typespec/http";
import "@typespec/openapi";
import "@typespec/versioning";

import "./agents";
import "./chat";
import "./docs";
import "./entries";
import "./jobs";
import "./sessions";
import "./tools";
import "./users";
import "./versions.tsp";

using TypeSpec.Http;
using TypeSpec.OpenAPI;
using TypeSpec.Versioning;

using Versions;

//
// MAIN
//

/** Julep is a backend for creating stateful AI apps with background tasks and long-term memory easily. */
@service({
    name: "julep-api",
    title: "Julep API",
})
@versioned(ApiVersions)
@summary("A backend for creating stateful AI apps")
@info({
    termsOfService: "https://julep.ai/terms",
    contact: {
        name: "Julep AI",
        url: "https://julep.ai",
        email: "developers@julep.ai",
    },
    license: {
        name: "Apache 2.0",
        url: "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
})
@externalDocs("https://docs.julep.ai", "Julep API documentation")
@server(
    "https://{serverEnv}.julep.ai/api",
    "The julep cloud service endpoint",
    {
        @doc("The environment to use")
        serverEnv?: "api" | "api-alpha" = "api-alpha",
    }
)
@useAuth(
    ApiKeyAuth<ApiKeyLocation.header, "Authorization">
    | ApiKeyAuth<ApiKeyLocation.header, "X-Auth-Key">
)
namespace Api {
    // model Agent_ is Agents.Agent {}

    @route("/agents")
    interface Agent extends Agents.Endpoints {}

    @route("/agents/{id}/docs")
    interface AgentDocs extends Docs.AgentEndpoints {}

    @route("/agents/{id}/tools")
    interface AgentTools extends Tools.AgentEndpoints {}

    @route("/users")
    interface User extends Users.Endpoints {}

    @route("/users/{id}/docs")
    interface UserDocs extends Docs.UserEndpoints {}

    @route("/sessions")
    interface Session extends Sessions.Endpoints {}

    @route("/sessions/{id}/history")
    interface History extends Entries.Endpoints {}

    @route("/docs/{id}")
    interface AgentIndividualDoc extends Docs.IndividualDocEndpoints {}

    @route("/tools")
    interface Tool extends Tools.Endpoints {}

    @route("/jobs")
    interface Job extends Jobs.Endpoints {}
}
