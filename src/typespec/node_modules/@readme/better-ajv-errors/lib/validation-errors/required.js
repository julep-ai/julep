"use strict";

var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");
Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;
var _defineProperty2 = _interopRequireDefault(require("@babel/runtime/helpers/defineProperty"));
var _taggedTemplateLiteral2 = _interopRequireDefault(require("@babel/runtime/helpers/taggedTemplateLiteral"));
var _classCallCheck2 = _interopRequireDefault(require("@babel/runtime/helpers/classCallCheck"));
var _createClass2 = _interopRequireDefault(require("@babel/runtime/helpers/createClass"));
var _get2 = _interopRequireDefault(require("@babel/runtime/helpers/get"));
var _inherits2 = _interopRequireDefault(require("@babel/runtime/helpers/inherits"));
var _possibleConstructorReturn2 = _interopRequireDefault(require("@babel/runtime/helpers/possibleConstructorReturn"));
var _getPrototypeOf2 = _interopRequireDefault(require("@babel/runtime/helpers/getPrototypeOf"));
var _base = _interopRequireDefault(require("./base"));
var _templateObject, _templateObject2;
function ownKeys(object, enumerableOnly) { var keys = Object.keys(object); if (Object.getOwnPropertySymbols) { var symbols = Object.getOwnPropertySymbols(object); enumerableOnly && (symbols = symbols.filter(function (sym) { return Object.getOwnPropertyDescriptor(object, sym).enumerable; })), keys.push.apply(keys, symbols); } return keys; }
function _objectSpread(target) { for (var i = 1; i < arguments.length; i++) { var source = null != arguments[i] ? arguments[i] : {}; i % 2 ? ownKeys(Object(source), !0).forEach(function (key) { (0, _defineProperty2["default"])(target, key, source[key]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(target, Object.getOwnPropertyDescriptors(source)) : ownKeys(Object(source)).forEach(function (key) { Object.defineProperty(target, key, Object.getOwnPropertyDescriptor(source, key)); }); } return target; }
function _createSuper(Derived) { var hasNativeReflectConstruct = _isNativeReflectConstruct(); return function _createSuperInternal() { var Super = (0, _getPrototypeOf2["default"])(Derived), result; if (hasNativeReflectConstruct) { var NewTarget = (0, _getPrototypeOf2["default"])(this).constructor; result = Reflect.construct(Super, arguments, NewTarget); } else { result = Super.apply(this, arguments); } return (0, _possibleConstructorReturn2["default"])(this, result); }; }
function _isNativeReflectConstruct() { if (typeof Reflect === "undefined" || !Reflect.construct) return false; if (Reflect.construct.sham) return false; if (typeof Proxy === "function") return true; try { Boolean.prototype.valueOf.call(Reflect.construct(Boolean, [], function () {})); return true; } catch (e) { return false; } }
var RequiredValidationError = /*#__PURE__*/function (_BaseValidationError) {
  (0, _inherits2["default"])(RequiredValidationError, _BaseValidationError);
  var _super = _createSuper(RequiredValidationError);
  function RequiredValidationError() {
    var _this;
    (0, _classCallCheck2["default"])(this, RequiredValidationError);
    for (var _len = arguments.length, args = new Array(_len), _key = 0; _key < _len; _key++) {
      args[_key] = arguments[_key];
    }
    _this = _super.call.apply(_super, [this].concat(args));
    _this.name = 'RequiredValidationError';
    return _this;
  }
  (0, _createClass2["default"])(RequiredValidationError, [{
    key: "getLocation",
    value: function getLocation() {
      var dataPath = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : this.instancePath;
      var _get$call = (0, _get2["default"])((0, _getPrototypeOf2["default"])(RequiredValidationError.prototype), "getLocation", this).call(this, dataPath),
        start = _get$call.start;
      return {
        start: start
      };
    }
  }, {
    key: "print",
    value: function print() {
      var _this$options = this.options,
        message = _this$options.message,
        params = _this$options.params;
      var chalk = this.getChalk();
      var output = [chalk(_templateObject || (_templateObject = (0, _taggedTemplateLiteral2["default"])(["{red {bold REQUIRED} ", "}\n"], ["{red {bold REQUIRED} ", "}\\n"])), message)];
      return output.concat(this.getCodeFrame(chalk(_templateObject2 || (_templateObject2 = (0, _taggedTemplateLiteral2["default"])(["\u2639\uFE0F  {magentaBright ", "} is missing here!"])), params.missingProperty)));
    }
  }, {
    key: "getError",
    value: function getError() {
      var message = this.options.message;
      return _objectSpread(_objectSpread({}, this.getLocation()), {}, {
        error: "".concat(this.getDecoratedPath(), " ").concat(message),
        path: this.instancePath
      });
    }
  }]);
  return RequiredValidationError;
}(_base["default"]);
exports["default"] = RequiredValidationError;
module.exports = exports.default;