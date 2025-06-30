// eslint-disable-next-line unicorn/import-style
const util = require('util');

const url = require('@readme/json-schema-ref-parser/lib/util/url');

exports.format = util.format;
exports.inherits = util.inherits;

/**
 * Regular Expression that matches Swagger path params.
 */
exports.swaggerParamRegExp = /\{([^/}]+)}/g;

/**
 * List of HTTP verbs used for OperationItem as per the Swagger specification
 */
const operationsList = ['get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace'];

/**
 * This function takes in a Server object, checks if it has relative path
 * and then fixes it as per the path url
 *
 * @param {object} server - The server object to be fixed
 * @param {string} path - The path (an http/https url) from where the file was downloaded
 * @returns {object} - The fixed server object
 */
function fixServers(server, path) {
  // Server url starting with "/" tells that it is not an http(s) url
  if (server.url && server.url.startsWith('/')) {
    const inUrl = url.parse(path);
    const finalUrl = `${inUrl.protocol}//${inUrl.hostname}${server.url}`;
    server.url = finalUrl; // eslint-disable-line no-param-reassign
  }

  return server;
}

/**
 * This function helps fix the relative servers in the API definition file
 * be at root, path or operation's level
 */
function fixOasRelativeServers(schema, filePath) {
  if (schema.openapi && filePath && (filePath.startsWith('http:') || filePath.startsWith('https:'))) {
    /**
     * From OpenAPI v3 spec for Server object's url property: "REQUIRED. A URL to the target host.
     * This URL supports Server Variables and MAY be relative, to indicate that the host location is relative to the location where
     * the OpenAPI document is being served."
     * Further, the spec says that "servers" property can show up at root level, in 'Path Item' object or in 'Operation' object.
     * However, interpretation of the spec says that relative paths for servers should take into account the hostname that
     * serves the OpenAPI file.
     */
    if (schema.servers) {
      schema.servers.map(server => fixServers(server, filePath)); // Root level servers array's fixup
    }

    // Path, Operation, or Webhook level servers array's fixup
    ['paths', 'webhooks'].forEach(component => {
      Object.keys(schema[component] || []).forEach(path => {
        const pathItem = schema[component][path];
        Object.keys(pathItem).forEach(opItem => {
          if (opItem === 'servers') {
            // servers at pathitem level
            pathItem[opItem].map(server => fixServers(server, filePath));
          } else if (operationsList.includes(opItem)) {
            // servers at operation level
            if (pathItem[opItem].servers) {
              pathItem[opItem].servers.map(server => fixServers(server, filePath));
            }
          }
        });
      });
    });
  } else {
    // Do nothing and return
  }
}

/**
 * Determine the proper name for the API specification schema used by a given schema.
 *
 * @param {object} schema
 * @returns {string} - The name of the specification that this schema utilizes.
 */
function getSpecificationName(schema) {
  return schema.swagger ? 'Swagger' : 'OpenAPI';
}

exports.fixOasRelativeServers = fixOasRelativeServers;
exports.getSpecificationName = getSpecificationName;
