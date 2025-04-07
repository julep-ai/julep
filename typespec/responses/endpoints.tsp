import "@typespec/http";
import "./models.tsp";
import "../common";

using TypeSpec.Http;
using Common;

namespace Responses;

interface ResponsesEndpoints extends GetResponsesEndpoints, CreateResponsesEndpoints {}

interface CreateResponsesEndpoints {
  @doc("Creates a model response. Provide text or image inputs to generate text or JSON outputs.")
  @post
  createResponse(
    @body 
    body: CreateResponse
  ): Response;
}

interface GetResponsesEndpoints {
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