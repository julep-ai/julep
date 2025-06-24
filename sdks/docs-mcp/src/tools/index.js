var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
import axios, { isAxiosError } from 'axios';
import dashify from 'dashify';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { convertEndpointToCategorizedZod, convertSecurityParameterSection, convertStrToTitle, findNextIteration, loadEnv, } from './helpers.js';
export function createTools(server, existingTools) {
    return __awaiter(this, void 0, void 0, function* () {
        const toolsDir = path.join(fileURLToPath(import.meta.url), '..', '..');
        let tools = JSON.parse(fs.readFileSync(path.join(toolsDir, 'tools.json'), 'utf-8'));
        tools = tools.filter((tool) => tool.endpoint);
        tools.forEach(({ uuid, endpoint }) => {
            const envVars = loadEnv(uuid);
            const { url: urlSchema, method: methodSchema, paths: pathsSchema, queries: queriesSchema, body: bodySchema, headers: headersSchema, cookies: cookiesSchema, } = convertEndpointToCategorizedZod(uuid, endpoint);
            const serverArgumentsSchemas = Object.assign(Object.assign(Object.assign(Object.assign(Object.assign({}, pathsSchema), queriesSchema), bodySchema), headersSchema), cookiesSchema);
            if (!endpoint.title) {
                endpoint.title = `${endpoint.method} ${convertStrToTitle(endpoint.path)}`;
            }
            if (existingTools.has(endpoint.title)) {
                const lastCount = findNextIteration(existingTools, endpoint.title);
                endpoint.title = `${endpoint.title}---${lastCount}`;
            }
            if (endpoint.title.length > 64) {
                endpoint.title = endpoint.title.slice(0, -64);
            }
            existingTools.add(endpoint.title);
            server.tool(dashify(endpoint.title), endpoint.description || endpoint.title, serverArgumentsSchemas, (inputArgs) => __awaiter(this, void 0, void 0, function* () {
                var _a;
                const inputParams = {};
                const inputHeaders = {};
                const inputCookies = {};
                let urlWithPathParams = urlSchema;
                let inputBody = undefined;
                if ('body' in inputArgs) {
                    inputBody = inputArgs.body;
                    delete inputArgs.body;
                }
                Object.entries(inputArgs).forEach(([key, value]) => {
                    if (key in pathsSchema) {
                        urlWithPathParams = urlWithPathParams.replace(`{${key}}`, value);
                    }
                    else if (key in queriesSchema) {
                        inputParams[key] = value;
                    }
                    else if (key in headersSchema) {
                        inputHeaders[key] = value;
                    }
                    else if (key in cookiesSchema) {
                        inputCookies[key] = value;
                    }
                });
                const securityParamSections = (_a = endpoint.request.security[0]) === null || _a === void 0 ? void 0 : _a.parameters;
                if (securityParamSections) {
                    const headerRes = convertSecurityParameterSection(securityParamSections.header, envVars, 'header');
                    headerRes.forEach(({ key, value }) => {
                        if (value) {
                            inputHeaders[key] = value;
                        }
                    });
                    const cookieRes = convertSecurityParameterSection(securityParamSections.cookie, envVars, 'cookie');
                    cookieRes.forEach(({ key, value }) => {
                        if (value) {
                            inputCookies[key] = value;
                        }
                    });
                    const queryRes = convertSecurityParameterSection(securityParamSections.query, envVars, 'query');
                    queryRes.forEach(({ key, value }) => {
                        if (value) {
                            inputParams[key] = value;
                        }
                    });
                }
                try {
                    const response = yield axios({
                        url: urlWithPathParams,
                        method: methodSchema,
                        params: inputParams,
                        data: inputBody,
                        headers: inputHeaders,
                    });
                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(response.data, undefined, 2),
                            },
                        ],
                    };
                }
                catch (error) {
                    const errMsg = JSON.stringify(error, undefined, 2);
                    return {
                        isError: true,
                        content: [
                            {
                                type: 'text',
                                text: isAxiosError(error) ? `${error.message}\n\n${errMsg}` : errMsg,
                            },
                        ],
                    };
                }
            }));
        });
    });
}
