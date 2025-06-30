"use strict";

var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");
var _regenerator = _interopRequireDefault(require("@babel/runtime/regenerator"));
var _slicedToArray2 = _interopRequireDefault(require("@babel/runtime/helpers/slicedToArray"));
var _asyncToGenerator2 = _interopRequireDefault(require("@babel/runtime/helpers/asyncToGenerator"));
var _momoa = require("@humanwhocodes/momoa");
var _testHelpers = require("../../test-helpers");
var _enum = _interopRequireDefault(require("../enum"));
describe('Enum', function () {
  describe('when value is an object', function () {
    var schema;
    var data;
    var jsonRaw;
    var jsonAst;
    beforeAll( /*#__PURE__*/(0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee() {
      var _yield$getSchemaAndDa, _yield$getSchemaAndDa2;
      return _regenerator["default"].wrap(function _callee$(_context) {
        while (1) {
          switch (_context.prev = _context.next) {
            case 0:
              _context.next = 2;
              return (0, _testHelpers.getSchemaAndData)('enum', __dirname);
            case 2:
              _yield$getSchemaAndDa = _context.sent;
              _yield$getSchemaAndDa2 = (0, _slicedToArray2["default"])(_yield$getSchemaAndDa, 2);
              schema = _yield$getSchemaAndDa2[0];
              data = _yield$getSchemaAndDa2[1];
              jsonRaw = JSON.stringify(data, null, 2);
              jsonAst = (0, _momoa.parse)(jsonRaw);
            case 8:
            case "end":
              return _context.stop();
          }
        }
      }, _callee);
    })));
    it.each([['prints correctly for enum prop', true], ['prints correctly for enum prop [without colors]', false]])('%s', function (_, colorize) {
      var error = new _enum["default"]({
        keyword: 'enum',
        dataPath: '/id',
        schemaPath: '#/enum',
        params: {
          allowedValues: ['foo', 'bar']
        },
        message: 'should be equal to one of the allowed values'
      }, {
        colorize: colorize,
        data: data,
        schema: schema,
        jsonRaw: jsonRaw,
        jsonAst: jsonAst
      });
      expect(error.print()).toMatchSnapshot();
    });
    it.each([['prints correctly for no levenshtein match', true], ['prints correctly for no levenshtein match [without colors]', false]])('%s', function (_, colorize) {
      var error = new _enum["default"]({
        keyword: 'enum',
        dataPath: '/id',
        schemaPath: '#/enum',
        params: {
          allowedValues: ['one', 'two']
        },
        message: 'should be equal to one of the allowed values'
      }, {
        colorize: colorize,
        data: data,
        schema: schema,
        jsonRaw: jsonRaw,
        jsonAst: jsonAst
      });
      expect(error.print()).toMatchSnapshot();
    });
    it.each([['prints correctly for empty value', true], ['prints correctly for empty value [without colors]', false]])('%s', function (_, colorize) {
      var error = new _enum["default"]({
        keyword: 'enum',
        dataPath: '/id',
        schemaPath: '#/enum',
        params: {
          allowedValues: ['foo', 'bar']
        },
        message: 'should be equal to one of the allowed values'
      }, {
        colorize: colorize,
        data: data,
        schema: schema,
        jsonRaw: jsonRaw,
        jsonAst: jsonAst
      });
      expect(error.print(schema, {
        id: ''
      })).toMatchSnapshot();
    });
  });
  describe('when value is a primitive', function () {
    var schema;
    var data;
    var jsonRaw;
    var jsonAst;
    beforeAll( /*#__PURE__*/(0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee2() {
      var _yield$getSchemaAndDa3, _yield$getSchemaAndDa4;
      return _regenerator["default"].wrap(function _callee2$(_context2) {
        while (1) {
          switch (_context2.prev = _context2.next) {
            case 0:
              _context2.next = 2;
              return (0, _testHelpers.getSchemaAndData)('enum-string', __dirname);
            case 2:
              _yield$getSchemaAndDa3 = _context2.sent;
              _yield$getSchemaAndDa4 = (0, _slicedToArray2["default"])(_yield$getSchemaAndDa3, 2);
              schema = _yield$getSchemaAndDa4[0];
              data = _yield$getSchemaAndDa4[1];
              jsonRaw = JSON.stringify(data, null, 2);
              jsonAst = (0, _momoa.parse)(jsonRaw);
            case 8:
            case "end":
              return _context2.stop();
          }
        }
      }, _callee2);
    })));
    it.each([['prints correctly for enum prop', true], ['prints correctly for enum prop [without colors]', false]])('%s', function (_, colorize) {
      var error = new _enum["default"]({
        keyword: 'enum',
        dataPath: '',
        schemaPath: '#/enum',
        params: {
          allowedValues: ['foo', 'bar']
        },
        message: 'should be equal to one of the allowed values'
      }, {
        colorize: colorize,
        data: data,
        schema: schema,
        jsonRaw: jsonRaw,
        jsonAst: jsonAst
      });
      expect(error.print()).toMatchSnapshot();
    });
    it.each([['prints correctly for no levenshtein match', true], ['prints correctly for no levenshtein match [without colors]', false]])('%s', function (_, colorize) {
      var error = new _enum["default"]({
        keyword: 'enum',
        dataPath: '',
        schemaPath: '#/enum',
        params: {
          allowedValues: ['one', 'two']
        },
        message: 'should be equal to one of the allowed values'
      }, {
        colorize: colorize,
        data: data,
        schema: schema,
        jsonRaw: jsonRaw,
        jsonAst: jsonAst
      });
      expect(error.print()).toMatchSnapshot();
    });
    it.each([['prints correctly for empty value', true], ['prints correctly for empty value [without colors]', false]])('%s', function (_, colorize) {
      var error = new _enum["default"]({
        keyword: 'enum',
        dataPath: '',
        schemaPath: '#/enum',
        params: {
          allowedValues: ['foo', 'bar']
        },
        message: 'should be equal to one of the allowed values'
      }, {
        colorize: colorize,
        data: data,
        schema: schema,
        jsonRaw: jsonRaw,
        jsonAst: jsonAst
      });
      expect(error.print(schema, '')).toMatchSnapshot();
    });
  });
});