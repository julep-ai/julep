"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.notUndefined = exports.isRequiredError = exports.isEnumError = exports.isAnyOfError = exports.getSiblings = exports.getErrors = exports.getChildren = exports.concatAll = void 0;
// Basic
var eq = function eq(x) {
  return function (y) {
    return x === y;
  };
};
var not = function not(fn) {
  return function (x) {
    return !fn(x);
  };
};
var getValues = function getValues(o) {
  return Object.values(o);
};
var notUndefined = function notUndefined(x) {
  return x !== undefined;
};

// Error
exports.notUndefined = notUndefined;
var isXError = function isXError(x) {
  return function (error) {
    return error.keyword === x;
  };
};
var isRequiredError = isXError('required');
exports.isRequiredError = isRequiredError;
var isAnyOfError = isXError('anyOf');
exports.isAnyOfError = isAnyOfError;
var isEnumError = isXError('enum');
exports.isEnumError = isEnumError;
var getErrors = function getErrors(node) {
  return node && node.errors || [];
};

// Node
exports.getErrors = getErrors;
var getChildren = function getChildren(node) {
  return node && getValues(node.children) || [];
};
exports.getChildren = getChildren;
var getSiblings = function getSiblings(parent /*: Node */) {
  return function /*: $ReadOnlyArray<Node> */
  (node /*: Node */) {
    return getChildren(parent).filter(not(eq(node)));
  };
};
exports.getSiblings = getSiblings;
var concatAll = /* ::<T> */

function concatAll(xs /*: $ReadOnlyArray<T> */) {
  return function /* : $ReadOnlyArray<T> */
  (ys /* : $ReadOnlyArray<T> */) {
    return ys.reduce(function (zs, z) {
      return zs.concat(z);
    }, xs);
  };
};
exports.concatAll = concatAll;