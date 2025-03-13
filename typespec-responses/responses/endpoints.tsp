import "@typespec/http";
import "./models.tsp";

using TypeSpec.Http;

@route("/responses")
interface ResponsesApi {
  @post
  @route("/responses")
  @doc("Creates a model response. Provide text or image inputs to generate text or JSON outputs.")
  op createResponse(@body body: CreateResponse): Response;
} 