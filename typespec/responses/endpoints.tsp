import "@typespec/http";
import "./models.tsp";
import "../common";

using TypeSpec.Http;
using Common;

namespace Responses;

@route("/responses")
interface ResponsesEndpoints {
  @doc("Creates a model response. Provide text or image inputs to generate text or JSON outputs.")
  @post
  createResponse(
    @body 
    body: CreateResponse
  ): Response;
  
  @get
  @doc("Get a response by id")
  getResponse(
    @path
    @doc("ID of the response")
    id: string,
    
    @query
    @doc("Specify additional output data to include in the model response")
    include?: Includable[];
  ): Response;
}