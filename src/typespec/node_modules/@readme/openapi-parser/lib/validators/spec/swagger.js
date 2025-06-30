const swaggerMethods = require('@apidevtools/swagger-methods');
const { ono } = require('@jsdevtools/ono');

const util = require('../../util');

const primitiveTypes = ['array', 'boolean', 'integer', 'number', 'string'];
const schemaTypes = ['array', 'boolean', 'integer', 'number', 'string', 'object', 'null', undefined];

module.exports = validateSpec;

/**
 * Validates parts of the Swagger 2.0 spec that aren't covered by the Swagger 2.0 JSON Schema.
 *
 * @param {SwaggerObject} api
 */
function validateSpec(api) {
  const operationIds = [];
  Object.keys(api.paths || {}).forEach(pathName => {
    const path = api.paths[pathName];
    const pathId = `/paths${pathName}`;

    if (path && pathName.indexOf('/') === 0) {
      validatePath(api, path, pathId, operationIds);
    }
  });

  Object.keys(api.definitions || {}).forEach(definitionName => {
    const definition = api.definitions[definitionName];
    const definitionId = `/definitions/${definitionName}`;

    if (!/^[a-zA-Z0-9.\-_]+$/.test(definitionName)) {
      throw ono.syntax(
        `Validation failed. ${definitionId} has an invalid name. Definition names should match against: /^[a-zA-Z0-9.-_]+$/`,
      );
    }

    validateRequiredPropertiesExist(definition, definitionId);
  });
}

/**
 * Validates the given path.
 *
 * @param {SwaggerObject} api           - The entire Swagger API object
 * @param {object}        path          - A Path object, from the Swagger API
 * @param {string}        pathId        - A value that uniquely identifies the path
 * @param {string}        operationIds  - An array of collected operationIds found in other paths
 */
function validatePath(api, path, pathId, operationIds) {
  swaggerMethods.forEach(operationName => {
    const operation = path[operationName];
    const operationId = `${pathId}/${operationName}`;

    if (operation) {
      const declaredOperationId = operation.operationId;
      if (declaredOperationId) {
        if (operationIds.indexOf(declaredOperationId) === -1) {
          operationIds.push(declaredOperationId);
        } else {
          throw ono.syntax(`Validation failed. Duplicate operation id '${declaredOperationId}'`);
        }
      }
      validateParameters(api, path, pathId, operation, operationId);

      Object.keys(operation.responses || {}).forEach(responseName => {
        const response = operation.responses[responseName];
        const responseId = `${operationId}/responses/${responseName}`;
        validateResponse(responseName, response || {}, responseId);
      });
    }
  });
}

/**
 * Validates the parameters for the given operation.
 *
 * @param {SwaggerObject} api           - The entire Swagger API object
 * @param {object}        path          - A Path object, from the Swagger API
 * @param {string}        pathId        - A value that uniquely identifies the path
 * @param {object}        operation     - An Operation object, from the Swagger API
 * @param {string}        operationId   - A value that uniquely identifies the operation
 */
function validateParameters(api, path, pathId, operation, operationId) {
  const pathParams = path.parameters || [];
  const operationParams = operation.parameters || [];

  // Check for duplicate path parameters
  try {
    checkForDuplicates(pathParams);
  } catch (e) {
    throw ono.syntax(e, `Validation failed. ${pathId} has duplicate parameters`);
  }

  // Check for duplicate operation parameters
  try {
    checkForDuplicates(operationParams);
  } catch (e) {
    throw ono.syntax(e, `Validation failed. ${operationId} has duplicate parameters`);
  }

  // Combine the path and operation parameters,
  // with the operation params taking precedence over the path params
  const params = pathParams.reduce((combinedParams, value) => {
    const duplicate = combinedParams.some(param => {
      return param.in === value.in && param.name === value.name;
    });
    if (!duplicate) {
      combinedParams.push(value);
    }
    return combinedParams;
  }, operationParams.slice());

  validateBodyParameters(params, operationId);
  validatePathParameters(params, pathId, operationId);
  validateParameterTypes(params, api, operation, operationId);
}

/**
 * Validates body and formData parameters for the given operation.
 *
 * @param   {object[]}  params       -  An array of Parameter objects
 * @param   {string}    operationId  -  A value that uniquely identifies the operation
 */
function validateBodyParameters(params, operationId) {
  const bodyParams = params.filter(param => {
    return param.in === 'body';
  });
  const formParams = params.filter(param => {
    return param.in === 'formData';
  });

  // There can only be one "body" parameter
  if (bodyParams.length > 1) {
    throw ono.syntax(
      `Validation failed. ${operationId} has ${bodyParams.length} body parameters. Only one is allowed.`,
    );
  } else if (bodyParams.length > 0 && formParams.length > 0) {
    // "body" params and "formData" params are mutually exclusive
    throw ono.syntax(
      `Validation failed. ${operationId} has body parameters and formData parameters. Only one or the other is allowed.`,
    );
  }
}

/**
 * Validates path parameters for the given path.
 *
 * @param   {object[]}  params        - An array of Parameter objects
 * @param   {string}    pathId        - A value that uniquely identifies the path
 * @param   {string}    operationId   - A value that uniquely identifies the operation
 */
function validatePathParameters(params, pathId, operationId) {
  // Find all {placeholders} in the path string
  const placeholders = pathId.match(util.swaggerParamRegExp) || [];

  // Check for duplicates
  for (let i = 0; i < placeholders.length; i++) {
    for (let j = i + 1; j < placeholders.length; j++) {
      if (placeholders[i] === placeholders[j]) {
        throw ono.syntax(`Validation failed. ${operationId} has multiple path placeholders named ${placeholders[i]}`);
      }
    }
  }

  params
    .filter(param => param.in === 'path')
    .forEach(param => {
      if (param.required !== true) {
        throw ono.syntax(
          'Validation failed. Path parameters cannot be optional. ' +
            `Set required=true for the "${param.name}" parameter at ${operationId}`,
        );
      }

      const match = placeholders.indexOf(`{${param.name}}`);
      if (match === -1) {
        throw ono.syntax(
          `Validation failed. ${operationId} has a path parameter named "${param.name}", ` +
            `but there is no corresponding {${param.name}} in the path string`,
        );
      }

      placeholders.splice(match, 1);
    });

  if (placeholders.length > 0) {
    throw ono.syntax(`Validation failed. ${operationId} is missing path parameter(s) for ${placeholders}`);
  }
}

/**
 * Validates data types of parameters for the given operation.
 *
 * @param   {object[]}  params       -  An array of Parameter objects
 * @param   {object}    api          -  The entire Swagger API object
 * @param   {object}    operation    -  An Operation object, from the Swagger API
 * @param   {string}    operationId  -  A value that uniquely identifies the operation
 */
function validateParameterTypes(params, api, operation, operationId) {
  params.forEach(param => {
    const parameterId = `${operationId}/parameters/${param.name}`;
    let schema;
    let validTypes;

    switch (param.in) {
      case 'body':
        schema = param.schema;
        validTypes = schemaTypes;
        break;
      case 'formData':
        schema = param;
        validTypes = primitiveTypes.concat('file');
        break;
      default:
        schema = param;
        validTypes = primitiveTypes;
    }

    validateSchema(schema, parameterId, validTypes);
    validateRequiredPropertiesExist(schema, parameterId);

    if (schema.type === 'file') {
      // "file" params must consume at least one of these MIME types
      const formData = /multipart\/(.*\+)?form-data/;
      const urlEncoded = /application\/(.*\+)?x-www-form-urlencoded/;

      const consumes = operation.consumes || api.consumes || [];

      const hasValidMimeType = consumes.some(consume => {
        return formData.test(consume) || urlEncoded.test(consume);
      });

      if (!hasValidMimeType) {
        throw ono.syntax(
          `Validation failed. ${operationId} has a file parameter, so it must consume multipart/form-data ` +
            'or application/x-www-form-urlencoded',
        );
      }
    }
  });
}

/**
 * Checks the given parameter list for duplicates, and throws an error if found.
 *
 * @param   {object[]}  params  - An array of Parameter objects
 */
function checkForDuplicates(params) {
  for (let i = 0; i < params.length - 1; i++) {
    const outer = params[i];
    for (let j = i + 1; j < params.length; j++) {
      const inner = params[j];
      if (outer.name === inner.name && outer.in === inner.in) {
        throw ono.syntax(`Validation failed. Found multiple ${outer.in} parameters named "${outer.name}"`);
      }
    }
  }
}

/**
 * Validates the given response object.
 *
 * @param   {string}    code        -  The HTTP response code (or "default")
 * @param   {object}    response    -  A Response object, from the Swagger API
 * @param   {string}    responseId  -  A value that uniquely identifies the response
 */
function validateResponse(code, response, responseId) {
  if (code !== 'default' && (code < 100 || code > 599)) {
    throw ono.syntax(`Validation failed. ${responseId} has an invalid response code (${code})`);
  }

  Object.keys(response.headers || {}).forEach(headerName => {
    const header = response.headers[headerName];
    const headerId = `${responseId}/headers/${headerName}`;
    validateSchema(header, headerId, primitiveTypes);
  });

  if (response.schema) {
    const validTypes = schemaTypes.concat('file');
    if (validTypes.indexOf(response.schema.type) === -1) {
      throw ono.syntax(
        `Validation failed. ${responseId} has an invalid response schema type (${response.schema.type})`,
      );
    } else {
      validateSchema(response.schema, `${responseId}/schema`, validTypes);
    }
  }
}

/**
 * Validates the given Swagger schema object.
 *
 * @param {object}    schema      - A Schema object, from the Swagger API
 * @param {string}    schemaId    - A value that uniquely identifies the schema object
 * @param {string[]}  validTypes  - An array of the allowed schema types
 */
function validateSchema(schema, schemaId, validTypes) {
  if (validTypes.indexOf(schema.type) === -1) {
    throw ono.syntax(`Validation failed. ${schemaId} has an invalid type (${schema.type})`);
  }

  if (schema.type === 'array' && !schema.items) {
    throw ono.syntax(`Validation failed. ${schemaId} is an array, so it must include an "items" schema`);
  }
}

/**
 * Validates that the declared properties of the given Swagger schema object actually exist.
 *
 * @param {object}    schema      - A Schema object, from the Swagger API
 * @param {string}    schemaId    - A value that uniquely identifies the schema object
 */
function validateRequiredPropertiesExist(schema, schemaId) {
  // Recursively collects all properties of the schema and its ancestors. They are added to the props object.
  function collectProperties(schemaObj, props) {
    if (schemaObj.properties) {
      Object.keys(schemaObj.properties).forEach(property => {
        // eslint-disable-next-line no-prototype-builtins
        if (schemaObj.properties.hasOwnProperty(property)) {
          // eslint-disable-next-line no-param-reassign
          props[property] = schemaObj.properties[property];
        }
      });
    }

    if (schemaObj.allOf) {
      schemaObj.allOf.forEach(parent => {
        collectProperties(parent, props);
      });
    }
  }

  if (schema.required && Array.isArray(schema.required)) {
    const props = {};
    collectProperties(schema, props);
    schema.required.forEach(requiredProperty => {
      if (!props[requiredProperty]) {
        throw ono.syntax(
          `Validation failed. Property '${requiredProperty}' listed as required but does not exist in '${schemaId}'`,
        );
      }
    });
  }
}
