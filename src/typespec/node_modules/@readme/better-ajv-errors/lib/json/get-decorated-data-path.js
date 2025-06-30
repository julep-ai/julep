"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = getDecoratedDataPath;
var _utils = require("./utils");
function getTypeName(obj) {
  if (!obj || !obj.elements) {
    return '';
  }
  var type = obj.elements.filter(function (child) {
    return child && child.name && child.name.value === 'type';
  });
  if (!type.length) {
    return '';
  }
  return type[0].value && ":".concat(type[0].value.value) || '';
}
function getDecoratedDataPath(jsonAst, dataPath) {
  var decoratedPath = '';
  (0, _utils.getPointers)(dataPath).reduce(function (obj, pointer) {
    switch (obj.type) {
      case 'Object':
        {
          decoratedPath += "/".concat(pointer);
          var filtered = obj.members.filter(function (child) {
            return child.name.value === pointer;
          });
          if (filtered.length !== 1) {
            throw new Error("Couldn't find property ".concat(pointer, " of ").concat(dataPath));
          }
          return filtered[0].value;
        }
      case 'Array':
        {
          decoratedPath += "/".concat(pointer).concat(getTypeName(obj.elements[pointer]));
          return obj.elements[pointer];
        }
      default:
        // eslint-disable-next-line no-console
        console.log(obj);
    }
  }, jsonAst.body);
  return decoratedPath;
}
module.exports = exports.default;