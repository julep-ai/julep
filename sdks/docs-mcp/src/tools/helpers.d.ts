import { OpenAPI } from '@mintlify/openapi-types';
import { HttpMethod, SecurityParameterGroup } from '@mintlify/validation';
import { Endpoint } from '@mintlify/validation';
import { DataSchemaArray } from '@mintlify/validation';
import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { ServerParams, ToolWithEndpoint } from '../types.js';
import { NestedRecord, SimpleRecord } from '../utils.js';
export declare function convertStrToTitle(str: string): string;
export declare function findNextIteration(set: Set<string>, str: string): number;
export declare function getMcpEnabledEndpointsFromOpenApiSpec(spec: OpenAPI.Document): Endpoint<DataSchemaArray>[];
export declare function convertEndpointToTool(endpoint: Endpoint<DataSchemaArray>): Omit<Tool, 'inputSchema'>;
export declare function getMcpToolsAndEndpointsFromOpenApiSpec(spec: OpenAPI.Document): ToolWithEndpoint[];
export declare function getEndpointsFromOpenApi(specification: OpenAPI.Document): Endpoint<DataSchemaArray>[];
export declare function loadEnv(key: string): SimpleRecord;
export declare function convertSecurityParameterSection(securityParameters: SecurityParameterGroup, envVariables: SimpleRecord, location: string): {
    key: string;
    value: NestedRecord | undefined;
}[];
export declare function convertEndpointToCategorizedZod(envKey: string, endpoint: Endpoint): {
    url: string;
    method: HttpMethod;
    paths: ServerParams;
    queries: ServerParams;
    body: ServerParams | undefined;
    headers: ServerParams;
    cookies: ServerParams;
};
