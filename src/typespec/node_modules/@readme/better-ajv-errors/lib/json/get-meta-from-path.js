"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = getMetaFromPath;
var _utils = require("./utils");
function getMetaFromPath(jsonAst, dataPath, includeIdentifierLocation) {
  var pointers = (0, _utils.getPointers)(dataPath);
  var lastPointerIndex = pointers.length - 1;
  return pointers.reduce(function (obj, pointer, idx) {
    switch (obj.type) {
      case 'Object':
        {
          var filtered = obj.members.filter(function (child) {
            return child.name.value === pointer;
          });
          if (filtered.length !== 1) {
            throw new Error("Couldn't find property ".concat(pointer, " of ").concat(dataPath));
          }
          var _filtered$ = filtered[0],
            name = _filtered$.name,
            value = _filtered$.value;
          return includeIdentifierLocation && idx === lastPointerIndex ? name : value;
        }
      case 'Array':
        return obj.elements[pointer];
      default:
        // eslint-disable-next-line no-console
        console.log(obj);
    }
  }, jsonAst.body);
}
module.exports = exports.default;