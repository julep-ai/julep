"use strict";

var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");
Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.getSchemaAndData = getSchemaAndData;
var _regenerator = _interopRequireDefault(require("@babel/runtime/regenerator"));
var _asyncToGenerator2 = _interopRequireDefault(require("@babel/runtime/helpers/asyncToGenerator"));
var _fs = require("fs");
var _jestFixtures = require("jest-fixtures");
function getSchemaAndData(_x, _x2) {
  return _getSchemaAndData.apply(this, arguments);
}
function _getSchemaAndData() {
  _getSchemaAndData = (0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee(name, dirPath) {
    var schemaPath, schema, dataPath, json, data;
    return _regenerator["default"].wrap(function _callee$(_context) {
      while (1) {
        switch (_context.prev = _context.next) {
          case 0:
            _context.next = 2;
            return (0, _jestFixtures.getFixturePath)(dirPath, name, 'schema.json');
          case 2:
            schemaPath = _context.sent;
            schema = JSON.parse((0, _fs.readFileSync)(schemaPath, 'utf8'));
            _context.next = 6;
            return (0, _jestFixtures.getFixturePath)(dirPath, name, 'data.json');
          case 6:
            dataPath = _context.sent;
            json = (0, _fs.readFileSync)(dataPath, 'utf8');
            data = JSON.parse(json);
            return _context.abrupt("return", [schema, data, json]);
          case 10:
          case "end":
            return _context.stop();
        }
      }
    }, _callee);
  }));
  return _getSchemaAndData.apply(this, arguments);
}