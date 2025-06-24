import { OpenApiToEndpointConverter, } from '@mintlify/validation';
import dashify from 'dashify';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { OpenAPIV3 } from 'openapi-types';
import { z } from 'zod';
import { initializeObject } from '../utils.js';
import { dataSchemaArrayToZod, dataSchemaToZod } from './zod.js';
export function convertStrToTitle(str) {
    const spacedString = str.replace(/[-_]/g, ' ');
    const words = spacedString.split(/(?=[A-Z])|\s+/);
    const titleCasedWords = words.map((word) => {
        return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
    });
    return titleCasedWords.join(' ');
}
export function findNextIteration(set, str) {
    let count = 1;
    set.forEach((val) => {
        if (val.startsWith(`${str}---`)) {
            count = Number(val.replace(`${str}---`, ''));
        }
    });
    return count + 1;
}
export function getMcpEnabledEndpointsFromOpenApiSpec(spec) {
    var _a;
    const mcpEnabledEndpoints = [];
    const isMcpEnabledGloballyInSpec = ((_a = spec['x-mcp']) === null || _a === void 0 ? void 0 : _a.enabled) === true;
    const endpoints = getEndpointsFromOpenApi(spec);
    if (isMcpEnabledGloballyInSpec) {
        const notDisabledEndpoints = endpoints.filter((endpoint) => { var _a; return ((_a = endpoint.xMcp) === null || _a === void 0 ? void 0 : _a.enabled) !== false; });
        mcpEnabledEndpoints.push(...notDisabledEndpoints);
    }
    else {
        const enabledEndpoints = endpoints.filter((endpoint) => { var _a; return ((_a = endpoint.xMcp) === null || _a === void 0 ? void 0 : _a.enabled) === true; });
        mcpEnabledEndpoints.push(...enabledEndpoints);
    }
    return mcpEnabledEndpoints;
}
export function convertEndpointToTool(endpoint) {
    var _a, _b;
    let name;
    if ((_a = endpoint.xMcp) === null || _a === void 0 ? void 0 : _a.name) {
        name = endpoint.xMcp.name;
    }
    else if (endpoint.title) {
        name = dashify(endpoint.title);
    }
    else {
        name = convertStrToTitle(endpoint.path);
    }
    let description;
    if ((_b = endpoint.xMcp) === null || _b === void 0 ? void 0 : _b.description) {
        description = endpoint.xMcp.description;
    }
    else if (endpoint.description) {
        description = endpoint.description;
    }
    else {
        description = `${endpoint.method} ${endpoint.path}`;
    }
    return {
        name,
        description,
    };
}
export function getMcpToolsAndEndpointsFromOpenApiSpec(spec) {
    const endpoints = getMcpEnabledEndpointsFromOpenApiSpec(spec);
    const toolsWithEndpoints = [];
    endpoints.forEach((endpoint) => {
        const tool = convertEndpointToTool(endpoint);
        toolsWithEndpoints.push({
            tool,
            endpoint,
        });
    });
    return toolsWithEndpoints;
}
export function getEndpointsFromOpenApi(specification) {
    const endpoints = [];
    const paths = specification.paths;
    for (const path in paths) {
        const pathObj = paths[path];
        const httpMethods = Object.values(OpenAPIV3.HttpMethods);
        for (const method of httpMethods) {
            if (!pathObj || !(method in pathObj)) {
                continue;
            }
            const endpoint = OpenApiToEndpointConverter.convert(specification, path, method, true);
            endpoints.push(endpoint);
        }
    }
    return endpoints;
}
export function loadEnv(key) {
    var _a;
    let envVars = {};
    try {
        const envPath = path.join(fileURLToPath(import.meta.url), '../../../', '.env.json');
        if (fs.existsSync(envPath)) {
            envVars = JSON.parse(fs.readFileSync(envPath).toString());
            return (_a = envVars[key]) !== null && _a !== void 0 ? _a : {};
        }
    }
    catch (error) {
        // if there's no env, the user will be prompted
        // for their auth info at runtime if necessary
        // (shouldn't happen either way)
    }
    return envVars;
}
function convertParameterSection(parameters, paramSection) {
    Object.entries(parameters).forEach(([key, value]) => {
        const schema = value.schema;
        paramSection[key] = dataSchemaArrayToZod(schema);
    });
}
function convertParametersAndAddToRelevantParamGroups(parameters, paths, queries, headers, cookies) {
    convertParameterSection(parameters.path, paths);
    convertParameterSection(parameters.query, queries);
    convertParameterSection(parameters.header, headers);
    convertParameterSection(parameters.cookie, cookies);
}
// this function returns all the securityParameters and seeds them with the envVariables if we have them
export function convertSecurityParameterSection(securityParameters, envVariables, location) {
    const res = [];
    Object.entries(securityParameters).forEach(([key, value]) => {
        let envKeyList = [];
        let targetKey = '';
        switch (value.type) {
            case 'apiKey':
                envKeyList = [location, key];
                targetKey = 'API_KEY';
                break;
            case 'http':
                envKeyList = [location, key, 'HTTP'];
                targetKey = value.scheme;
                break;
            case 'oauth2':
            default:
                break;
        }
        const target = initializeObject(Object.assign({}, envVariables), envKeyList);
        if (envKeyList.length && !target[targetKey]) {
            res.push({
                key,
                value: undefined,
            });
        }
        else {
            res.push({
                key,
                value: target[targetKey],
            });
        }
    });
    return res;
}
function convertSecurityParametersAndAddToRelevantParamGroups(securityParameters, queries, headers, cookies, envVariables) {
    const queryRes = convertSecurityParameterSection(securityParameters.query, envVariables, 'query');
    const headerRes = convertSecurityParameterSection(securityParameters.header, envVariables, 'header');
    const cookieRes = convertSecurityParameterSection(securityParameters.cookie, envVariables, 'cookie');
    // non intuitive that we seed the query with a zod type if it *doesn't* exist
    // but that's because if we don't have it in our env Variables, that means the user should provide it in their query.
    queryRes.forEach(({ key, value }) => {
        if (!value) {
            queries[key] = z.string();
        }
    });
    headerRes.forEach(({ key, value }) => {
        if (!value) {
            headers[key] = z.string();
        }
    });
    cookieRes.forEach(({ key, value }) => {
        if (!value) {
            cookies[key] = z.string();
        }
    });
}
export function convertEndpointToCategorizedZod(envKey, endpoint) {
    var _a, _b, _c;
    const envVariables = loadEnv(envKey);
    const url = `${((_b = (_a = endpoint.servers) === null || _a === void 0 ? void 0 : _a[0]) === null || _b === void 0 ? void 0 : _b.url) || ''}${endpoint.path}`;
    const method = endpoint.method;
    const paths = {};
    const queries = {};
    const headers = {};
    const cookies = {};
    let body = undefined;
    convertParametersAndAddToRelevantParamGroups(endpoint.request.parameters, paths, queries, headers, cookies);
    if ((_c = endpoint.request.security[0]) === null || _c === void 0 ? void 0 : _c.parameters) {
        convertSecurityParametersAndAddToRelevantParamGroups(endpoint.request.security[0].parameters, queries, headers, cookies, envVariables);
    }
    const jsonBodySchema = endpoint.request.body['application/json'];
    const bodySchemaArray = jsonBodySchema === null || jsonBodySchema === void 0 ? void 0 : jsonBodySchema.schemaArray;
    const bodySchema = bodySchemaArray === null || bodySchemaArray === void 0 ? void 0 : bodySchemaArray[0];
    if (bodySchema) {
        const zodBodySchema = dataSchemaToZod(bodySchema);
        body = { body: zodBodySchema };
    }
    return { url, method, paths, queries, body, headers, cookies };
}
