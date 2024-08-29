import { Common_uuid } from "./api";
import { BaseRoutes } from "./baseRoutes";

export class HistoryRoutes extends BaseRoutes {
  async delete({ id }: { id: Common_uuid }) {
    return await this.apiClient.default.historyRouteDelete({ id });
  }

  async get({ id }: { id: Common_uuid }) {
    return await this.apiClient.default.historyRouteHistory({ id });
  }
}
