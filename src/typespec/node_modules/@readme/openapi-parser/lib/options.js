const $RefParserOptions = require('@readme/json-schema-ref-parser/lib/options');

const util = require('./util');
const schemaValidator = require('./validators/schema');
const specValidator = require('./validators/spec');

module.exports = ParserOptions;

/**
 * Options that determine how Swagger APIs are parsed, resolved, dereferenced, and validated.
 *
 * @param {object|ParserOptions} [_options] - Overridden options
 * @class
 * @augments $RefParserOptions
 */
// eslint-disable-next-line no-unused-vars
function ParserOptions(_options) {
  $RefParserOptions.call(this, ParserOptions.defaults);
  $RefParserOptions.apply(this, arguments);
}

ParserOptions.defaults = {
  /**
   * Determines how the API definition will be validated.
   *
   * You can add additional validators of your own, replace an existing one with
   * your own implemenation, or disable any validator by setting it to false.
   */
  validate: {
    colorizeErrors: false,
    schema: schemaValidator,
    spec: specValidator,
  },
};

util.inherits(ParserOptions, $RefParserOptions);
