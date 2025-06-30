"use strict";

var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");
Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = betterAjvErrors;
var _momoa = require("@humanwhocodes/momoa");
var _helpers = _interopRequireDefault(require("./helpers"));
function betterAjvErrors(schema, data, errors) {
  var options = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : {};
  var _options$colorize = options.colorize,
    colorize = _options$colorize === void 0 ? true : _options$colorize,
    _options$format = options.format,
    format = _options$format === void 0 ? 'cli' : _options$format,
    _options$indent = options.indent,
    indent = _options$indent === void 0 ? null : _options$indent,
    _options$json = options.json,
    json = _options$json === void 0 ? null : _options$json;
  var jsonRaw = json || JSON.stringify(data, null, indent);
  var jsonAst = (0, _momoa.parse)(jsonRaw);
  var customErrorToText = function customErrorToText(error) {
    return error.print().join('\n');
  };
  var customErrorToStructure = function customErrorToStructure(error) {
    return error.getError();
  };
  var customErrors = (0, _helpers["default"])(errors, {
    colorize: colorize,
    data: data,
    schema: schema,
    jsonAst: jsonAst,
    jsonRaw: jsonRaw
  });
  if (format === 'cli') {
    return customErrors.map(customErrorToText).join('\n\n');
  }
  return customErrors.map(customErrorToStructure);
}
module.exports = exports.default;