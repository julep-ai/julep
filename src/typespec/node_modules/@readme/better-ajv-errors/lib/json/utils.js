"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.getPointers = void 0;
// TODO: Better error handling
var getPointers = function getPointers(dataPath) {
  var pointers = dataPath.split('/').slice(1);
  for (var index in pointers) {
    pointers[index] = pointers[index].split('~1').join('/').split('~0').join('~');
  }
  return pointers;
};
exports.getPointers = getPointers;