var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
import axios from 'axios';
import { TrieveSDK } from 'trieve-ts-sdk';
import { z } from 'zod';
import { SUBDOMAIN } from './config.readonly.js';
import { SERVER_URL } from './config.readonly.js';
import { formatErr, throwOnAxiosError } from './utils.js';
const DEFAULT_BASE_URL = 'https://api.mintlifytrieve.com';
export function fetchSearchConfigurationAndTools(subdomain) {
    return __awaiter(this, void 0, void 0, function* () {
        try {
            const response = yield axios.get(`${SERVER_URL}/api/mcp/config/${subdomain}`, {
                validateStatus() {
                    return true;
                },
            });
            throwOnAxiosError(response, 'Failed to fetch MCP config');
            return response.data;
        }
        catch (err) {
            throw new Error(formatErr(err).replace('Request failed with status code 404', `${subdomain} not found`));
        }
    });
}
function search(query, config) {
    return __awaiter(this, void 0, void 0, function* () {
        const trieve = new TrieveSDK({
            apiKey: config.trieveApiKey,
            datasetId: config.trieveDatasetId,
            baseUrl: DEFAULT_BASE_URL,
        });
        const data = yield trieve.autocomplete({
            page_size: 10,
            query,
            search_type: 'fulltext',
            extend_results: true,
            score_threshold: 1,
        });
        if (data.chunks === undefined || data.chunks.length === 0) {
            throw new Error('No results found');
        }
        return data.chunks.map((result) => {
            const { chunk } = result;
            // TODO: Append custom domain to the link
            return {
                title: chunk.metadata.title,
                content: chunk.chunk_html,
                link: chunk.link,
            };
        });
    });
}
export function createSearchTool(server) {
    return __awaiter(this, void 0, void 0, function* () {
        const config = yield fetchSearchConfigurationAndTools(SUBDOMAIN);
        server.tool('search', `Search across the ${config.name} documentation to fetch relevant context for a given query`, {
            query: z.string(),
        }, (_a) => __awaiter(this, [_a], void 0, function* ({ query }) {
            const results = yield search(query, config);
            const content = results.map((result) => {
                const { title, content, link } = result;
                const text = `Title: ${title}\nContent: ${content}\nLink: ${link}`;
                return {
                    type: 'text',
                    text,
                };
            });
            return {
                content,
            };
        }));
    });
}
