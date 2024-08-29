import { Common_uuid } from "./api";
import { BaseRoutes } from "./baseRoutes";

export class JobsRoutes extends BaseRoutes {
  async _({ id }: { id: Common_uuid }) {
    return await this.apiClient.default.jobRouteGet({ id });
  }
}
