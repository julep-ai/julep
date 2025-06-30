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
var _jsonpointer = _interopRequireDefault(require("jsonpointer"));
var _leven = _interopRequireDefault(require("leven"));
var _base = _interopRequireDefault(require("./base"));
var _templateObject, _templateObject2, _templateObject3, _templateObject4;
function ownKeys(object, enumerableOnly) { var keys = Object.keys(object); if (Object.getOwnPropertySymbols) { var symbols = Object.getOwnPropertySymbols(object); enumerableOnly && (symbols = symbols.filter(function (sym) { return Object.getOwnPropertyDescriptor(object, sym).enumerable; })), keys.push.apply(keys, symbols); } return keys; }
function _objectSpread(target) { for (var i = 1; i < arguments.length; i++) { var source = null != arguments[i] ? arguments[i] : {}; i % 2 ? ownKeys(Object(source), !0).forEach(function (key) { (0, _defineProperty2["default"])(target, key, source[key]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(target, Object.getOwnPropertyDescriptors(source)) : ownKeys(Object(source)).forEach(function (key) { Object.defineProperty(target, key, Object.getOwnPropertyDescriptor(source, key)); }); } return target; }
function _createSuper(Derived) { var hasNativeReflectConstruct = _isNativeReflectConstruct(); return function _createSuperInternal() { var Super = (0, _getPrototypeOf2["default"])(Derived), result; if (hasNativeReflectConstruct) { var NewTarget = (0, _getPrototypeOf2["default"])(this).constructor; result = Reflect.construct(Super, arguments, NewTarget); } else { result = Super.apply(this, arguments); } return (0, _possibleConstructorReturn2["default"])(this, result); }; }
function _isNativeReflectConstruct() { if (typeof Reflect === "undefined" || !Reflect.construct) return false; if (Reflect.construct.sham) return false; if (typeof Proxy === "function") return true; try { Boolean.prototype.valueOf.call(Reflect.construct(Boolean, [], function () {})); return true; } catch (e) { return false; } }
var EnumValidationError = /*#__PURE__*/function (_BaseValidationError) {
  (0, _inherits2["default"])(EnumValidationError, _BaseValidationError);
  var _super = _createSuper(EnumValidationError);
  function EnumValidationError() {
    var _this;
    (0, _classCallCheck2["default"])(this, EnumValidationError);
    for (var _len = arguments.length, args = new Array(_len), _key = 0; _key < _len; _key++) {
      args[_key] = arguments[_key];
    }
    _this = _super.call.apply(_super, [this].concat(args));
    _this.name = 'EnumValidationError';
    return _this;
  }
  (0, _createClass2["default"])(EnumValidationError, [{
    key: "print",
    value: function print() {
      var _this$options = this.options,
        message = _this$options.message,
        allowedValues = _this$options.params.allowedValues;
      var chalk = this.getChalk();
      var bestMatch = this.findBestMatch();
      var output = [chalk(_templateObject || (_templateObject = (0, _taggedTemplateLiteral2["default"])(["{red {bold ENUM} ", "}"])), message), chalk(_templateObject2 || (_templateObject2 = (0, _taggedTemplateLiteral2["default"])(["{red (", ")}\n"], ["{red (", ")}\\n"])), allowedValues.join(', '))];
      return output.concat(this.getCodeFrame(bestMatch !== null ? chalk(_templateObject3 || (_templateObject3 = (0, _taggedTemplateLiteral2["default"])(["\uD83D\uDC48\uD83C\uDFFD  Did you mean {magentaBright ", "} here?"])), bestMatch) : chalk(_templateObject4 || (_templateObject4 = (0, _taggedTemplateLiteral2["default"])(["\uD83D\uDC48\uD83C\uDFFD  Unexpected value, should be equal to one of the allowed values"])))));
    }
  }, {
    key: "getError",
    value: function getError() {
      var _this$options2 = this.options,
        message = _this$options2.message,
        params = _this$options2.params;
      var bestMatch = this.findBestMatch();
      var allowedValues = params.allowedValues.join(', ');
      var output = _objectSpread(_objectSpread({}, this.getLocation()), {}, {
        error: "".concat(this.getDecoratedPath(), " ").concat(message, ": ").concat(allowedValues),
        path: this.instancePath
      });
      if (bestMatch !== null) {
        output.suggestion = "Did you mean ".concat(bestMatch, "?");
      }
      return output;
    }
  }, {
    key: "findBestMatch",
    value: function findBestMatch() {
      var allowedValues = this.options.params.allowedValues;
      var currentValue = this.instancePath === '' ? this.data : _jsonpointer["default"].get(this.data, this.instancePath);
      if (!currentValue) {
        return null;
      }
      var bestMatch = allowedValues.map(function (value) {
        return {
          value: value,
          weight: (0, _leven["default"])(value, currentValue.toString())
        };
      }).sort(function (x, y) {
        return x.weight > y.weight ? 1 : x.weight < y.weight ? -1 : 0;
      })[0];
      return allowedValues.length === 1 || bestMatch.weight < bestMatch.value.length ? bestMatch.value : null;
    }
  }]);
  return EnumValidationError;
}(_base["default"]);
exports["default"] = EnumValidationError;
module.exports = exports.default;