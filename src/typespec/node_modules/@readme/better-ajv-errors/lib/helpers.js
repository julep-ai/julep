"use strict";

var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");
Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.createErrorInstances = createErrorInstances;
exports["default"] = prettify;
exports.filterRedundantErrors = filterRedundantErrors;
exports.makeTree = makeTree;
var _defineProperty2 = _interopRequireDefault(require("@babel/runtime/helpers/defineProperty"));
var _toConsumableArray2 = _interopRequireDefault(require("@babel/runtime/helpers/toConsumableArray"));
var _slicedToArray2 = _interopRequireDefault(require("@babel/runtime/helpers/slicedToArray"));
var _utils = require("./utils");
var _validationErrors = require("./validation-errors");
function ownKeys(object, enumerableOnly) { var keys = Object.keys(object); if (Object.getOwnPropertySymbols) { var symbols = Object.getOwnPropertySymbols(object); enumerableOnly && (symbols = symbols.filter(function (sym) { return Object.getOwnPropertyDescriptor(object, sym).enumerable; })), keys.push.apply(keys, symbols); } return keys; }
function _objectSpread(target) { for (var i = 1; i < arguments.length; i++) { var source = null != arguments[i] ? arguments[i] : {}; i % 2 ? ownKeys(Object(source), !0).forEach(function (key) { (0, _defineProperty2["default"])(target, key, source[key]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(target, Object.getOwnPropertyDescriptors(source)) : ownKeys(Object(source)).forEach(function (key) { Object.defineProperty(target, key, Object.getOwnPropertyDescriptor(source, key)); }); } return target; }
// eslint-disable-next-line unicorn/no-unsafe-regex
var JSON_POINTERS_REGEX = /\/[\w_-]+(\/\d+)?/g;

// Make a tree of errors from ajv errors array
function makeTree() {
  var ajvErrors = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : [];
  var root = {
    children: {}
  };
  ajvErrors.forEach(function (ajvError) {
    var instancePath = typeof ajvError.instancePath !== 'undefined' ? ajvError.instancePath : ajvError.dataPath;

    // `dataPath === ''` is root
    var paths = instancePath === '' ? [''] : instancePath.match(JSON_POINTERS_REGEX);
    if (paths) {
      paths.reduce(function (obj, path, i) {
        obj.children[path] = obj.children[path] || {
          children: {},
          errors: []
        };
        if (i === paths.length - 1) {
          obj.children[path].errors.push(ajvError);
        }
        return obj.children[path];
      }, root);
    }
  });
  return root;
}
function filterRedundantErrors(root, parent, key) {
  /**
   * If there is a `required` error then we can just skip everythig else.
   * And, also `required` should have more priority than `anyOf`. @see #8
   */
  (0, _utils.getErrors)(root).forEach(function (error) {
    if ((0, _utils.isRequiredError)(error)) {
      root.errors = [error];
      root.children = {};
    }
  });

  /**
   * If there is an `anyOf` error that means we have more meaningful errors
   * inside children. So we will just remove all errors from this level.
   *
   * If there are no children, then we don't delete the errors since we should
   * have at least one error to report.
   */
  if ((0, _utils.getErrors)(root).some(_utils.isAnyOfError)) {
    if (Object.keys(root.children).length > 0) {
      delete root.errors;
    }
  }

  /**
   * If all errors are `enum` and siblings have any error then we can safely
   * ignore the node.
   *
   * **CAUTION**
   * Need explicit `root.errors` check because `[].every(fn) === true`
   * https://en.wikipedia.org/wiki/Vacuous_truth#Vacuous_truths_in_mathematics
   */
  if (root.errors && root.errors.length && (0, _utils.getErrors)(root).every(_utils.isEnumError)) {
    if ((0, _utils.getSiblings)(parent)(root)
    // Remove any reference which becomes `undefined` later
    .filter(_utils.notUndefined).some(_utils.getErrors)) {
      delete parent.children[key];
    }
  }
  Object.entries(root.children).forEach(function (_ref) {
    var _ref2 = (0, _slicedToArray2["default"])(_ref, 2),
      k = _ref2[0],
      child = _ref2[1];
    return filterRedundantErrors(child, root, k);
  });
}
function createErrorInstances(root, options) {
  var errors = (0, _utils.getErrors)(root);
  if (errors.length && errors.every(_utils.isEnumError)) {
    var uniqueValues = new Set((0, _utils.concatAll)([])(errors.map(function (e) {
      return e.params.allowedValues;
    })));
    var allowedValues = (0, _toConsumableArray2["default"])(uniqueValues);
    var error = errors[0];
    return [new _validationErrors.EnumValidationError(_objectSpread(_objectSpread({}, error), {}, {
      params: {
        allowedValues: allowedValues
      }
    }), options)];
  }
  return (0, _utils.concatAll)(errors.reduce(function (ret, error) {
    switch (error.keyword) {
      case 'additionalProperties':
        return ret.concat(new _validationErrors.AdditionalPropValidationError(error, options));
      case 'pattern':
        return ret.concat(new _validationErrors.PatternValidationError(error, options));
      case 'required':
        return ret.concat(new _validationErrors.RequiredValidationError(error, options));
      case 'unevaluatedProperties':
        return ret.concat(new _validationErrors.UnevaluatedPropValidationError(error, options));
      default:
        return ret.concat(new _validationErrors.DefaultValidationError(error, options));
    }
  }, []))((0, _utils.getChildren)(root).map(function (child) {
    return createErrorInstances(child, options);
  }));
}
function prettify(ajvErrors, options) {
  var tree = makeTree(ajvErrors || []);
  filterRedundantErrors(tree);
  return createErrorInstances(tree, options);
}