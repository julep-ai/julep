import axios from 'axios';
import { TrieveSDK } from 'trieve-ts-sdk';
import { SearchResult, TrieveConfig } from '../../types.js';

const SUBDOMAIN = 'julep';
const SERVER_URL = 'https://leaves.mintlify.com';
const DEFAULT_TRIEVE_BASE_URL = 'https://api.mintlifytrieve.com';

// AIDEV-NOTE: Ported from docs-mcp - searches Julep docs via Trieve/Mintlify

let cachedConfig: TrieveConfig | null = null;
let configCacheTime = 0;
const CONFIG_CACHE_DURATION = 15 * 60 * 1000; // 15 minutes

async function fetchSearchConfiguration(): Promise<TrieveConfig> {
  // Check cache
  if (cachedConfig !== null && Date.now() - configCacheTime < CONFIG_CACHE_DURATION) {
    return cachedConfig;
  }

  try {
    const response = await axios.get(`${SERVER_URL}/api/mcp/config/${SUBDOMAIN}`, {
      validateStatus() {
        return true;
      },
    });

    if (response.status !== 200) {
      throw new Error(
        response.status === 404
          ? `Documentation for ${SUBDOMAIN} not found`
          : `Failed to fetch documentation config: ${response.status}`
      );
    }

    cachedConfig = response.data;
    configCacheTime = Date.now();
    return response.data;
  } catch (err) {
    if (axios.isAxiosError(err)) {
      throw new Error(
        err.response?.status === 404
          ? `Documentation for ${SUBDOMAIN} not found`
          : `Failed to fetch documentation config: ${err.message}`
      );
    }
    throw err;
  }
}

export async function searchDocs(query: string): Promise<SearchResult[]> {
  const config = await fetchSearchConfiguration();

  const trieve = new TrieveSDK({
    apiKey: config.trieveApiKey,
    datasetId: config.trieveDatasetId,
    baseUrl: DEFAULT_TRIEVE_BASE_URL,
  });

  try {
    const data = await trieve.autocomplete({
      page_size: 10,
      query,
      search_type: 'fulltext',
      extend_results: true,
      score_threshold: 1,
    });

    if (!data.chunks || data.chunks.length === 0) {
      return [];
    }

    return data.chunks.map((result: any) => {
      const { chunk } = result;
      return {
        title: chunk.metadata.title || 'Untitled',
        content: chunk.chunk_html || chunk.content || '',
        link: chunk.link || '#',
      };
    });
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Search failed: ${error.message}`);
    }
    throw new Error('Search failed with unknown error');
  }
}