import { Docs_EmbedQueryRequest } from "./api";
import { BaseRoutes } from "./baseRoutes";

export class EmbedRoutes extends BaseRoutes {
    async embed({
        requestBody,
    }: {
        requestBody: {
            body: Docs_EmbedQueryRequest;
        };
    }) {
        return await this.apiClient.default.embedRouteEmbed({ requestBody })
    }
}