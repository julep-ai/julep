import type { OpenAPIConfig } from "../api";

import type { ApiRequestOptions } from "../api/core/ApiRequestOptions";

import { isPlainObject, mapKeys, camelCase } from "lodash";

import { AxiosHttpRequest } from "../api/core/AxiosHttpRequest";
import { CancelablePromise } from "../api/core/CancelablePromise";

const camelCaseify = (responseBody: any) =>
  mapKeys(responseBody, (_value: any, key: string) => camelCase(key));

export class CustomHttpRequest extends AxiosHttpRequest {
  constructor(config: OpenAPIConfig) {
    super(config);
  }

  public override request<T>(options: ApiRequestOptions): CancelablePromise<T> {
    const cancelableResponse = super.request(options);

    return new CancelablePromise<T>((resolve, reject, onCancel) => {
      onCancel(() => cancelableResponse.cancel());

      const handleResponse = (responseBody: any) => {
        // If the response body is not a plain object, return it as is
        if (!isPlainObject(responseBody)) {
          return responseBody;
        }

        // Otherwise, convert the response body to camelCase
        let updatedResponseBody = responseBody;
        updatedResponseBody = camelCaseify(updatedResponseBody);

        if ("items" in updatedResponseBody) {
          updatedResponseBody.items =
            updatedResponseBody.items.map(camelCaseify);
        }

        return updatedResponseBody as T;
      };

      cancelableResponse.then(handleResponse).then(resolve, reject);
    });
  }
}
