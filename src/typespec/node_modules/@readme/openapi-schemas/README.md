# @readme/openapi-schemas

[![Build](https://github.com/readmeio/openapi-schemas/workflows/CI/badge.svg)](https://github.com/readmeio/openapi-schemas/) [![](https://img.shields.io/npm/v/@readme/openapi-schemas)](https://npm.im/@readme/openapi-schemas)

[![](https://raw.githubusercontent.com/readmeio/.github/main/oss-header.png)](https://readme.io)

This package contains [**the official JSON Schemas**](https://github.com/OAI/OpenAPI-Specification/tree/main/schemas) for every version of Swagger/OpenAPI Specification:

<!-- prettier-ignore-start -->
| Version | Schema | Docs |
| :--- | :--- | :--- |
| Swagger 1.2 | [v1.2 schema](https://github.com/OAI/OpenAPI-Specification/tree/main/schemas/v1.2) | [v1.2 docs](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/1.2.md) |
| Swagger 2.0 | [v2.0 schema](https://github.com/OAI/OpenAPI-Specification/blob/main/schemas/v2.0/schema.json) | [v2.0 docs](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/2.0.md) |
| OpenAPI 3.0.x | [v3.0.x schema](https://github.com/OAI/OpenAPI-Specification/blob/main/schemas/v3.0/schema.json) | [v3.0.3 docs](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md) |
| OpenAPI 3.1.x | [v3.1.x schema](https://github.com/OAI/OpenAPI-Specification/blob/main/schemas/v3.1/schema.json) | [v3.1.0 docs](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md) |
<!-- prettier-ignore-end -->

## Installation

You can install OpenAPI Schemas via [npm](https://docs.npmjs.com/about-npm/).

```bash
npm install @readme/openapi-schemas
```

## Usage

The library contains all OpenAPI Specification versions:

```js
import { openapi } from '@readme/openapi-schemas';

console.log(openapi.v1); // { $schema, id, properties, definitions, ... }
console.log(openapi.v2); // { $schema, id, properties, definitions, ... }
console.log(openapi.v3); // { $schema, id, properties, definitions, ... }
console.log(openapi.v31); // { $schema, id, properties, definitions, ... }
```

You can use a JSON Schema validator such as [Z-Schema](https://npm.im/z-schema) or [AJV](https://npm.im/ajv) to validate OpenAPI definitions against the specification.

```js
import { openapi } from '@readme/openapi-schemas';
import ZSchema from 'z-schema';

// Create a ZSchema validator
let validator = new ZSchema();

// Validate an OpenAPI definition against the OpenAPI v3.0 specification
validator.validate(openapiDefinition, openapi.v31);
```
