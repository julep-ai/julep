declare const openapi: {
    readonly v1: {
        id: string;
        $schema: string;
        type: string;
        required: string[];
        properties: {
            swaggerVersion: {
                enum: string[];
            };
            apiVersion: {
                type: string;
            };
            basePath: {
                type: string;
                format: string;
                pattern: string;
            };
            resourcePath: {
                type: string;
                format: string;
                pattern: string;
            };
            apis: {
                type: string;
                items: {
                    $ref: string;
                };
            };
            models: {
                type: string;
                additionalProperties: {
                    $ref: string;
                };
            };
            produces: {
                $ref: string;
            };
            consumes: {
                $ref: string;
            };
            authorizations: {
                $ref: string;
            };
        };
        additionalProperties: boolean;
        definitions: {
            apiObject: {
                type: string;
                required: string[];
                properties: {
                    path: {
                        type: string;
                        format: string;
                        pattern: string;
                    };
                    description: {
                        type: string;
                    };
                    operations: {
                        type: string;
                        items: {
                            $ref: string;
                        };
                    };
                };
                additionalProperties: boolean;
            };
            mimeTypeArray: {
                type: string;
                items: {
                    type: string;
                    format: string;
                };
                uniqueItems: boolean;
            };
        };
    };
    readonly v2: {
        title: string;
        id: string;
        $schema: string;
        type: string;
        required: string[];
        additionalProperties: boolean;
        patternProperties: {
            "^x-": {
                $ref: string;
            };
        };
        properties: {
            swagger: {
                type: string;
                enum: string[];
                description: string;
            };
            info: {
                $ref: string;
            };
            host: {
                type: string;
                pattern: string;
                description: string;
            };
            basePath: {
                type: string;
                pattern: string;
                description: string;
            };
            schemes: {
                $ref: string;
            };
            consumes: {
                description: string;
                allOf: {
                    $ref: string;
                }[];
            };
            produces: {
                description: string;
                allOf: {
                    $ref: string;
                }[];
            };
            paths: {
                $ref: string;
            };
            definitions: {
                $ref: string;
            };
            parameters: {
                $ref: string;
            };
            responses: {
                $ref: string;
            };
            security: {
                $ref: string;
            };
            securityDefinitions: {
                $ref: string;
            };
            tags: {
                type: string;
                items: {
                    $ref: string;
                };
                uniqueItems: boolean;
            };
            externalDocs: {
                $ref: string;
            };
        };
        definitions: {
            info: {
                type: string;
                description: string;
                required: string[];
                additionalProperties: boolean;
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
                properties: {
                    title: {
                        type: string;
                        description: string;
                    };
                    version: {
                        type: string;
                        description: string;
                    };
                    description: {
                        type: string;
                        description: string;
                    };
                    termsOfService: {
                        type: string;
                        description: string;
                    };
                    contact: {
                        $ref: string;
                    };
                    license: {
                        $ref: string;
                    };
                };
            };
            contact: {
                type: string;
                description: string;
                additionalProperties: boolean;
                properties: {
                    name: {
                        type: string;
                        description: string;
                    };
                    url: {
                        type: string;
                        description: string;
                        format: string;
                    };
                    email: {
                        type: string;
                        description: string;
                        format: string;
                    };
                };
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
            };
            license: {
                type: string;
                required: string[];
                additionalProperties: boolean;
                properties: {
                    name: {
                        type: string;
                        description: string;
                    };
                    url: {
                        type: string;
                        description: string;
                        format: string;
                    };
                };
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
            };
            paths: {
                type: string;
                description: string;
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                    "^/": {
                        $ref: string;
                    };
                };
                additionalProperties: boolean;
            };
            definitions: {
                type: string;
                additionalProperties: {
                    $ref: string;
                };
                description: string;
            };
            parameterDefinitions: {
                type: string;
                additionalProperties: {
                    $ref: string;
                };
                description: string;
            };
            responseDefinitions: {
                type: string;
                additionalProperties: {
                    $ref: string;
                };
                description: string;
            };
            externalDocs: {
                type: string;
                additionalProperties: boolean;
                description: string;
                required: string[];
                properties: {
                    description: {
                        type: string;
                    };
                    url: {
                        type: string;
                        format: string;
                    };
                };
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
            };
            examples: {
                type: string;
                additionalProperties: boolean;
            };
            mimeType: {
                type: string;
                description: string;
            };
            operation: {
                type: string;
                required: string[];
                additionalProperties: boolean;
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
                properties: {
                    tags: {
                        type: string;
                        items: {
                            type: string;
                        };
                        uniqueItems: boolean;
                    };
                    summary: {
                        type: string;
                        description: string;
                    };
                    description: {
                        type: string;
                        description: string;
                    };
                    externalDocs: {
                        $ref: string;
                    };
                    operationId: {
                        type: string;
                        description: string;
                    };
                    produces: {
                        description: string;
                        allOf: {
                            $ref: string;
                        }[];
                    };
                    consumes: {
                        description: string;
                        allOf: {
                            $ref: string;
                        }[];
                    };
                    parameters: {
                        $ref: string;
                    };
                    responses: {
                        $ref: string;
                    };
                    schemes: {
                        $ref: string;
                    };
                    deprecated: {
                        type: string;
                        default: boolean;
                    };
                    security: {
                        $ref: string;
                    };
                };
            };
            pathItem: {
                type: string;
                additionalProperties: boolean;
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
                properties: {
                    $ref: {
                        type: string;
                    };
                    get: {
                        $ref: string;
                    };
                    put: {
                        $ref: string;
                    };
                    post: {
                        $ref: string;
                    };
                    delete: {
                        $ref: string;
                    };
                    options: {
                        $ref: string;
                    };
                    head: {
                        $ref: string;
                    };
                    patch: {
                        $ref: string;
                    };
                    parameters: {
                        $ref: string;
                    };
                };
            };
            responses: {
                type: string;
                description: string;
                minProperties: number;
                additionalProperties: boolean;
                patternProperties: {
                    "^([0-9]{3})$|^(default)$": {
                        $ref: string;
                    };
                    "^x-": {
                        $ref: string;
                    };
                };
                not: {
                    type: string;
                    additionalProperties: boolean;
                    patternProperties: {
                        "^x-": {
                            $ref: string;
                        };
                    };
                };
            };
            responseValue: {
                oneOf: {
                    $ref: string;
                }[];
            };
            response: {
                type: string;
                required: string[];
                properties: {
                    description: {
                        type: string;
                    };
                    schema: {
                        oneOf: {
                            $ref: string;
                        }[];
                    };
                    headers: {
                        $ref: string;
                    };
                    examples: {
                        $ref: string;
                    };
                };
                additionalProperties: boolean;
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
            };
            headers: {
                type: string;
                additionalProperties: {
                    $ref: string;
                };
            };
            header: {
                type: string;
                additionalProperties: boolean;
                required: string[];
                properties: {
                    type: {
                        type: string;
                        enum: string[];
                    };
                    format: {
                        type: string;
                    };
                    items: {
                        $ref: string;
                    };
                    collectionFormat: {
                        $ref: string;
                    };
                    default: {
                        $ref: string;
                    };
                    maximum: {
                        $ref: string;
                    };
                    exclusiveMaximum: {
                        $ref: string;
                    };
                    minimum: {
                        $ref: string;
                    };
                    exclusiveMinimum: {
                        $ref: string;
                    };
                    maxLength: {
                        $ref: string;
                    };
                    minLength: {
                        $ref: string;
                    };
                    pattern: {
                        $ref: string;
                    };
                    maxItems: {
                        $ref: string;
                    };
                    minItems: {
                        $ref: string;
                    };
                    uniqueItems: {
                        $ref: string;
                    };
                    enum: {
                        $ref: string;
                    };
                    multipleOf: {
                        $ref: string;
                    };
                    description: {
                        type: string;
                    };
                };
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
            };
            vendorExtension: {
                description: string;
                additionalProperties: boolean;
                additionalItems: boolean;
            };
            bodyParameter: {
                type: string;
                required: string[];
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
                properties: {
                    description: {
                        type: string;
                        description: string;
                    };
                    name: {
                        type: string;
                        description: string;
                    };
                    in: {
                        type: string;
                        description: string;
                        enum: string[];
                    };
                    required: {
                        type: string;
                        description: string;
                        default: boolean;
                    };
                    schema: {
                        $ref: string;
                    };
                };
                additionalProperties: boolean;
            };
            headerParameterSubSchema: {
                additionalProperties: boolean;
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
                properties: {
                    required: {
                        type: string;
                        description: string;
                        default: boolean;
                    };
                    in: {
                        type: string;
                        description: string;
                        enum: string[];
                    };
                    description: {
                        type: string;
                        description: string;
                    };
                    name: {
                        type: string;
                        description: string;
                    };
                    type: {
                        type: string;
                        enum: string[];
                    };
                    format: {
                        type: string;
                    };
                    items: {
                        $ref: string;
                    };
                    collectionFormat: {
                        $ref: string;
                    };
                    default: {
                        $ref: string;
                    };
                    maximum: {
                        $ref: string;
                    };
                    exclusiveMaximum: {
                        $ref: string;
                    };
                    minimum: {
                        $ref: string;
                    };
                    exclusiveMinimum: {
                        $ref: string;
                    };
                    maxLength: {
                        $ref: string;
                    };
                    minLength: {
                        $ref: string;
                    };
                    pattern: {
                        $ref: string;
                    };
                    maxItems: {
                        $ref: string;
                    };
                    minItems: {
                        $ref: string;
                    };
                    uniqueItems: {
                        $ref: string;
                    };
                    enum: {
                        $ref: string;
                    };
                    multipleOf: {
                        $ref: string;
                    };
                };
            };
            queryParameterSubSchema: {
                additionalProperties: boolean;
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
                properties: {
                    required: {
                        type: string;
                        description: string;
                        default: boolean;
                    };
                    in: {
                        type: string;
                        description: string;
                        enum: string[];
                    };
                    description: {
                        type: string;
                        description: string;
                    };
                    name: {
                        type: string;
                        description: string;
                    };
                    allowEmptyValue: {
                        type: string;
                        default: boolean;
                        description: string;
                    };
                    type: {
                        type: string;
                        enum: string[];
                    };
                    format: {
                        type: string;
                    };
                    items: {
                        $ref: string;
                    };
                    collectionFormat: {
                        $ref: string;
                    };
                    default: {
                        $ref: string;
                    };
                    maximum: {
                        $ref: string;
                    };
                    exclusiveMaximum: {
                        $ref: string;
                    };
                    minimum: {
                        $ref: string;
                    };
                    exclusiveMinimum: {
                        $ref: string;
                    };
                    maxLength: {
                        $ref: string;
                    };
                    minLength: {
                        $ref: string;
                    };
                    pattern: {
                        $ref: string;
                    };
                    maxItems: {
                        $ref: string;
                    };
                    minItems: {
                        $ref: string;
                    };
                    uniqueItems: {
                        $ref: string;
                    };
                    enum: {
                        $ref: string;
                    };
                    multipleOf: {
                        $ref: string;
                    };
                };
            };
            formDataParameterSubSchema: {
                additionalProperties: boolean;
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
                properties: {
                    required: {
                        type: string;
                        description: string;
                        default: boolean;
                    };
                    in: {
                        type: string;
                        description: string;
                        enum: string[];
                    };
                    description: {
                        type: string;
                        description: string;
                    };
                    name: {
                        type: string;
                        description: string;
                    };
                    allowEmptyValue: {
                        type: string;
                        default: boolean;
                        description: string;
                    };
                    type: {
                        type: string;
                        enum: string[];
                    };
                    format: {
                        type: string;
                    };
                    items: {
                        $ref: string;
                    };
                    collectionFormat: {
                        $ref: string;
                    };
                    default: {
                        $ref: string;
                    };
                    maximum: {
                        $ref: string;
                    };
                    exclusiveMaximum: {
                        $ref: string;
                    };
                    minimum: {
                        $ref: string;
                    };
                    exclusiveMinimum: {
                        $ref: string;
                    };
                    maxLength: {
                        $ref: string;
                    };
                    minLength: {
                        $ref: string;
                    };
                    pattern: {
                        $ref: string;
                    };
                    maxItems: {
                        $ref: string;
                    };
                    minItems: {
                        $ref: string;
                    };
                    uniqueItems: {
                        $ref: string;
                    };
                    enum: {
                        $ref: string;
                    };
                    multipleOf: {
                        $ref: string;
                    };
                };
            };
            pathParameterSubSchema: {
                additionalProperties: boolean;
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
                required: string[];
                properties: {
                    required: {
                        type: string;
                        enum: boolean[];
                        description: string;
                    };
                    in: {
                        type: string;
                        description: string;
                        enum: string[];
                    };
                    description: {
                        type: string;
                        description: string;
                    };
                    name: {
                        type: string;
                        description: string;
                    };
                    type: {
                        type: string;
                        enum: string[];
                    };
                    format: {
                        type: string;
                    };
                    items: {
                        $ref: string;
                    };
                    collectionFormat: {
                        $ref: string;
                    };
                    default: {
                        $ref: string;
                    };
                    maximum: {
                        $ref: string;
                    };
                    exclusiveMaximum: {
                        $ref: string;
                    };
                    minimum: {
                        $ref: string;
                    };
                    exclusiveMinimum: {
                        $ref: string;
                    };
                    maxLength: {
                        $ref: string;
                    };
                    minLength: {
                        $ref: string;
                    };
                    pattern: {
                        $ref: string;
                    };
                    maxItems: {
                        $ref: string;
                    };
                    minItems: {
                        $ref: string;
                    };
                    uniqueItems: {
                        $ref: string;
                    };
                    enum: {
                        $ref: string;
                    };
                    multipleOf: {
                        $ref: string;
                    };
                };
            };
            nonBodyParameter: {
                type: string;
                required: string[];
                oneOf: {
                    $ref: string;
                }[];
            };
            parameter: {
                oneOf: {
                    $ref: string;
                }[];
            };
            schema: {
                type: string;
                description: string;
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
                properties: {
                    $ref: {
                        type: string;
                    };
                    format: {
                        type: string;
                    };
                    title: {
                        $ref: string;
                    };
                    description: {
                        $ref: string;
                    };
                    default: {
                        $ref: string;
                    };
                    multipleOf: {
                        $ref: string;
                    };
                    maximum: {
                        $ref: string;
                    };
                    exclusiveMaximum: {
                        $ref: string;
                    };
                    minimum: {
                        $ref: string;
                    };
                    exclusiveMinimum: {
                        $ref: string;
                    };
                    maxLength: {
                        $ref: string;
                    };
                    minLength: {
                        $ref: string;
                    };
                    pattern: {
                        $ref: string;
                    };
                    maxItems: {
                        $ref: string;
                    };
                    minItems: {
                        $ref: string;
                    };
                    uniqueItems: {
                        $ref: string;
                    };
                    maxProperties: {
                        $ref: string;
                    };
                    minProperties: {
                        $ref: string;
                    };
                    required: {
                        $ref: string;
                    };
                    enum: {
                        $ref: string;
                    };
                    additionalProperties: {
                        anyOf: ({
                            $ref: string;
                            type?: undefined;
                        } | {
                            type: string;
                            $ref?: undefined;
                        })[];
                        default: {};
                    };
                    type: {
                        $ref: string;
                    };
                    items: {
                        anyOf: ({
                            $ref: string;
                            type?: undefined;
                            minItems?: undefined;
                            items?: undefined;
                        } | {
                            type: string;
                            minItems: number;
                            items: {
                                $ref: string;
                            };
                            $ref?: undefined;
                        })[];
                        default: {};
                    };
                    allOf: {
                        type: string;
                        minItems: number;
                        items: {
                            $ref: string;
                        };
                    };
                    properties: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                        default: {};
                    };
                    discriminator: {
                        type: string;
                    };
                    readOnly: {
                        type: string;
                        default: boolean;
                    };
                    xml: {
                        $ref: string;
                    };
                    externalDocs: {
                        $ref: string;
                    };
                    example: {};
                };
                additionalProperties: boolean;
            };
            fileSchema: {
                type: string;
                description: string;
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
                required: string[];
                properties: {
                    format: {
                        type: string;
                    };
                    title: {
                        $ref: string;
                    };
                    description: {
                        $ref: string;
                    };
                    default: {
                        $ref: string;
                    };
                    required: {
                        $ref: string;
                    };
                    type: {
                        type: string;
                        enum: string[];
                    };
                    readOnly: {
                        type: string;
                        default: boolean;
                    };
                    externalDocs: {
                        $ref: string;
                    };
                    example: {};
                };
                additionalProperties: boolean;
            };
            primitivesItems: {
                type: string;
                additionalProperties: boolean;
                properties: {
                    type: {
                        type: string;
                        enum: string[];
                    };
                    format: {
                        type: string;
                    };
                    items: {
                        $ref: string;
                    };
                    collectionFormat: {
                        $ref: string;
                    };
                    default: {
                        $ref: string;
                    };
                    maximum: {
                        $ref: string;
                    };
                    exclusiveMaximum: {
                        $ref: string;
                    };
                    minimum: {
                        $ref: string;
                    };
                    exclusiveMinimum: {
                        $ref: string;
                    };
                    maxLength: {
                        $ref: string;
                    };
                    minLength: {
                        $ref: string;
                    };
                    pattern: {
                        $ref: string;
                    };
                    maxItems: {
                        $ref: string;
                    };
                    minItems: {
                        $ref: string;
                    };
                    uniqueItems: {
                        $ref: string;
                    };
                    enum: {
                        $ref: string;
                    };
                    multipleOf: {
                        $ref: string;
                    };
                };
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
            };
            security: {
                type: string;
                items: {
                    $ref: string;
                };
                uniqueItems: boolean;
            };
            securityRequirement: {
                type: string;
                additionalProperties: {
                    type: string;
                    items: {
                        type: string;
                    };
                    uniqueItems: boolean;
                };
            };
            xml: {
                type: string;
                additionalProperties: boolean;
                properties: {
                    name: {
                        type: string;
                    };
                    namespace: {
                        type: string;
                    };
                    prefix: {
                        type: string;
                    };
                    attribute: {
                        type: string;
                        default: boolean;
                    };
                    wrapped: {
                        type: string;
                        default: boolean;
                    };
                };
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
            };
            tag: {
                type: string;
                additionalProperties: boolean;
                required: string[];
                properties: {
                    name: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                    externalDocs: {
                        $ref: string;
                    };
                };
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
            };
            securityDefinitions: {
                type: string;
                additionalProperties: {
                    oneOf: {
                        $ref: string;
                    }[];
                };
            };
            basicAuthenticationSecurity: {
                type: string;
                additionalProperties: boolean;
                required: string[];
                properties: {
                    type: {
                        type: string;
                        enum: string[];
                    };
                    description: {
                        type: string;
                    };
                };
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
            };
            apiKeySecurity: {
                type: string;
                additionalProperties: boolean;
                required: string[];
                properties: {
                    type: {
                        type: string;
                        enum: string[];
                    };
                    name: {
                        type: string;
                    };
                    in: {
                        type: string;
                        enum: string[];
                    };
                    description: {
                        type: string;
                    };
                };
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
            };
            oauth2ImplicitSecurity: {
                type: string;
                additionalProperties: boolean;
                required: string[];
                properties: {
                    type: {
                        type: string;
                        enum: string[];
                    };
                    flow: {
                        type: string;
                        enum: string[];
                    };
                    scopes: {
                        $ref: string;
                    };
                    authorizationUrl: {
                        type: string;
                        format: string;
                    };
                    description: {
                        type: string;
                    };
                };
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
            };
            oauth2PasswordSecurity: {
                type: string;
                additionalProperties: boolean;
                required: string[];
                properties: {
                    type: {
                        type: string;
                        enum: string[];
                    };
                    flow: {
                        type: string;
                        enum: string[];
                    };
                    scopes: {
                        $ref: string;
                    };
                    tokenUrl: {
                        type: string;
                        format: string;
                    };
                    description: {
                        type: string;
                    };
                };
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
            };
            oauth2ApplicationSecurity: {
                type: string;
                additionalProperties: boolean;
                required: string[];
                properties: {
                    type: {
                        type: string;
                        enum: string[];
                    };
                    flow: {
                        type: string;
                        enum: string[];
                    };
                    scopes: {
                        $ref: string;
                    };
                    tokenUrl: {
                        type: string;
                        format: string;
                    };
                    description: {
                        type: string;
                    };
                };
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
            };
            oauth2AccessCodeSecurity: {
                type: string;
                additionalProperties: boolean;
                required: string[];
                properties: {
                    type: {
                        type: string;
                        enum: string[];
                    };
                    flow: {
                        type: string;
                        enum: string[];
                    };
                    scopes: {
                        $ref: string;
                    };
                    authorizationUrl: {
                        type: string;
                        format: string;
                    };
                    tokenUrl: {
                        type: string;
                        format: string;
                    };
                    description: {
                        type: string;
                    };
                };
                patternProperties: {
                    "^x-": {
                        $ref: string;
                    };
                };
            };
            oauth2Scopes: {
                type: string;
                additionalProperties: {
                    type: string;
                };
            };
            mediaTypeList: {
                type: string;
                items: {
                    $ref: string;
                };
                uniqueItems: boolean;
            };
            parametersList: {
                type: string;
                description: string;
                additionalItems: boolean;
                items: {
                    oneOf: {
                        $ref: string;
                    }[];
                };
                uniqueItems: boolean;
            };
            schemesList: {
                type: string;
                description: string;
                items: {
                    type: string;
                    enum: string[];
                };
                uniqueItems: boolean;
            };
            collectionFormat: {
                type: string;
                enum: string[];
                default: string;
            };
            collectionFormatWithMulti: {
                type: string;
                enum: string[];
                default: string;
            };
            title: {
                $ref: string;
            };
            description: {
                $ref: string;
            };
            default: {
                $ref: string;
            };
            multipleOf: {
                $ref: string;
            };
            maximum: {
                $ref: string;
            };
            exclusiveMaximum: {
                $ref: string;
            };
            minimum: {
                $ref: string;
            };
            exclusiveMinimum: {
                $ref: string;
            };
            maxLength: {
                $ref: string;
            };
            minLength: {
                $ref: string;
            };
            pattern: {
                $ref: string;
            };
            maxItems: {
                $ref: string;
            };
            minItems: {
                $ref: string;
            };
            uniqueItems: {
                $ref: string;
            };
            enum: {
                $ref: string;
            };
            jsonReference: {
                type: string;
                required: string[];
                additionalProperties: boolean;
                properties: {
                    $ref: {
                        type: string;
                    };
                };
            };
        };
    };
    readonly v3: {
        id: string;
        $schema: string;
        description: string;
        type: string;
        required: string[];
        properties: {
            openapi: {
                type: string;
                pattern: string;
            };
            info: {
                $ref: string;
            };
            externalDocs: {
                $ref: string;
            };
            servers: {
                type: string;
                items: {
                    $ref: string;
                };
            };
            security: {
                type: string;
                items: {
                    $ref: string;
                };
            };
            tags: {
                type: string;
                items: {
                    $ref: string;
                };
                uniqueItems: boolean;
            };
            paths: {
                $ref: string;
            };
            components: {
                $ref: string;
            };
        };
        patternProperties: {
            "^x-": {};
        };
        additionalProperties: boolean;
        definitions: {
            Reference: {
                type: string;
                required: string[];
                patternProperties: {
                    "^\\$ref$": {
                        type: string;
                        format: string;
                    };
                };
            };
            Info: {
                type: string;
                required: string[];
                properties: {
                    title: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                    termsOfService: {
                        type: string;
                        format: string;
                    };
                    contact: {
                        $ref: string;
                    };
                    license: {
                        $ref: string;
                    };
                    version: {
                        type: string;
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            Contact: {
                type: string;
                properties: {
                    name: {
                        type: string;
                    };
                    url: {
                        type: string;
                        format: string;
                    };
                    email: {
                        type: string;
                        format: string;
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            License: {
                type: string;
                required: string[];
                properties: {
                    name: {
                        type: string;
                    };
                    url: {
                        type: string;
                        format: string;
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            Server: {
                type: string;
                required: string[];
                properties: {
                    url: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                    variables: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            ServerVariable: {
                type: string;
                required: string[];
                properties: {
                    enum: {
                        type: string;
                        items: {
                            type: string;
                        };
                    };
                    default: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            Components: {
                type: string;
                properties: {
                    schemas: {
                        type: string;
                        patternProperties: {
                            "^[a-zA-Z0-9\\.\\-_]+$": {
                                oneOf: {
                                    $ref: string;
                                }[];
                            };
                        };
                    };
                    responses: {
                        type: string;
                        patternProperties: {
                            "^[a-zA-Z0-9\\.\\-_]+$": {
                                oneOf: {
                                    $ref: string;
                                }[];
                            };
                        };
                    };
                    parameters: {
                        type: string;
                        patternProperties: {
                            "^[a-zA-Z0-9\\.\\-_]+$": {
                                oneOf: {
                                    $ref: string;
                                }[];
                            };
                        };
                    };
                    examples: {
                        type: string;
                        patternProperties: {
                            "^[a-zA-Z0-9\\.\\-_]+$": {
                                oneOf: {
                                    $ref: string;
                                }[];
                            };
                        };
                    };
                    requestBodies: {
                        type: string;
                        patternProperties: {
                            "^[a-zA-Z0-9\\.\\-_]+$": {
                                oneOf: {
                                    $ref: string;
                                }[];
                            };
                        };
                    };
                    headers: {
                        type: string;
                        patternProperties: {
                            "^[a-zA-Z0-9\\.\\-_]+$": {
                                oneOf: {
                                    $ref: string;
                                }[];
                            };
                        };
                    };
                    securitySchemes: {
                        type: string;
                        patternProperties: {
                            "^[a-zA-Z0-9\\.\\-_]+$": {
                                oneOf: {
                                    $ref: string;
                                }[];
                            };
                        };
                    };
                    links: {
                        type: string;
                        patternProperties: {
                            "^[a-zA-Z0-9\\.\\-_]+$": {
                                oneOf: {
                                    $ref: string;
                                }[];
                            };
                        };
                    };
                    callbacks: {
                        type: string;
                        patternProperties: {
                            "^[a-zA-Z0-9\\.\\-_]+$": {
                                oneOf: {
                                    $ref: string;
                                }[];
                            };
                        };
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            Schema: {
                type: string;
                properties: {
                    title: {
                        type: string;
                    };
                    multipleOf: {
                        type: string;
                        minimum: number;
                        exclusiveMinimum: boolean;
                    };
                    maximum: {
                        type: string;
                    };
                    exclusiveMaximum: {
                        type: string;
                        default: boolean;
                    };
                    minimum: {
                        type: string;
                    };
                    exclusiveMinimum: {
                        type: string;
                        default: boolean;
                    };
                    maxLength: {
                        type: string;
                        minimum: number;
                    };
                    minLength: {
                        type: string;
                        minimum: number;
                        default: number;
                    };
                    pattern: {
                        type: string;
                        format: string;
                    };
                    maxItems: {
                        type: string;
                        minimum: number;
                    };
                    minItems: {
                        type: string;
                        minimum: number;
                        default: number;
                    };
                    uniqueItems: {
                        type: string;
                        default: boolean;
                    };
                    maxProperties: {
                        type: string;
                        minimum: number;
                    };
                    minProperties: {
                        type: string;
                        minimum: number;
                        default: number;
                    };
                    required: {
                        type: string;
                        items: {
                            type: string;
                        };
                        minItems: number;
                        uniqueItems: boolean;
                    };
                    enum: {
                        type: string;
                        items: {};
                        minItems: number;
                        uniqueItems: boolean;
                    };
                    type: {
                        type: string;
                        enum: string[];
                    };
                    not: {
                        oneOf: {
                            $ref: string;
                        }[];
                    };
                    allOf: {
                        type: string;
                        items: {
                            oneOf: {
                                $ref: string;
                            }[];
                        };
                    };
                    oneOf: {
                        type: string;
                        items: {
                            oneOf: {
                                $ref: string;
                            }[];
                        };
                    };
                    anyOf: {
                        type: string;
                        items: {
                            oneOf: {
                                $ref: string;
                            }[];
                        };
                    };
                    items: {
                        oneOf: {
                            $ref: string;
                        }[];
                    };
                    properties: {
                        type: string;
                        additionalProperties: {
                            oneOf: {
                                $ref: string;
                            }[];
                        };
                    };
                    additionalProperties: {
                        oneOf: ({
                            $ref: string;
                            type?: undefined;
                        } | {
                            type: string;
                            $ref?: undefined;
                        })[];
                        default: boolean;
                    };
                    description: {
                        type: string;
                    };
                    format: {
                        type: string;
                    };
                    default: {};
                    nullable: {
                        type: string;
                        default: boolean;
                    };
                    discriminator: {
                        $ref: string;
                    };
                    readOnly: {
                        type: string;
                        default: boolean;
                    };
                    writeOnly: {
                        type: string;
                        default: boolean;
                    };
                    example: {};
                    externalDocs: {
                        $ref: string;
                    };
                    deprecated: {
                        type: string;
                        default: boolean;
                    };
                    xml: {
                        $ref: string;
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            Discriminator: {
                type: string;
                required: string[];
                properties: {
                    propertyName: {
                        type: string;
                    };
                    mapping: {
                        type: string;
                        additionalProperties: {
                            type: string;
                        };
                    };
                };
            };
            XML: {
                type: string;
                properties: {
                    name: {
                        type: string;
                    };
                    namespace: {
                        type: string;
                        format: string;
                    };
                    prefix: {
                        type: string;
                    };
                    attribute: {
                        type: string;
                        default: boolean;
                    };
                    wrapped: {
                        type: string;
                        default: boolean;
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            Response: {
                type: string;
                required: string[];
                properties: {
                    description: {
                        type: string;
                    };
                    headers: {
                        type: string;
                        additionalProperties: {
                            oneOf: {
                                $ref: string;
                            }[];
                        };
                    };
                    content: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    links: {
                        type: string;
                        additionalProperties: {
                            oneOf: {
                                $ref: string;
                            }[];
                        };
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            MediaType: {
                type: string;
                properties: {
                    schema: {
                        oneOf: {
                            $ref: string;
                        }[];
                    };
                    example: {};
                    examples: {
                        type: string;
                        additionalProperties: {
                            oneOf: {
                                $ref: string;
                            }[];
                        };
                    };
                    encoding: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
                allOf: {
                    $ref: string;
                }[];
            };
            Example: {
                type: string;
                properties: {
                    summary: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                    value: {};
                    externalValue: {
                        type: string;
                        format: string;
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            Header: {
                type: string;
                properties: {
                    description: {
                        type: string;
                    };
                    required: {
                        type: string;
                        default: boolean;
                    };
                    deprecated: {
                        type: string;
                        default: boolean;
                    };
                    allowEmptyValue: {
                        type: string;
                        default: boolean;
                    };
                    style: {
                        type: string;
                        enum: string[];
                        default: string;
                    };
                    explode: {
                        type: string;
                    };
                    allowReserved: {
                        type: string;
                        default: boolean;
                    };
                    schema: {
                        oneOf: {
                            $ref: string;
                        }[];
                    };
                    content: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                        minProperties: number;
                        maxProperties: number;
                    };
                    example: {};
                    examples: {
                        type: string;
                        additionalProperties: {
                            oneOf: {
                                $ref: string;
                            }[];
                        };
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
                allOf: {
                    $ref: string;
                }[];
            };
            Paths: {
                type: string;
                patternProperties: {
                    "^\\/": {
                        $ref: string;
                    };
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            PathItem: {
                type: string;
                properties: {
                    $ref: {
                        type: string;
                    };
                    summary: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                    servers: {
                        type: string;
                        items: {
                            $ref: string;
                        };
                    };
                    parameters: {
                        type: string;
                        items: {
                            oneOf: {
                                $ref: string;
                            }[];
                        };
                        uniqueItems: boolean;
                    };
                };
                patternProperties: {
                    "^(get|put|post|delete|options|head|patch|trace)$": {
                        $ref: string;
                    };
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            Operation: {
                type: string;
                required: string[];
                properties: {
                    tags: {
                        type: string;
                        items: {
                            type: string;
                        };
                    };
                    summary: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                    externalDocs: {
                        $ref: string;
                    };
                    operationId: {
                        type: string;
                    };
                    parameters: {
                        type: string;
                        items: {
                            oneOf: {
                                $ref: string;
                            }[];
                        };
                        uniqueItems: boolean;
                    };
                    requestBody: {
                        oneOf: {
                            $ref: string;
                        }[];
                    };
                    responses: {
                        $ref: string;
                    };
                    callbacks: {
                        type: string;
                        additionalProperties: {
                            oneOf: {
                                $ref: string;
                            }[];
                        };
                    };
                    deprecated: {
                        type: string;
                        default: boolean;
                    };
                    security: {
                        type: string;
                        items: {
                            $ref: string;
                        };
                    };
                    servers: {
                        type: string;
                        items: {
                            $ref: string;
                        };
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            Responses: {
                type: string;
                properties: {
                    default: {
                        oneOf: {
                            $ref: string;
                        }[];
                    };
                };
                patternProperties: {
                    "^[1-5](?:\\d{2}|XX)$": {
                        oneOf: {
                            $ref: string;
                        }[];
                    };
                    "^x-": {};
                };
                minProperties: number;
                additionalProperties: boolean;
            };
            SecurityRequirement: {
                type: string;
                additionalProperties: {
                    type: string;
                    items: {
                        type: string;
                    };
                };
            };
            Tag: {
                type: string;
                required: string[];
                properties: {
                    name: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                    externalDocs: {
                        $ref: string;
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            ExternalDocumentation: {
                type: string;
                required: string[];
                properties: {
                    description: {
                        type: string;
                    };
                    url: {
                        type: string;
                        format: string;
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            ExampleXORExamples: {
                description: string;
                not: {
                    required: string[];
                };
            };
            SchemaXORContent: {
                description: string;
                not: {
                    required: string[];
                };
                oneOf: ({
                    required: string[];
                    description?: undefined;
                    allOf?: undefined;
                } | {
                    required: string[];
                    description: string;
                    allOf: {
                        not: {
                            required: string[];
                        };
                    }[];
                })[];
            };
            Parameter: {
                type: string;
                properties: {
                    name: {
                        type: string;
                    };
                    in: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                    required: {
                        type: string;
                        default: boolean;
                    };
                    deprecated: {
                        type: string;
                        default: boolean;
                    };
                    allowEmptyValue: {
                        type: string;
                        default: boolean;
                    };
                    style: {
                        type: string;
                    };
                    explode: {
                        type: string;
                    };
                    allowReserved: {
                        type: string;
                        default: boolean;
                    };
                    schema: {
                        oneOf: {
                            $ref: string;
                        }[];
                    };
                    content: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                        minProperties: number;
                        maxProperties: number;
                    };
                    example: {};
                    examples: {
                        type: string;
                        additionalProperties: {
                            oneOf: {
                                $ref: string;
                            }[];
                        };
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
                required: string[];
                allOf: {
                    $ref: string;
                }[];
            };
            ParameterLocation: {
                description: string;
                oneOf: ({
                    description: string;
                    required: string[];
                    properties: {
                        in: {
                            enum: string[];
                        };
                        style: {
                            enum: string[];
                            default: string;
                        };
                        required: {
                            enum: boolean[];
                        };
                    };
                } | {
                    description: string;
                    properties: {
                        in: {
                            enum: string[];
                        };
                        style: {
                            enum: string[];
                            default: string;
                        };
                        required?: undefined;
                    };
                    required?: undefined;
                })[];
            };
            RequestBody: {
                type: string;
                required: string[];
                properties: {
                    description: {
                        type: string;
                    };
                    content: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    required: {
                        type: string;
                        default: boolean;
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            SecurityScheme: {
                oneOf: {
                    $ref: string;
                }[];
            };
            APIKeySecurityScheme: {
                type: string;
                required: string[];
                properties: {
                    type: {
                        type: string;
                        enum: string[];
                    };
                    name: {
                        type: string;
                    };
                    in: {
                        type: string;
                        enum: string[];
                    };
                    description: {
                        type: string;
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            HTTPSecurityScheme: {
                type: string;
                required: string[];
                properties: {
                    scheme: {
                        type: string;
                    };
                    bearerFormat: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                    type: {
                        type: string;
                        enum: string[];
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
                oneOf: ({
                    description: string;
                    properties: {
                        scheme: {
                            type: string;
                            pattern: string;
                            not?: undefined;
                        };
                    };
                    not?: undefined;
                } | {
                    description: string;
                    not: {
                        required: string[];
                    };
                    properties: {
                        scheme: {
                            not: {
                                type: string;
                                pattern: string;
                            };
                            type?: undefined;
                            pattern?: undefined;
                        };
                    };
                })[];
            };
            OAuth2SecurityScheme: {
                type: string;
                required: string[];
                properties: {
                    type: {
                        type: string;
                        enum: string[];
                    };
                    flows: {
                        $ref: string;
                    };
                    description: {
                        type: string;
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            OpenIdConnectSecurityScheme: {
                type: string;
                required: string[];
                properties: {
                    type: {
                        type: string;
                        enum: string[];
                    };
                    openIdConnectUrl: {
                        type: string;
                        format: string;
                    };
                    description: {
                        type: string;
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            OAuthFlows: {
                type: string;
                properties: {
                    implicit: {
                        $ref: string;
                    };
                    password: {
                        $ref: string;
                    };
                    clientCredentials: {
                        $ref: string;
                    };
                    authorizationCode: {
                        $ref: string;
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            ImplicitOAuthFlow: {
                type: string;
                required: string[];
                properties: {
                    authorizationUrl: {
                        type: string;
                        format: string;
                    };
                    refreshUrl: {
                        type: string;
                        format: string;
                    };
                    scopes: {
                        type: string;
                        additionalProperties: {
                            type: string;
                        };
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            PasswordOAuthFlow: {
                type: string;
                required: string[];
                properties: {
                    tokenUrl: {
                        type: string;
                        format: string;
                    };
                    refreshUrl: {
                        type: string;
                        format: string;
                    };
                    scopes: {
                        type: string;
                        additionalProperties: {
                            type: string;
                        };
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            ClientCredentialsFlow: {
                type: string;
                required: string[];
                properties: {
                    tokenUrl: {
                        type: string;
                        format: string;
                    };
                    refreshUrl: {
                        type: string;
                        format: string;
                    };
                    scopes: {
                        type: string;
                        additionalProperties: {
                            type: string;
                        };
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            AuthorizationCodeOAuthFlow: {
                type: string;
                required: string[];
                properties: {
                    authorizationUrl: {
                        type: string;
                        format: string;
                    };
                    tokenUrl: {
                        type: string;
                        format: string;
                    };
                    refreshUrl: {
                        type: string;
                        format: string;
                    };
                    scopes: {
                        type: string;
                        additionalProperties: {
                            type: string;
                        };
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
            Link: {
                type: string;
                properties: {
                    operationId: {
                        type: string;
                    };
                    operationRef: {
                        type: string;
                        format: string;
                    };
                    parameters: {
                        type: string;
                        additionalProperties: {};
                    };
                    requestBody: {};
                    description: {
                        type: string;
                    };
                    server: {
                        $ref: string;
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
                not: {
                    description: string;
                    required: string[];
                };
            };
            Callback: {
                type: string;
                additionalProperties: {
                    $ref: string;
                };
                patternProperties: {
                    "^x-": {};
                };
            };
            Encoding: {
                type: string;
                properties: {
                    contentType: {
                        type: string;
                    };
                    headers: {
                        type: string;
                        additionalProperties: {
                            oneOf: {
                                $ref: string;
                            }[];
                        };
                    };
                    style: {
                        type: string;
                        enum: string[];
                    };
                    explode: {
                        type: string;
                    };
                    allowReserved: {
                        type: string;
                        default: boolean;
                    };
                };
                patternProperties: {
                    "^x-": {};
                };
                additionalProperties: boolean;
            };
        };
    };
    readonly v31: {
        $id: string;
        $schema: string;
        description: string;
        type: string;
        properties: {
            openapi: {
                type: string;
                pattern: string;
            };
            info: {
                $ref: string;
            };
            jsonSchemaDialect: {
                type: string;
                format: string;
                default: string;
            };
            servers: {
                type: string;
                items: {
                    $ref: string;
                };
                default: {
                    url: string;
                }[];
            };
            paths: {
                $ref: string;
            };
            webhooks: {
                type: string;
                additionalProperties: {
                    $ref: string;
                };
            };
            components: {
                $ref: string;
            };
            security: {
                type: string;
                items: {
                    $ref: string;
                };
            };
            tags: {
                type: string;
                items: {
                    $ref: string;
                };
            };
            externalDocs: {
                $ref: string;
            };
        };
        required: string[];
        anyOf: {
            required: string[];
        }[];
        $ref: string;
        unevaluatedProperties: boolean;
        $defs: {
            info: {
                $comment: string;
                type: string;
                properties: {
                    title: {
                        type: string;
                    };
                    summary: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                    termsOfService: {
                        type: string;
                        format: string;
                    };
                    contact: {
                        $ref: string;
                    };
                    license: {
                        $ref: string;
                    };
                    version: {
                        type: string;
                    };
                };
                required: string[];
                $ref: string;
                unevaluatedProperties: boolean;
            };
            contact: {
                $comment: string;
                type: string;
                properties: {
                    name: {
                        type: string;
                    };
                    url: {
                        type: string;
                        format: string;
                    };
                    email: {
                        type: string;
                        format: string;
                    };
                };
                $ref: string;
                unevaluatedProperties: boolean;
            };
            license: {
                $comment: string;
                type: string;
                properties: {
                    name: {
                        type: string;
                    };
                    identifier: {
                        type: string;
                    };
                    url: {
                        type: string;
                        format: string;
                    };
                };
                required: string[];
                dependentSchemas: {
                    identifier: {
                        not: {
                            required: string[];
                        };
                    };
                };
                $ref: string;
                unevaluatedProperties: boolean;
            };
            server: {
                $comment: string;
                type: string;
                properties: {
                    url: {
                        type: string;
                        format: string;
                    };
                    description: {
                        type: string;
                    };
                    variables: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                };
                required: string[];
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "server-variable": {
                $comment: string;
                type: string;
                properties: {
                    enum: {
                        type: string;
                        items: {
                            type: string;
                        };
                        minItems: number;
                    };
                    default: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                };
                required: string[];
                $ref: string;
                unevaluatedProperties: boolean;
            };
            components: {
                $comment: string;
                type: string;
                properties: {
                    schemas: {
                        type: string;
                        additionalProperties: {
                            $dynamicRef: string;
                        };
                    };
                    responses: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    parameters: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    examples: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    requestBodies: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    headers: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    securitySchemes: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    links: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    callbacks: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    pathItems: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                };
                patternProperties: {
                    "^(schemas|responses|parameters|examples|requestBodies|headers|securitySchemes|links|callbacks|pathItems)$": {
                        $comment: string;
                        propertyNames: {
                            pattern: string;
                        };
                    };
                };
                $ref: string;
                unevaluatedProperties: boolean;
            };
            paths: {
                $comment: string;
                type: string;
                patternProperties: {
                    "^/": {
                        $ref: string;
                    };
                };
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "path-item": {
                $comment: string;
                type: string;
                properties: {
                    summary: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                    servers: {
                        type: string;
                        items: {
                            $ref: string;
                        };
                    };
                    parameters: {
                        type: string;
                        items: {
                            $ref: string;
                        };
                    };
                    get: {
                        $ref: string;
                    };
                    put: {
                        $ref: string;
                    };
                    post: {
                        $ref: string;
                    };
                    delete: {
                        $ref: string;
                    };
                    options: {
                        $ref: string;
                    };
                    head: {
                        $ref: string;
                    };
                    patch: {
                        $ref: string;
                    };
                    trace: {
                        $ref: string;
                    };
                };
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "path-item-or-reference": {
                if: {
                    type: string;
                    required: string[];
                };
                then: {
                    $ref: string;
                };
                else: {
                    $ref: string;
                };
            };
            operation: {
                $comment: string;
                type: string;
                properties: {
                    tags: {
                        type: string;
                        items: {
                            type: string;
                        };
                    };
                    summary: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                    externalDocs: {
                        $ref: string;
                    };
                    operationId: {
                        type: string;
                    };
                    parameters: {
                        type: string;
                        items: {
                            $ref: string;
                        };
                    };
                    requestBody: {
                        $ref: string;
                    };
                    responses: {
                        $ref: string;
                    };
                    callbacks: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    deprecated: {
                        default: boolean;
                        type: string;
                    };
                    security: {
                        type: string;
                        items: {
                            $ref: string;
                        };
                    };
                    servers: {
                        type: string;
                        items: {
                            $ref: string;
                        };
                    };
                };
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "external-documentation": {
                $comment: string;
                type: string;
                properties: {
                    description: {
                        type: string;
                    };
                    url: {
                        type: string;
                        format: string;
                    };
                };
                required: string[];
                $ref: string;
                unevaluatedProperties: boolean;
            };
            parameter: {
                $comment: string;
                type: string;
                properties: {
                    name: {
                        type: string;
                    };
                    in: {
                        enum: string[];
                    };
                    description: {
                        type: string;
                    };
                    required: {
                        default: boolean;
                        type: string;
                    };
                    deprecated: {
                        default: boolean;
                        type: string;
                    };
                    schema: {
                        $dynamicRef: string;
                    };
                    content: {
                        $ref: string;
                        minProperties: number;
                        maxProperties: number;
                    };
                };
                required: string[];
                oneOf: {
                    required: string[];
                }[];
                if: {
                    properties: {
                        in: {
                            const: string;
                        };
                    };
                    required: string[];
                };
                then: {
                    properties: {
                        allowEmptyValue: {
                            default: boolean;
                            type: string;
                        };
                    };
                };
                dependentSchemas: {
                    schema: {
                        properties: {
                            style: {
                                type: string;
                            };
                            explode: {
                                type: string;
                            };
                        };
                        allOf: {
                            $ref: string;
                        }[];
                        $defs: {
                            "styles-for-path": {
                                if: {
                                    properties: {
                                        in: {
                                            const: string;
                                        };
                                    };
                                    required: string[];
                                };
                                then: {
                                    properties: {
                                        style: {
                                            default: string;
                                            enum: string[];
                                        };
                                        required: {
                                            const: boolean;
                                        };
                                    };
                                    required: string[];
                                };
                            };
                            "styles-for-header": {
                                if: {
                                    properties: {
                                        in: {
                                            const: string;
                                        };
                                    };
                                    required: string[];
                                };
                                then: {
                                    properties: {
                                        style: {
                                            default: string;
                                            const: string;
                                        };
                                    };
                                };
                            };
                            "styles-for-query": {
                                if: {
                                    properties: {
                                        in: {
                                            const: string;
                                        };
                                    };
                                    required: string[];
                                };
                                then: {
                                    properties: {
                                        style: {
                                            default: string;
                                            enum: string[];
                                        };
                                        allowReserved: {
                                            default: boolean;
                                            type: string;
                                        };
                                    };
                                };
                            };
                            "styles-for-cookie": {
                                if: {
                                    properties: {
                                        in: {
                                            const: string;
                                        };
                                    };
                                    required: string[];
                                };
                                then: {
                                    properties: {
                                        style: {
                                            default: string;
                                            const: string;
                                        };
                                    };
                                };
                            };
                        };
                    };
                };
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "parameter-or-reference": {
                if: {
                    type: string;
                    required: string[];
                };
                then: {
                    $ref: string;
                };
                else: {
                    $ref: string;
                };
            };
            "request-body": {
                $comment: string;
                type: string;
                properties: {
                    description: {
                        type: string;
                    };
                    content: {
                        $ref: string;
                    };
                    required: {
                        default: boolean;
                        type: string;
                    };
                };
                required: string[];
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "request-body-or-reference": {
                if: {
                    type: string;
                    required: string[];
                };
                then: {
                    $ref: string;
                };
                else: {
                    $ref: string;
                };
            };
            content: {
                $comment: string;
                type: string;
                additionalProperties: {
                    $ref: string;
                };
                propertyNames: {
                    format: string;
                };
            };
            "media-type": {
                $comment: string;
                type: string;
                properties: {
                    schema: {
                        $dynamicRef: string;
                    };
                    encoding: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                };
                allOf: {
                    $ref: string;
                }[];
                unevaluatedProperties: boolean;
            };
            encoding: {
                $comment: string;
                type: string;
                properties: {
                    contentType: {
                        type: string;
                        format: string;
                    };
                    headers: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    style: {
                        default: string;
                        enum: string[];
                    };
                    explode: {
                        type: string;
                    };
                    allowReserved: {
                        default: boolean;
                        type: string;
                    };
                };
                allOf: {
                    $ref: string;
                }[];
                unevaluatedProperties: boolean;
            };
            responses: {
                $comment: string;
                type: string;
                properties: {
                    default: {
                        $ref: string;
                    };
                };
                patternProperties: {
                    "^[1-5](?:[0-9]{2}|XX)$": {
                        $ref: string;
                    };
                };
                minProperties: number;
                $ref: string;
                unevaluatedProperties: boolean;
                if: {
                    $comment: string;
                    patternProperties: {
                        "^[1-5](?:[0-9]{2}|XX)$": boolean;
                    };
                };
                then: {
                    required: string[];
                };
            };
            response: {
                $comment: string;
                type: string;
                properties: {
                    description: {
                        type: string;
                    };
                    headers: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    content: {
                        $ref: string;
                    };
                    links: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                };
                required: string[];
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "response-or-reference": {
                if: {
                    type: string;
                    required: string[];
                };
                then: {
                    $ref: string;
                };
                else: {
                    $ref: string;
                };
            };
            callbacks: {
                $comment: string;
                type: string;
                $ref: string;
                additionalProperties: {
                    $ref: string;
                };
            };
            "callbacks-or-reference": {
                if: {
                    type: string;
                    required: string[];
                };
                then: {
                    $ref: string;
                };
                else: {
                    $ref: string;
                };
            };
            example: {
                $comment: string;
                type: string;
                properties: {
                    summary: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                    value: boolean;
                    externalValue: {
                        type: string;
                        format: string;
                    };
                };
                not: {
                    required: string[];
                };
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "example-or-reference": {
                if: {
                    type: string;
                    required: string[];
                };
                then: {
                    $ref: string;
                };
                else: {
                    $ref: string;
                };
            };
            link: {
                $comment: string;
                type: string;
                properties: {
                    operationRef: {
                        type: string;
                        format: string;
                    };
                    operationId: {
                        type: string;
                    };
                    parameters: {
                        $ref: string;
                    };
                    requestBody: boolean;
                    description: {
                        type: string;
                    };
                    body: {
                        $ref: string;
                    };
                };
                oneOf: {
                    required: string[];
                }[];
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "link-or-reference": {
                if: {
                    type: string;
                    required: string[];
                };
                then: {
                    $ref: string;
                };
                else: {
                    $ref: string;
                };
            };
            header: {
                $comment: string;
                type: string;
                properties: {
                    description: {
                        type: string;
                    };
                    required: {
                        default: boolean;
                        type: string;
                    };
                    deprecated: {
                        default: boolean;
                        type: string;
                    };
                    schema: {
                        $dynamicRef: string;
                    };
                    content: {
                        $ref: string;
                        minProperties: number;
                        maxProperties: number;
                    };
                };
                oneOf: {
                    required: string[];
                }[];
                dependentSchemas: {
                    schema: {
                        properties: {
                            style: {
                                default: string;
                                const: string;
                            };
                            explode: {
                                default: boolean;
                                type: string;
                            };
                        };
                        $ref: string;
                    };
                };
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "header-or-reference": {
                if: {
                    type: string;
                    required: string[];
                };
                then: {
                    $ref: string;
                };
                else: {
                    $ref: string;
                };
            };
            tag: {
                $comment: string;
                type: string;
                properties: {
                    name: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                    externalDocs: {
                        $ref: string;
                    };
                };
                required: string[];
                $ref: string;
                unevaluatedProperties: boolean;
            };
            reference: {
                $comment: string;
                type: string;
                properties: {
                    $ref: {
                        type: string;
                        format: string;
                    };
                    summary: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                };
            };
            schema: {
                $comment: string;
                $dynamicAnchor: string;
                type: string[];
            };
            "security-scheme": {
                $comment: string;
                type: string;
                properties: {
                    type: {
                        enum: string[];
                    };
                    description: {
                        type: string;
                    };
                };
                required: string[];
                allOf: {
                    $ref: string;
                }[];
                unevaluatedProperties: boolean;
                $defs: {
                    "type-apikey": {
                        if: {
                            properties: {
                                type: {
                                    const: string;
                                };
                            };
                            required: string[];
                        };
                        then: {
                            properties: {
                                name: {
                                    type: string;
                                };
                                in: {
                                    enum: string[];
                                };
                            };
                            required: string[];
                        };
                    };
                    "type-http": {
                        if: {
                            properties: {
                                type: {
                                    const: string;
                                };
                            };
                            required: string[];
                        };
                        then: {
                            properties: {
                                scheme: {
                                    type: string;
                                };
                            };
                            required: string[];
                        };
                    };
                    "type-http-bearer": {
                        if: {
                            properties: {
                                type: {
                                    const: string;
                                };
                                scheme: {
                                    type: string;
                                    pattern: string;
                                };
                            };
                            required: string[];
                        };
                        then: {
                            properties: {
                                bearerFormat: {
                                    type: string;
                                };
                            };
                        };
                    };
                    "type-oauth2": {
                        if: {
                            properties: {
                                type: {
                                    const: string;
                                };
                            };
                            required: string[];
                        };
                        then: {
                            properties: {
                                flows: {
                                    $ref: string;
                                };
                            };
                            required: string[];
                        };
                    };
                    "type-oidc": {
                        if: {
                            properties: {
                                type: {
                                    const: string;
                                };
                            };
                            required: string[];
                        };
                        then: {
                            properties: {
                                openIdConnectUrl: {
                                    type: string;
                                    format: string;
                                };
                            };
                            required: string[];
                        };
                    };
                };
            };
            "security-scheme-or-reference": {
                if: {
                    type: string;
                    required: string[];
                };
                then: {
                    $ref: string;
                };
                else: {
                    $ref: string;
                };
            };
            "oauth-flows": {
                type: string;
                properties: {
                    implicit: {
                        $ref: string;
                    };
                    password: {
                        $ref: string;
                    };
                    clientCredentials: {
                        $ref: string;
                    };
                    authorizationCode: {
                        $ref: string;
                    };
                };
                $ref: string;
                unevaluatedProperties: boolean;
                $defs: {
                    implicit: {
                        type: string;
                        properties: {
                            authorizationUrl: {
                                type: string;
                                format: string;
                            };
                            refreshUrl: {
                                type: string;
                                format: string;
                            };
                            scopes: {
                                $ref: string;
                            };
                        };
                        required: string[];
                        $ref: string;
                        unevaluatedProperties: boolean;
                    };
                    password: {
                        type: string;
                        properties: {
                            tokenUrl: {
                                type: string;
                                format: string;
                            };
                            refreshUrl: {
                                type: string;
                                format: string;
                            };
                            scopes: {
                                $ref: string;
                            };
                        };
                        required: string[];
                        $ref: string;
                        unevaluatedProperties: boolean;
                    };
                    "client-credentials": {
                        type: string;
                        properties: {
                            tokenUrl: {
                                type: string;
                                format: string;
                            };
                            refreshUrl: {
                                type: string;
                                format: string;
                            };
                            scopes: {
                                $ref: string;
                            };
                        };
                        required: string[];
                        $ref: string;
                        unevaluatedProperties: boolean;
                    };
                    "authorization-code": {
                        type: string;
                        properties: {
                            authorizationUrl: {
                                type: string;
                                format: string;
                            };
                            tokenUrl: {
                                type: string;
                                format: string;
                            };
                            refreshUrl: {
                                type: string;
                                format: string;
                            };
                            scopes: {
                                $ref: string;
                            };
                        };
                        required: string[];
                        $ref: string;
                        unevaluatedProperties: boolean;
                    };
                };
            };
            "security-requirement": {
                $comment: string;
                type: string;
                additionalProperties: {
                    type: string;
                    items: {
                        type: string;
                    };
                };
            };
            "specification-extensions": {
                $comment: string;
                patternProperties: {
                    "^x-": boolean;
                };
            };
            examples: {
                properties: {
                    example: boolean;
                    examples: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                };
            };
            "map-of-strings": {
                type: string;
                additionalProperties: {
                    type: string;
                };
            };
            "styles-for-form": {
                if: {
                    properties: {
                        style: {
                            const: string;
                        };
                    };
                    required: string[];
                };
                then: {
                    properties: {
                        explode: {
                            default: boolean;
                        };
                    };
                };
                else: {
                    properties: {
                        explode: {
                            default: boolean;
                        };
                    };
                };
            };
        };
    };
    readonly v31legacy: {
        $id: string;
        $schema: string;
        description: string;
        type: string;
        properties: {
            openapi: {
                type: string;
                pattern: string;
            };
            info: {
                $ref: string;
            };
            jsonSchemaDialect: {
                type: string;
                format: string;
                default: string;
            };
            servers: {
                type: string;
                items: {
                    $ref: string;
                };
                default: {
                    url: string;
                }[];
            };
            paths: {
                $ref: string;
            };
            webhooks: {
                type: string;
                additionalProperties: {
                    $ref: string;
                };
            };
            components: {
                $ref: string;
            };
            security: {
                type: string;
                items: {
                    $ref: string;
                };
            };
            tags: {
                type: string;
                items: {
                    $ref: string;
                };
            };
            externalDocs: {
                $ref: string;
            };
        };
        required: string[];
        anyOf: {
            required: string[];
        }[];
        $ref: string;
        unevaluatedProperties: boolean;
        $defs: {
            info: {
                $comment: string;
                type: string;
                properties: {
                    title: {
                        type: string;
                    };
                    summary: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                    termsOfService: {
                        type: string;
                        format: string;
                    };
                    contact: {
                        $ref: string;
                    };
                    license: {
                        $ref: string;
                    };
                    version: {
                        type: string;
                    };
                };
                required: string[];
                $ref: string;
                unevaluatedProperties: boolean;
            };
            contact: {
                $comment: string;
                type: string;
                properties: {
                    name: {
                        type: string;
                    };
                    url: {
                        type: string;
                        format: string;
                    };
                    email: {
                        type: string;
                        format: string;
                    };
                };
                $ref: string;
                unevaluatedProperties: boolean;
            };
            license: {
                $comment: string;
                type: string;
                properties: {
                    name: {
                        type: string;
                    };
                    identifier: {
                        type: string;
                    };
                    url: {
                        type: string;
                        format: string;
                    };
                };
                required: string[];
                dependentSchemas: {
                    identifier: {
                        not: {
                            required: string[];
                        };
                    };
                };
                $ref: string;
                unevaluatedProperties: boolean;
            };
            server: {
                $comment: string;
                type: string;
                properties: {
                    url: {
                        type: string;
                        format: string;
                    };
                    description: {
                        type: string;
                    };
                    variables: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                };
                required: string[];
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "server-variable": {
                $comment: string;
                type: string;
                properties: {
                    enum: {
                        type: string;
                        items: {
                            type: string;
                        };
                        minItems: number;
                    };
                    default: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                };
                required: string[];
                $ref: string;
                unevaluatedProperties: boolean;
            };
            components: {
                $comment: string;
                type: string;
                properties: {
                    schemas: {
                        type: string;
                        additionalProperties: {
                            $dynamicRef: string;
                        };
                    };
                    responses: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    parameters: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    examples: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    requestBodies: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    headers: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    securitySchemes: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    links: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    callbacks: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    pathItems: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                };
                patternProperties: {
                    "^(schemas|responses|parameters|examples|requestBodies|headers|securitySchemes|links|callbacks|pathItems)$": {
                        $comment: string;
                        propertyNames: {
                            pattern: string;
                        };
                    };
                };
                $ref: string;
                unevaluatedProperties: boolean;
            };
            paths: {
                $comment: string;
                type: string;
                patternProperties: {
                    "^/": {
                        $ref: string;
                    };
                };
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "path-item": {
                $comment: string;
                type: string;
                properties: {
                    summary: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                    servers: {
                        type: string;
                        items: {
                            $ref: string;
                        };
                    };
                    parameters: {
                        type: string;
                        items: {
                            $ref: string;
                        };
                    };
                    get: {
                        $ref: string;
                    };
                    put: {
                        $ref: string;
                    };
                    post: {
                        $ref: string;
                    };
                    delete: {
                        $ref: string;
                    };
                    options: {
                        $ref: string;
                    };
                    head: {
                        $ref: string;
                    };
                    patch: {
                        $ref: string;
                    };
                    trace: {
                        $ref: string;
                    };
                };
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "path-item-or-reference": {
                if: {
                    type: string;
                    required: string[];
                };
                then: {
                    $ref: string;
                };
                else: {
                    $ref: string;
                };
            };
            operation: {
                $comment: string;
                type: string;
                properties: {
                    tags: {
                        type: string;
                        items: {
                            type: string;
                        };
                    };
                    summary: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                    externalDocs: {
                        $ref: string;
                    };
                    operationId: {
                        type: string;
                    };
                    parameters: {
                        type: string;
                        items: {
                            $ref: string;
                        };
                    };
                    requestBody: {
                        $ref: string;
                    };
                    responses: {
                        $ref: string;
                    };
                    callbacks: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    deprecated: {
                        default: boolean;
                        type: string;
                    };
                    security: {
                        type: string;
                        items: {
                            $ref: string;
                        };
                    };
                    servers: {
                        type: string;
                        items: {
                            $ref: string;
                        };
                    };
                };
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "external-documentation": {
                $comment: string;
                type: string;
                properties: {
                    description: {
                        type: string;
                    };
                    url: {
                        type: string;
                        format: string;
                    };
                };
                required: string[];
                $ref: string;
                unevaluatedProperties: boolean;
            };
            parameter: {
                $comment: string;
                type: string;
                properties: {
                    name: {
                        type: string;
                    };
                    in: {
                        enum: string[];
                    };
                    description: {
                        type: string;
                    };
                    required: {
                        default: boolean;
                        type: string;
                    };
                    deprecated: {
                        default: boolean;
                        type: string;
                    };
                    schema: {
                        $dynamicRef: string;
                    };
                    content: {
                        $ref: string;
                        minProperties: number;
                        maxProperties: number;
                    };
                };
                required: string[];
                oneOf: {
                    required: string[];
                }[];
                if: {
                    properties: {
                        in: {
                            const: string;
                        };
                    };
                    required: string[];
                };
                then: {
                    properties: {
                        allowEmptyValue: {
                            default: boolean;
                            type: string;
                        };
                    };
                };
                dependentSchemas: {
                    schema: {
                        properties: {
                            style: {
                                type: string;
                            };
                            explode: {
                                type: string;
                            };
                        };
                        allOf: {
                            $ref: string;
                        }[];
                        $defs: {
                            "styles-for-path": {
                                if: {
                                    properties: {
                                        in: {
                                            const: string;
                                        };
                                    };
                                    required: string[];
                                };
                                then: {
                                    properties: {
                                        style: {
                                            default: string;
                                            enum: string[];
                                        };
                                        required: {
                                            const: boolean;
                                        };
                                    };
                                    required: string[];
                                };
                            };
                            "styles-for-header": {
                                if: {
                                    properties: {
                                        in: {
                                            const: string;
                                        };
                                    };
                                    required: string[];
                                };
                                then: {
                                    properties: {
                                        style: {
                                            default: string;
                                            const: string;
                                        };
                                    };
                                };
                            };
                            "styles-for-query": {
                                if: {
                                    properties: {
                                        in: {
                                            const: string;
                                        };
                                    };
                                    required: string[];
                                };
                                then: {
                                    properties: {
                                        style: {
                                            default: string;
                                            enum: string[];
                                        };
                                        allowReserved: {
                                            default: boolean;
                                            type: string;
                                        };
                                    };
                                };
                            };
                            "styles-for-cookie": {
                                if: {
                                    properties: {
                                        in: {
                                            const: string;
                                        };
                                    };
                                    required: string[];
                                };
                                then: {
                                    properties: {
                                        style: {
                                            default: string;
                                            const: string;
                                        };
                                    };
                                };
                            };
                        };
                    };
                };
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "parameter-or-reference": {
                if: {
                    type: string;
                    required: string[];
                };
                then: {
                    $ref: string;
                };
                else: {
                    $ref: string;
                };
            };
            "request-body": {
                $comment: string;
                type: string;
                properties: {
                    description: {
                        type: string;
                    };
                    content: {
                        $ref: string;
                    };
                    required: {
                        default: boolean;
                        type: string;
                    };
                };
                required: string[];
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "request-body-or-reference": {
                if: {
                    type: string;
                    required: string[];
                };
                then: {
                    $ref: string;
                };
                else: {
                    $ref: string;
                };
            };
            content: {
                $comment: string;
                type: string;
                additionalProperties: {
                    $ref: string;
                };
                propertyNames: {
                    format: string;
                };
            };
            "media-type": {
                $comment: string;
                type: string;
                properties: {
                    schema: {
                        $dynamicRef: string;
                    };
                    encoding: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                };
                allOf: {
                    $ref: string;
                }[];
                unevaluatedProperties: boolean;
            };
            encoding: {
                $comment: string;
                type: string;
                properties: {
                    contentType: {
                        type: string;
                        format: string;
                    };
                    headers: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    style: {
                        default: string;
                        enum: string[];
                    };
                    explode: {
                        type: string;
                    };
                    allowReserved: {
                        default: boolean;
                        type: string;
                    };
                };
                allOf: {
                    $ref: string;
                }[];
                unevaluatedProperties: boolean;
            };
            responses: {
                $comment: string;
                type: string;
                properties: {
                    default: {
                        $ref: string;
                    };
                };
                patternProperties: {
                    "^[1-5](?:[0-9]{2}|XX)$": {
                        $ref: string;
                    };
                };
                minProperties: number;
                $ref: string;
                unevaluatedProperties: boolean;
                if: {
                    $comment: string;
                    patternProperties: {
                        "^[1-5](?:[0-9]{2}|XX)$": boolean;
                    };
                };
                then: {
                    required: string[];
                };
            };
            response: {
                $comment: string;
                type: string;
                properties: {
                    description: {
                        type: string;
                    };
                    headers: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                    content: {
                        $ref: string;
                    };
                    links: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                };
                required: string[];
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "response-or-reference": {
                if: {
                    type: string;
                    required: string[];
                };
                then: {
                    $ref: string;
                };
                else: {
                    $ref: string;
                };
            };
            callbacks: {
                $comment: string;
                type: string;
                $ref: string;
                additionalProperties: {
                    $ref: string;
                };
            };
            "callbacks-or-reference": {
                if: {
                    type: string;
                    required: string[];
                };
                then: {
                    $ref: string;
                };
                else: {
                    $ref: string;
                };
            };
            example: {
                $comment: string;
                type: string;
                properties: {
                    summary: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                    value: boolean;
                    externalValue: {
                        type: string;
                        format: string;
                    };
                };
                not: {
                    required: string[];
                };
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "example-or-reference": {
                if: {
                    type: string;
                    required: string[];
                };
                then: {
                    $ref: string;
                };
                else: {
                    $ref: string;
                };
            };
            link: {
                $comment: string;
                type: string;
                properties: {
                    operationRef: {
                        type: string;
                        format: string;
                    };
                    operationId: {
                        type: string;
                    };
                    parameters: {
                        $ref: string;
                    };
                    requestBody: boolean;
                    description: {
                        type: string;
                    };
                    body: {
                        $ref: string;
                    };
                };
                oneOf: {
                    required: string[];
                }[];
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "link-or-reference": {
                if: {
                    type: string;
                    required: string[];
                };
                then: {
                    $ref: string;
                };
                else: {
                    $ref: string;
                };
            };
            header: {
                $comment: string;
                type: string;
                properties: {
                    description: {
                        type: string;
                    };
                    required: {
                        default: boolean;
                        type: string;
                    };
                    deprecated: {
                        default: boolean;
                        type: string;
                    };
                    schema: {
                        type: string[];
                    };
                    content: {
                        $ref: string;
                        minProperties: number;
                        maxProperties: number;
                    };
                };
                oneOf: {
                    required: string[];
                }[];
                dependentSchemas: {
                    schema: {
                        properties: {
                            style: {
                                default: string;
                                const: string;
                            };
                            explode: {
                                default: boolean;
                                type: string;
                            };
                        };
                        $ref: string;
                    };
                };
                $ref: string;
                unevaluatedProperties: boolean;
            };
            "header-or-reference": {
                if: {
                    type: string;
                    required: string[];
                };
                then: {
                    $ref: string;
                };
                else: {
                    $ref: string;
                };
            };
            tag: {
                $comment: string;
                type: string;
                properties: {
                    name: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                    externalDocs: {
                        $ref: string;
                    };
                };
                required: string[];
                $ref: string;
                unevaluatedProperties: boolean;
            };
            reference: {
                $comment: string;
                type: string;
                properties: {
                    $ref: {
                        type: string;
                        format: string;
                    };
                    summary: {
                        type: string;
                    };
                    description: {
                        type: string;
                    };
                };
            };
            schema: {
                $comment: string;
                $dynamicAnchor: string;
                type: string[];
            };
            "security-scheme": {
                $comment: string;
                type: string;
                properties: {
                    type: {
                        enum: string[];
                    };
                    description: {
                        type: string;
                    };
                };
                required: string[];
                allOf: {
                    $ref: string;
                }[];
                unevaluatedProperties: boolean;
                $defs: {
                    "type-apikey": {
                        if: {
                            properties: {
                                type: {
                                    const: string;
                                };
                            };
                            required: string[];
                        };
                        then: {
                            properties: {
                                name: {
                                    type: string;
                                };
                                in: {
                                    enum: string[];
                                };
                            };
                            required: string[];
                        };
                    };
                    "type-http": {
                        if: {
                            properties: {
                                type: {
                                    const: string;
                                };
                            };
                            required: string[];
                        };
                        then: {
                            properties: {
                                scheme: {
                                    type: string;
                                };
                            };
                            required: string[];
                        };
                    };
                    "type-http-bearer": {
                        if: {
                            properties: {
                                type: {
                                    const: string;
                                };
                                scheme: {
                                    type: string;
                                    pattern: string;
                                };
                            };
                            required: string[];
                        };
                        then: {
                            properties: {
                                bearerFormat: {
                                    type: string;
                                };
                            };
                        };
                    };
                    "type-oauth2": {
                        if: {
                            properties: {
                                type: {
                                    const: string;
                                };
                            };
                            required: string[];
                        };
                        then: {
                            properties: {
                                flows: {
                                    $ref: string;
                                };
                            };
                            required: string[];
                        };
                    };
                    "type-oidc": {
                        if: {
                            properties: {
                                type: {
                                    const: string;
                                };
                            };
                            required: string[];
                        };
                        then: {
                            properties: {
                                openIdConnectUrl: {
                                    type: string;
                                    format: string;
                                };
                            };
                            required: string[];
                        };
                    };
                };
            };
            "security-scheme-or-reference": {
                if: {
                    type: string;
                    required: string[];
                };
                then: {
                    $ref: string;
                };
                else: {
                    $ref: string;
                };
            };
            "oauth-flows": {
                type: string;
                properties: {
                    implicit: {
                        $ref: string;
                    };
                    password: {
                        $ref: string;
                    };
                    clientCredentials: {
                        $ref: string;
                    };
                    authorizationCode: {
                        $ref: string;
                    };
                };
                $ref: string;
                unevaluatedProperties: boolean;
                $defs: {
                    implicit: {
                        type: string;
                        properties: {
                            authorizationUrl: {
                                type: string;
                                format: string;
                            };
                            refreshUrl: {
                                type: string;
                                format: string;
                            };
                            scopes: {
                                $ref: string;
                            };
                        };
                        required: string[];
                        $ref: string;
                        unevaluatedProperties: boolean;
                    };
                    password: {
                        type: string;
                        properties: {
                            tokenUrl: {
                                type: string;
                                format: string;
                            };
                            refreshUrl: {
                                type: string;
                                format: string;
                            };
                            scopes: {
                                $ref: string;
                            };
                        };
                        required: string[];
                        $ref: string;
                        unevaluatedProperties: boolean;
                    };
                    "client-credentials": {
                        type: string;
                        properties: {
                            tokenUrl: {
                                type: string;
                                format: string;
                            };
                            refreshUrl: {
                                type: string;
                                format: string;
                            };
                            scopes: {
                                $ref: string;
                            };
                        };
                        required: string[];
                        $ref: string;
                        unevaluatedProperties: boolean;
                    };
                    "authorization-code": {
                        type: string;
                        properties: {
                            authorizationUrl: {
                                type: string;
                                format: string;
                            };
                            tokenUrl: {
                                type: string;
                                format: string;
                            };
                            refreshUrl: {
                                type: string;
                                format: string;
                            };
                            scopes: {
                                $ref: string;
                            };
                        };
                        required: string[];
                        $ref: string;
                        unevaluatedProperties: boolean;
                    };
                };
            };
            "security-requirement": {
                $comment: string;
                type: string;
                additionalProperties: {
                    type: string;
                    items: {
                        type: string;
                    };
                };
            };
            "specification-extensions": {
                $comment: string;
                patternProperties: {
                    "^x-": boolean;
                };
            };
            examples: {
                properties: {
                    example: boolean;
                    examples: {
                        type: string;
                        additionalProperties: {
                            $ref: string;
                        };
                    };
                };
            };
            "map-of-strings": {
                type: string;
                additionalProperties: {
                    type: string;
                };
            };
            "styles-for-form": {
                if: {
                    properties: {
                        style: {
                            const: string;
                        };
                    };
                    required: string[];
                };
                then: {
                    properties: {
                        explode: {
                            default: boolean;
                        };
                    };
                };
                else: {
                    properties: {
                        explode: {
                            default: boolean;
                        };
                    };
                };
            };
        };
    };
};

export { openapi };
