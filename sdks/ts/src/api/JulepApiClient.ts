/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BaseHttpRequest } from "./core/BaseHttpRequest";
import type { OpenAPIConfig } from "./core/OpenAPI";
import { AxiosHttpRequest } from "./core/AxiosHttpRequest";
import { DefaultService } from "./services/DefaultService";
type HttpRequestConstructor = new (config: OpenAPIConfig) => BaseHttpRequest;
export class JulepApiClient {
  public readonly default: DefaultService;
  public readonly request: BaseHttpRequest;
  constructor(
    config?: Partial<OpenAPIConfig>,
    HttpRequest: HttpRequestConstructor = AxiosHttpRequest,
  ) {
    this.request = new HttpRequest({
      BASE: config?.BASE ?? "https://api-alpha.julep.ai/api",
      VERSION: config?.VERSION ?? "0.4.0",
      WITH_CREDENTIALS: config?.WITH_CREDENTIALS ?? false,
      CREDENTIALS: config?.CREDENTIALS ?? "include",
      TOKEN: config?.TOKEN,
      USERNAME: config?.USERNAME,
      PASSWORD: config?.PASSWORD,
      HEADERS: config?.HEADERS,
      ENCODE_PATH: config?.ENCODE_PATH,
    });
    this.default = new DefaultService(this.request);
  }
}
