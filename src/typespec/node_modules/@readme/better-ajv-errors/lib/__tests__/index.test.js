"use strict";

var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");
var _regenerator = _interopRequireDefault(require("@babel/runtime/regenerator"));
var _slicedToArray2 = _interopRequireDefault(require("@babel/runtime/helpers/slicedToArray"));
var _asyncToGenerator2 = _interopRequireDefault(require("@babel/runtime/helpers/asyncToGenerator"));
var _openapiSchemas = require("@apidevtools/openapi-schemas");
var _ajv = _interopRequireDefault(require("ajv"));
var _2 = _interopRequireDefault(require("ajv/dist/2020"));
var _3 = _interopRequireDefault(require(".."));
var _lib = _interopRequireDefault(require("../../lib"));
var _testHelpers = require("../test-helpers");
describe('Main', function () {
  it.each([['should output error with reconstructed codeframe', true], ['should output error with reconstructed codeframe [without colors]', false]])('%s', /*#__PURE__*/function () {
    var _ref = (0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee(_, colorize) {
      var _yield$getSchemaAndDa, _yield$getSchemaAndDa2, schema, data, ajv, validate, valid, res;
      return _regenerator["default"].wrap(function _callee$(_context) {
        while (1) {
          switch (_context.prev = _context.next) {
            case 0:
              _context.next = 2;
              return (0, _testHelpers.getSchemaAndData)('default', __dirname);
            case 2:
              _yield$getSchemaAndDa = _context.sent;
              _yield$getSchemaAndDa2 = (0, _slicedToArray2["default"])(_yield$getSchemaAndDa, 2);
              schema = _yield$getSchemaAndDa2[0];
              data = _yield$getSchemaAndDa2[1];
              ajv = new _ajv["default"]();
              validate = ajv.compile(schema);
              valid = validate(data);
              expect(valid).toBe(false);
              res = (0, _3["default"])(schema, data, validate.errors, {
                colorize: colorize,
                format: 'cli',
                indent: 2
              });
              expect(res).toMatchSnapshot();
            case 12:
            case "end":
              return _context.stop();
          }
        }
      }, _callee);
    }));
    return function (_x, _x2) {
      return _ref.apply(this, arguments);
    };
  }());
  it('should output error with codeframe', /*#__PURE__*/(0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee2() {
    var _yield$getSchemaAndDa3, _yield$getSchemaAndDa4, schema, data, json, ajv, validate, valid, res;
    return _regenerator["default"].wrap(function _callee2$(_context2) {
      while (1) {
        switch (_context2.prev = _context2.next) {
          case 0:
            _context2.next = 2;
            return (0, _testHelpers.getSchemaAndData)('default', __dirname);
          case 2:
            _yield$getSchemaAndDa3 = _context2.sent;
            _yield$getSchemaAndDa4 = (0, _slicedToArray2["default"])(_yield$getSchemaAndDa3, 3);
            schema = _yield$getSchemaAndDa4[0];
            data = _yield$getSchemaAndDa4[1];
            json = _yield$getSchemaAndDa4[2];
            ajv = new _ajv["default"]();
            validate = ajv.compile(schema);
            valid = validate(data);
            expect(valid).toBe(false);
            res = (0, _3["default"])(schema, data, validate.errors, {
              format: 'cli',
              json: json
            });
            expect(res).toMatchSnapshot();
          case 13:
          case "end":
            return _context2.stop();
        }
      }
    }, _callee2);
  })));
  describe('Babel export', function () {
    it('should function as normal', /*#__PURE__*/(0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee3() {
      var _yield$getSchemaAndDa5, _yield$getSchemaAndDa6, schema, data, ajv, validate, valid, res;
      return _regenerator["default"].wrap(function _callee3$(_context3) {
        while (1) {
          switch (_context3.prev = _context3.next) {
            case 0:
              _context3.next = 2;
              return (0, _testHelpers.getSchemaAndData)('default', __dirname);
            case 2:
              _yield$getSchemaAndDa5 = _context3.sent;
              _yield$getSchemaAndDa6 = (0, _slicedToArray2["default"])(_yield$getSchemaAndDa5, 2);
              schema = _yield$getSchemaAndDa6[0];
              data = _yield$getSchemaAndDa6[1];
              ajv = new _ajv["default"]();
              validate = ajv.compile(schema);
              valid = validate(data);
              expect(valid).toBe(false);
              res = (0, _lib["default"])(schema, data, validate.errors);
              expect(res).toMatchSnapshot();
            case 12:
            case "end":
              return _context3.stop();
          }
        }
      }, _callee3);
    })));
  });
  describe('complex schema examples', function () {
    it('should output an error on an invalid OpenAPI 3.1 definition', /*#__PURE__*/(0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee4() {
      var schema, _yield$getSchemaAndDa7, _yield$getSchemaAndDa8, data, ajv, validate, valid, res;
      return _regenerator["default"].wrap(function _callee4$(_context4) {
        while (1) {
          switch (_context4.prev = _context4.next) {
            case 0:
              schema = _openapiSchemas.openapi.v31;
              _context4.next = 3;
              return (0, _testHelpers.getSchemaAndData)('openapi-3.1', __dirname);
            case 3:
              _yield$getSchemaAndDa7 = _context4.sent;
              _yield$getSchemaAndDa8 = (0, _slicedToArray2["default"])(_yield$getSchemaAndDa7, 2);
              data = _yield$getSchemaAndDa8[1];
              // Need to load the 2020 dist because it supports draft-7, which we'll need for an 3.1.0
              // OpenAPI definition.
              ajv = new _2["default"]({
                allErrors: true,
                strict: false,
                validateFormats: false
              });
              validate = ajv.compile(schema);
              valid = validate(data);
              expect(valid).toBe(false);
              res = (0, _3["default"])(schema, data, validate.errors, {
                indent: 2,
                format: 'cli'
              });
              expect(res).toMatchSnapshot();
            case 12:
            case "end":
              return _context4.stop();
          }
        }
      }, _callee4);
    })));
  });
});