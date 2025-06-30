"use strict";

var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");
Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;
var _classCallCheck2 = _interopRequireDefault(require("@babel/runtime/helpers/classCallCheck"));
var _createClass2 = _interopRequireDefault(require("@babel/runtime/helpers/createClass"));
var _codeFrame = require("@babel/code-frame");
var _chalk = _interopRequireDefault(require("chalk"));
var _json = require("../json");
var BaseValidationError = /*#__PURE__*/function () {
  // eslint-disable-next-line default-param-last
  function BaseValidationError() {
    var options = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {
      isIdentifierLocation: false
    };
    var _ref = arguments.length > 1 ? arguments[1] : undefined,
      colorize = _ref.colorize,
      data = _ref.data,
      schema = _ref.schema,
      jsonAst = _ref.jsonAst,
      jsonRaw = _ref.jsonRaw;
    (0, _classCallCheck2["default"])(this, BaseValidationError);
    this.options = options;
    this.colorize = !!(!!colorize || colorize === undefined);
    this.data = data;
    this.schema = schema;
    this.jsonAst = jsonAst;
    this.jsonRaw = jsonRaw;
  }
  (0, _createClass2["default"])(BaseValidationError, [{
    key: "getChalk",
    value: function getChalk() {
      return this.colorize ? _chalk["default"] : new _chalk["default"].Instance({
        level: 0
      });
    }
  }, {
    key: "getLocation",
    value: function getLocation() {
      var dataPath = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : this.instancePath;
      var _this$options = this.options,
        isIdentifierLocation = _this$options.isIdentifierLocation,
        isSkipEndLocation = _this$options.isSkipEndLocation;
      var _getMetaFromPath = (0, _json.getMetaFromPath)(this.jsonAst, dataPath, isIdentifierLocation),
        loc = _getMetaFromPath.loc;
      return {
        start: loc.start,
        end: isSkipEndLocation ? undefined : loc.end
      };
    }
  }, {
    key: "getDecoratedPath",
    value: function getDecoratedPath() {
      var dataPath = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : this.instancePath;
      return (0, _json.getDecoratedDataPath)(this.jsonAst, dataPath);
    }
  }, {
    key: "getCodeFrame",
    value: function getCodeFrame(message) {
      var dataPath = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : this.instancePath;
      return (0, _codeFrame.codeFrameColumns)(this.jsonRaw, this.getLocation(dataPath), {
        /**
         * `@babel/highlight`, by way of `@babel/code-frame`, highlights out entire block of raw JSON
         * instead of just our `location` block -- so if you have a block of raw JSON that's upwards
         * of 2mb+ and have a lot of errors to generate code frames for then we're re-highlighting
         * the same huge chunk of code over and over and over and over again, all just so
         * `@babel/code-frame` will eventually extract a small <10 line chunk out of it to return to
         * us.
         *
         * Disabling `highlightCode` here will only disable highlighting the code we're showing users;
         * if `options.colorize` is supplied to this library then the error message we're adding will
         * still be highlighted.
         */
        highlightCode: false,
        message: message
      });
    }

    /**
     * @return {string}
     */
  }, {
    key: "instancePath",
    get: function get() {
      return typeof this.options.instancePath !== 'undefined' ? this.options.instancePath : this.options.dataPath;
    }
  }, {
    key: "print",
    value: function print() {
      throw new Error("Implement the 'print' method inside ".concat(this.constructor.name, "!"));
    }
  }, {
    key: "getError",
    value: function getError() {
      throw new Error("Implement the 'getError' method inside ".concat(this.constructor.name, "!"));
    }
  }]);
  return BaseValidationError;
}();
exports["default"] = BaseValidationError;
module.exports = exports.default;