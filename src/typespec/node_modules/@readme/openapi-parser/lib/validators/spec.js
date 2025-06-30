const validateOpenAPI = require('./spec/openapi');
const validateSwagger = require('./spec/swagger');

/**
 * Validates either a Swagger 2.0 or OpenAPI 3.x API definition against cases that aren't covered by their JSON Schema
 * definitions.
 *
 * @param {SwaggerObject} api
 */
module.exports = function validateSpec(api) {
  if (api.openapi) {
    return validateOpenAPI(api);
  }

  return validateSwagger(api);
};
