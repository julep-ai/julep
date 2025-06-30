/* eslint-disable max-classes-per-file */
const { Ono } = require('@jsdevtools/ono');

const { stripHash, toFileSystemPath } = require('./url');

function setErrorName(err) {
  Object.defineProperty(err.prototype, 'name', {
    value: err.name,
    enumerable: true,
  });
}

const JSONParserError = class JSONParserError extends Error {
  constructor(message, source) {
    super();

    this.code = 'EUNKNOWN';
    this.message = message;
    this.source = source;
    this.path = null;

    Ono.extend(this);
  }

  get footprint() {
    return `${this.path}+${this.source}+${this.code}+${this.message}`;
  }
};

exports.JSONParserError = JSONParserError;
setErrorName(JSONParserError);

const JSONParserErrorGroup = class JSONParserErrorGroup extends Error {
  constructor(parser) {
    super();

    this.files = parser;
    this.message = `${this.errors.length} error${
      this.errors.length > 1 ? 's' : ''
    } occurred while reading '${toFileSystemPath(parser.$refs._root$Ref.path)}'`;

    Ono.extend(this);
  }

  static getParserErrors(parser) {
    const errors = [];

    for (const $ref of Object.values(parser.$refs._$refs)) {
      if ($ref.errors) {
        errors.push(...$ref.errors);
      }
    }

    return errors;
  }

  get errors() {
    return JSONParserErrorGroup.getParserErrors(this.files);
  }
};

exports.JSONParserErrorGroup = JSONParserErrorGroup;
setErrorName(JSONParserErrorGroup);

const ParserError = class ParserError extends JSONParserError {
  constructor(message, source) {
    super(`Error parsing ${source}: ${message}`, source);

    this.code = 'EPARSER';
  }
};

exports.ParserError = ParserError;
setErrorName(ParserError);

const UnmatchedParserError = class UnmatchedParserError extends JSONParserError {
  constructor(source) {
    super(`Could not find parser for "${source}"`, source);

    this.code = 'EUNMATCHEDPARSER';
  }
};

exports.UnmatchedParserError = UnmatchedParserError;
setErrorName(UnmatchedParserError);

const ResolverError = class ResolverError extends JSONParserError {
  constructor(ex, source) {
    super(ex.message || `Error reading file "${source}"`, source);

    this.code = 'ERESOLVER';

    if ('code' in ex) {
      this.ioErrorCode = String(ex.code);
    }
  }
};
exports.ResolverError = ResolverError;
setErrorName(ResolverError);

const UnmatchedResolverError = class UnmatchedResolverError extends JSONParserError {
  constructor(source) {
    super(`Could not find resolver for "${source}"`, source);

    this.code = 'EUNMATCHEDRESOLVER';
  }
};

exports.UnmatchedResolverError = UnmatchedResolverError;
setErrorName(UnmatchedResolverError);

const MissingPointerError = class MissingPointerError extends JSONParserError {
  constructor(token, path) {
    super(`Token "${token}" does not exist.`, stripHash(path));

    this.code = 'EMISSINGPOINTER';
  }
};

exports.MissingPointerError = MissingPointerError;
setErrorName(MissingPointerError);

const InvalidPointerError = class InvalidPointerError extends JSONParserError {
  constructor(pointer, path) {
    super(`Invalid $ref pointer "${pointer}". Pointers must begin with "#/"`, stripHash(path));

    this.code = 'EINVALIDPOINTER';
  }
};

exports.InvalidPointerError = InvalidPointerError;
setErrorName(InvalidPointerError);

exports.isHandledError = function (err) {
  return err instanceof JSONParserError || err instanceof JSONParserErrorGroup;
};

exports.normalizeError = function (err) {
  if (err.path === null) {
    // eslint-disable-next-line no-param-reassign
    err.path = [];
  }

  return err;
};
