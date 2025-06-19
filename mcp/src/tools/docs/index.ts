import { z } from 'zod';
import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { searchDocs } from './search.js';
import { UnifiedTool } from '../../types.js';

// AIDEV-NOTE: Documentation search tools that work without authentication

export async function createDocumentationTools() {
  const tools: Array<{
    tool: Tool;
    handler: (args: any) => Promise<any>;
    unified: UnifiedTool;
  }> = [];

  // Documentation search tool
  const searchTool: Tool = {
    name: 'search-julep-docs',
    description: 'Search across the Julep documentation to find relevant information and code examples',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'The search query to find relevant documentation',
        },
      },
      required: ['query'],
    },
  };

  const searchHandler = async ({ query }: { query: string }) => {
    try {
      const results = await searchDocs(query);
      
      if (results.length === 0) {
        return {
          content: [
            {
              type: 'text',
              text: `No documentation found for query: "${query}"`,
            },
          ],
        };
      }

      const content = results.map((result) => ({
        type: 'text',
        text: `Title: ${result.title}\nContent: ${result.content}\nLink: ${result.link}\n`,
      }));

      return { content };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      return {
        content: [
          {
            type: 'text',
            text: `Error searching documentation: ${errorMessage}`,
          },
        ],
        isError: true,
      };
    }
  };

  tools.push({
    tool: searchTool,
    handler: searchHandler,
    unified: {
      name: searchTool.name,
      description: searchTool.description || '',
      category: 'docs',
      requiresAuth: false,
    },
  });

  return tools;
}