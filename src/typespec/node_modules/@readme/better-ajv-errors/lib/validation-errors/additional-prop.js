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
var _inherits2 = _interopRequireDefault(require("@babel/runtime/helpers/inherits"));
var _possibleConstructorReturn2 = _interopRequireDefault(require("@babel/runtime/helpers/possibleConstructorReturn"));
var _getPrototypeOf2 = _interopRequireDefault(require("@babel/runtime/helpers/getPrototypeOf"));
var _base = _interopRequireDefault(require("./base"));
var _templateObject, _templateObject2;
function ownKeys(object, enumerableOnly) { var keys = Object.keys(object); if (Object.getOwnPropertySymbols) { var symbols = Object.getOwnPropertySymbols(object); enumerableOnly && (symbols = symbols.filter(function (sym) { return Object.getOwnPropertyDescriptor(object, sym).enumerable; })), keys.push.apply(keys, symbols); } return keys; }
function _objectSpread(target) { for (var i = 1; i < arguments.length; i++) { var source = null != arguments[i] ? arguments[i] : {}; i % 2 ? ownKeys(Object(source), !0).forEach(function (key) { (0, _defineProperty2["default"])(target, key, source[key]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(target, Object.getOwnPropertyDescriptors(source)) : ownKeys(Object(source)).forEach(function (key) { Object.defineProperty(target, key, Object.getOwnPropertyDescriptor(source, key)); }); } return target; }
function _createSuper(Derived) { var hasNativeReflectConstruct = _isNativeReflectConstruct(); return function _createSuperInternal() { var Super = (0, _getPrototypeOf2["default"])(Derived), result; if (hasNativeReflectConstruct) { var NewTarget = (0, _getPrototypeOf2["default"])(this).constructor; result = Reflect.construct(Super, arguments, NewTarget); } else { result = Super.apply(this, arguments); } return (0, _possibleConstructorReturn2["default"])(this, result); }; }
function _isNativeReflectConstruct() { if (typeof Reflect === "undefined" || !Reflect.construct) return false; if (Reflect.construct.sham) return false; if (typeof Proxy === "function") return true; try { Boolean.prototype.valueOf.call(Reflect.construct(Boolean, [], function () {})); return true; } catch (e) { return false; } }
var AdditionalPropValidationError = /*#__PURE__*/function (_BaseValidationError) {
  (0, _inherits2["default"])(AdditionalPropValidationError, _BaseValidationError);
  var _super = _createSuper(AdditionalPropValidationError);
  function AdditionalPropValidationError() {
    var _this;
    (0, _classCallCheck2["default"])(this, AdditionalPropValidationError);
    for (var _len = arguments.length, args = new Array(_len), _key = 0; _key < _len; _key++) {
      args[_key] = arguments[_key];
    }
    _this = _super.call.apply(_super, [this].concat(args));
    _this.name = 'AdditionalPropValidationError';
    _this.options.isIdentifierLocation = true;
    return _this;
  }
  (0, _createClass2["default"])(AdditionalPropValidationError, [{
    key: "print",
    value: function print() {
      var _this$options = this.options,
        message = _this$options.message,
        params = _this$options.params;
      var chalk = this.getChalk();
      var output = [chalk(_templateObject || (_templateObject = (0, _taggedTemplateLiteral2["default"])(["{red {bold ADDITIONAL PROPERTY} ", "}\n"], ["{red {bold ADDITIONAL PROPERTY} ", "}\\n"])), message)];
      return output.concat(this.getCodeFrame(chalk(_templateObject2 || (_templateObject2 = (0, _taggedTemplateLiteral2["default"])(["\uD83D\uDE32  {magentaBright ", "} is not expected to be here!"])), params.additionalProperty), "".concat(this.instancePath, "/").concat(params.additionalProperty)));
    }
  }, {
    key: "getError",
    value: function getError() {
      var params = this.options.params;
      return _objectSpread(_objectSpread({}, this.getLocation("".concat(this.instancePath, "/").concat(params.additionalProperty))), {}, {
        error: "".concat(this.getDecoratedPath(), " Property ").concat(params.additionalProperty, " is not expected to be here"),
        path: this.instancePath
      });
    }
  }]);
  return AdditionalPropValidationError;
}(_base["default"]);
exports["default"] = AdditionalPropValidationError;
module.exports = exports.default;