import "@typespec/http";
import "./models.tsp";

using TypeSpec.Http;

namespace Responses;

@route("/responses")
interface ResponsesEndpoints {
  @doc("Creates a model response. Provide text or image inputs to generate text or JSON outputs.")
  @post
  createResponse(
    @body 
    body: CreateResponse
  ): Response;
}