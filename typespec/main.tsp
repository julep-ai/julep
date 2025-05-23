import "@typespec/http";
import "@typespec/openapi";
import "@typespec/versioning";

import "./agents";
import "./chat";
import "./docs";
import "./entries";
import "./executions";
import "./files";
import "./jobs";
import "./sessions";
import "./tasks";
import "./tools";
import "./users";
import "./versions.tsp";
import "./responses";
import "./projects";
import "./secrets";

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
        serverEnv?: "api" | "dev" = "api",
    }
)
@useAuth(
    ApiKeyAuth<ApiKeyLocation.header, "Authorization"> | ApiKeyAuth<
        ApiKeyLocation.header,
        "X-Auth-Key"
    >
)
namespace Api {
    @route("/agents")
    interface AgentsRoute extends Agents.Endpoints {}

    @route("/agents/{id}/docs")
    interface AgentDocsRoute extends Docs.AgentEndpoints, Docs.BulkDeleteEndpoints<"Bulk delete Docs owned by an Agent"> {}

    @route("/agents/{id}/search")
    interface AgentsDocsSearchRoute extends Docs.SearchEndpoints<"Search Docs owned by an Agent"> {}

    @route("/agents/{id}/tools")
    interface AgentToolsRoute extends Tools.AgentEndpoints {}

    @route("/responses")
    interface ResponsesRoute extends Responses.ResponsesEndpoints {}

    @route("/users")
    interface UsersRoute extends Users.Endpoints {}

    @route("/users/{id}/docs")
    interface UserDocsRoute extends Docs.UserEndpoints, Docs.BulkDeleteEndpoints<"Bulk delete Docs owned by a User"> {}

    @route("/users/{id}/search")
    interface UserDocsSearchRoute extends Docs.SearchEndpoints<"Search Docs owned by a User"> {}

    @route("/sessions")
    interface SessionsRoute extends Sessions.Endpoints {}

    @route("/sessions/{id}/history")
    interface HistoryRoute extends Entries.Endpoints {}

    @route("/sessions/{id}/chat")
    interface ChatRoute extends Chat.Endpoints {}

    @route("/sessions/{id}/render")
    interface RenderRoute extends Chat.RenderEndpoints {}

    @route("/embed")
    interface EmbedRoute extends Docs.EmbedEndpoints {}

    @route("/docs")
    interface IndividualDocsRoute extends Docs.IndividualDocEndpoints {}

    @route("/tasks")
    interface TasksGetRoute extends Tasks.GetEndpoints {}

    @route("/agents/{id}/tasks")
    interface TasksRoute extends Tasks.Endpoints {}

    @route("/agents/{parent_id}/tasks")
    interface TasksCreateOrUpdateRoute extends Tasks.CreateOrUpdateEndpoints {}

    @route("/tasks/{id}/executions")
    interface TaskExecutionsRoute extends Executions.TaskEndpoints {}

    @route("/executions")
    interface ExecutionsRoute extends Executions.Endpoints, Executions.PublicEndpoints {}

    @route("/executions/{id}/transitions")
    interface ExecutionTransitionsRoute extends Executions.TransitionEndpoints {}

    @route("/executions/{id}/transitions.stream")
    interface ExecutionTransitionsStreamRoute extends Executions.TransitionStreamEndpoints {}

    @route("/executions/{id}/status.stream")
    interface ExecutionStatusStreamRoute extends Executions.ExecutionStatusStreamEndpoints {}

    @route("/jobs")
    interface JobRoute extends Jobs.Endpoints {}

    @route("/files")
    interface FilesRoute extends Files.Endpoints {}

    @route("/projects")
    interface ProjectsRoute extends Projects.Endpoints {}

    @route("/secrets")
    interface DeveloperSecretsRoute extends Secrets.DeveloperSecretsEndpoints {}

    @route("/agents/{id}/secrets")
    interface AgentSecretsRoute extends Secrets.AgentSecretsEndpoints {}
}
