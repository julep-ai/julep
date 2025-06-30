"use strict";

var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");
var _regenerator = _interopRequireDefault(require("@babel/runtime/regenerator"));
var _slicedToArray2 = _interopRequireDefault(require("@babel/runtime/helpers/slicedToArray"));
var _asyncToGenerator2 = _interopRequireDefault(require("@babel/runtime/helpers/asyncToGenerator"));
var _openapiSchemas = require("@apidevtools/openapi-schemas");
var _ = _interopRequireDefault(require("ajv/dist/2020"));
var _2 = _interopRequireDefault(require("../.."));
var _testHelpers = require("../../test-helpers");
describe('Main', function () {
  it('should support js output format for default errors', /*#__PURE__*/(0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee() {
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
            ajv = new _["default"]();
            validate = ajv.compile(schema);
            valid = validate(data);
            expect(valid).toBe(false);
            res = (0, _2["default"])(schema, data, validate.errors, {
              format: 'js'
            });
            expect(res).toMatchSnapshot();
          case 12:
          case "end":
            return _context.stop();
        }
      }
    }, _callee);
  })));
  it('should support js output format for required errors', /*#__PURE__*/(0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee2() {
    var _yield$getSchemaAndDa3, _yield$getSchemaAndDa4, schema, data, ajv, validate, valid, res;
    return _regenerator["default"].wrap(function _callee2$(_context2) {
      while (1) {
        switch (_context2.prev = _context2.next) {
          case 0:
            _context2.next = 2;
            return (0, _testHelpers.getSchemaAndData)('required', __dirname);
          case 2:
            _yield$getSchemaAndDa3 = _context2.sent;
            _yield$getSchemaAndDa4 = (0, _slicedToArray2["default"])(_yield$getSchemaAndDa3, 2);
            schema = _yield$getSchemaAndDa4[0];
            data = _yield$getSchemaAndDa4[1];
            ajv = new _["default"]();
            validate = ajv.compile(schema);
            valid = validate(data);
            expect(valid).toBe(false);
            res = (0, _2["default"])(schema, data, validate.errors, {
              format: 'js'
            });
            expect(res).toMatchSnapshot();
          case 12:
          case "end":
            return _context2.stop();
        }
      }
    }, _callee2);
  })));
  it('should support js output format for additionalProperties errors', /*#__PURE__*/(0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee3() {
    var _yield$getSchemaAndDa5, _yield$getSchemaAndDa6, schema, data, ajv, validate, valid, res;
    return _regenerator["default"].wrap(function _callee3$(_context3) {
      while (1) {
        switch (_context3.prev = _context3.next) {
          case 0:
            _context3.next = 2;
            return (0, _testHelpers.getSchemaAndData)('additionalProperties', __dirname);
          case 2:
            _yield$getSchemaAndDa5 = _context3.sent;
            _yield$getSchemaAndDa6 = (0, _slicedToArray2["default"])(_yield$getSchemaAndDa5, 2);
            schema = _yield$getSchemaAndDa6[0];
            data = _yield$getSchemaAndDa6[1];
            ajv = new _["default"]();
            validate = ajv.compile(schema);
            valid = validate(data);
            expect(valid).toBe(false);
            res = (0, _2["default"])(schema, data, validate.errors, {
              format: 'js'
            });
            expect(res).toMatchSnapshot();
          case 12:
          case "end":
            return _context3.stop();
        }
      }
    }, _callee3);
  })));

  // Though this is testing `patternProperties` cases, the error that'll come back will just be for `pattern` since
  // that's what `patternPropeties` utilizes in the schema.
  it('should support js output format for patternProperties errors', /*#__PURE__*/(0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee4() {
    var _yield$getSchemaAndDa7, _yield$getSchemaAndDa8, data, schema, ajv, validate, valid, res;
    return _regenerator["default"].wrap(function _callee4$(_context4) {
      while (1) {
        switch (_context4.prev = _context4.next) {
          case 0:
            _context4.next = 2;
            return (0, _testHelpers.getSchemaAndData)('patternProperties', __dirname);
          case 2:
            _yield$getSchemaAndDa7 = _context4.sent;
            _yield$getSchemaAndDa8 = (0, _slicedToArray2["default"])(_yield$getSchemaAndDa7, 2);
            data = _yield$getSchemaAndDa8[1];
            // The OpenAPI 3.1 schema has a good example of this for component names so we're using that instead of writing
            // our own.
            schema = _openapiSchemas.openapi.v31;
            ajv = new _["default"]({
              allErrors: true,
              strict: false,
              validateFormats: false
            });
            validate = ajv.compile(schema);
            valid = validate(data);
            expect(valid).toBe(false);
            res = (0, _2["default"])(schema, data, validate.errors, {
              format: 'js'
            });
            expect(res).toMatchSnapshot();
          case 12:
          case "end":
            return _context4.stop();
        }
      }
    }, _callee4);
  })));
  it('should support js output format for unevaluatedProperties errors', /*#__PURE__*/(0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee5() {
    var _yield$getSchemaAndDa9, _yield$getSchemaAndDa10, schema, data, ajv, validate, valid, res;
    return _regenerator["default"].wrap(function _callee5$(_context5) {
      while (1) {
        switch (_context5.prev = _context5.next) {
          case 0:
            _context5.next = 2;
            return (0, _testHelpers.getSchemaAndData)('unevaluatedProperties', __dirname);
          case 2:
            _yield$getSchemaAndDa9 = _context5.sent;
            _yield$getSchemaAndDa10 = (0, _slicedToArray2["default"])(_yield$getSchemaAndDa9, 2);
            schema = _yield$getSchemaAndDa10[0];
            data = _yield$getSchemaAndDa10[1];
            ajv = new _["default"]();
            validate = ajv.compile(schema);
            valid = validate(data);
            expect(valid).toBe(false);
            res = (0, _2["default"])(schema, data, validate.errors, {
              format: 'js'
            });
            expect(res).toMatchSnapshot();
          case 12:
          case "end":
            return _context5.stop();
        }
      }
    }, _callee5);
  })));
  it('should support js output format for enum errors', /*#__PURE__*/(0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee6() {
    var _yield$getSchemaAndDa11, _yield$getSchemaAndDa12, schema, data, ajv, validate, valid, res;
    return _regenerator["default"].wrap(function _callee6$(_context6) {
      while (1) {
        switch (_context6.prev = _context6.next) {
          case 0:
            _context6.next = 2;
            return (0, _testHelpers.getSchemaAndData)('enum', __dirname);
          case 2:
            _yield$getSchemaAndDa11 = _context6.sent;
            _yield$getSchemaAndDa12 = (0, _slicedToArray2["default"])(_yield$getSchemaAndDa11, 2);
            schema = _yield$getSchemaAndDa12[0];
            data = _yield$getSchemaAndDa12[1];
            ajv = new _["default"]();
            validate = ajv.compile(schema);
            valid = validate(data);
            expect(valid).toBe(false);
            res = (0, _2["default"])(schema, data, validate.errors, {
              format: 'js'
            });
            expect(res).toMatchSnapshot();
          case 12:
          case "end":
            return _context6.stop();
        }
      }
    }, _callee6);
  })));
});