import "@typespec/http";
import "@typespec/openapi";
import "@typespec/versioning";

import "./agents";
import "./chat";
import "./docs";
import "./entries";
import "./jobs";
import "./sessions";
import "./tasks";
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
    ApiKeyAuth<ApiKeyLocation.header, "Authorization"> | ApiKeyAuth<
        ApiKeyLocation.header,
        "X-Auth-Key"
    >
)
namespace Api {
    model Agent is Agents.Agent;
    model Doc is Docs.Doc;
    model Tool is Tools.Tool;
    model User is Users.User;
    model Session is Sessions.Session;
    model History is Entries.History;
    model Entry is Entries.Entry;
    model Task is Tasks.Task;
    model JobStatus is Jobs.JobStatus;

    @route("/agents")
    interface AgentRoute extends Agents.Endpoints {}

    @route("/agents/{id}/docs")
    interface AgentDocsRoute extends Docs.AgentEndpoints {}

    @route("/agents/{id}/tools")
    interface AgentToolsRoute extends Tools.AgentEndpoints {}

    @route("/users")
    interface UserRoute extends Users.Endpoints {}

    @route("/users/{id}/docs")
    interface UserDocsRoute extends Docs.UserEndpoints {}

    @route("/sessions")
    interface SessionRoute extends Sessions.Endpoints {}

    @route("/sessions/{id}/history")
    interface HistoryRoute extends Entries.Endpoints {}

    @route("/docs/{id}")
    interface AgentIndividualDocRoute extends Docs.IndividualDocEndpoints {}

    @route("/tasks")
    interface TaskRoute extends Tasks.Endpoints {}

    @route("/tools")
    interface ToolRoute extends Tools.Endpoints {}

    @route("/jobs")
    interface JobRoute extends Jobs.Endpoints {}
}
