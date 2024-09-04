import { Common_uuid } from "./api";
import { BaseRoutes } from "./baseRoutes";

export class DocsRoutes extends BaseRoutes {
  async get({ id }: { id: Common_uuid }) {
    return await this.apiClient.default.individualDocsRouteGet({ id });
  }
}
