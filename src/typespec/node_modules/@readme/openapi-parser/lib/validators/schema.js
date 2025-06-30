const { ono } = require('@jsdevtools/ono');
const betterAjvErrors = require('@readme/better-ajv-errors');
const { openapi } = require('@readme/openapi-schemas');
const Ajv = require('ajv/dist/2020');
const AjvDraft4 = require('ajv-draft-04');

const { getSpecificationName } = require('../util');

/**
 * We've had issues with specs larger than 2MB+ with 1,000+ errors causing memory leaks so if we
 * have a spec with more than `LARGE_SPEC_ERROR_CAP` errors and it's **stringified** length is
 * larger than `LARGE_SPEC_LIMITS` then we will only return the first `LARGE_SPEC_ERROR_CAP` errors.
 *
 * Ideally we'd be looking at the byte size of the spec instead of looking at its stringified
 * length value but the Blob API, which we'd use to get its size with `new Blob([str]).size;`, was
 * only recently introduced in Node 15.
 *
 * w/r/t the 5,000,000 limit here: The spec we found causing these memory leaks had a size of
 * 13,934,323 so 5mil seems like a decent cap to start with.
 *
 * @see {@link https://developer.mozilla.org/en-US/docs/Web/API/Blob}
 */
const LARGE_SPEC_ERROR_CAP = 20;
const LARGE_SPEC_SIZE_CAP = 5000000;

module.exports = validateSchema;

/**
 * Validates the given Swagger API against the Swagger 2.0 or OpenAPI 3.0 and 3.1 schemas.
 *
 * @param {SwaggerObject} api
 * @param {Object} options
 */
function validateSchema(api, options) {
  let ajv;

  // Choose the appropriate schema (Swagger or OpenAPI)
  let schema;

  if (api.swagger) {
    schema = openapi.v2;
    ajv = initializeAjv();
  } else if (api.openapi.startsWith('3.1')) {
    schema = openapi.v31legacy;

    // There's a bug with Ajv in how it handles `$dynamicRef` in the way that it's used within the 3.1 schema so we
    // need to do some adhoc workarounds.
    // https://github.com/OAI/OpenAPI-Specification/issues/2689
    // https://github.com/ajv-validator/ajv/issues/1573
    const schemaDynamicRef = schema.$defs.schema;
    delete schemaDynamicRef.$dynamicAnchor;

    schema.$defs.components.properties.schemas.additionalProperties = schemaDynamicRef;
    schema.$defs.header.dependentSchemas.schema.properties.schema = schemaDynamicRef;
    schema.$defs['media-type'].properties.schema = schemaDynamicRef;
    schema.$defs.parameter.properties.schema = schemaDynamicRef;

    ajv = initializeAjv(false);
  } else {
    schema = openapi.v3;
    ajv = initializeAjv();
  }

  // Validate against the schema
  const isValid = ajv.validate(schema, api);
  if (!isValid) {
    const err = ajv.errors;

    let additionalErrors = 0;
    let reducedErrors = reduceAjvErrors(err);
    const totalErrors = reducedErrors.length;
    if (reducedErrors.length >= LARGE_SPEC_ERROR_CAP) {
      try {
        if (JSON.stringify(api).length >= LARGE_SPEC_SIZE_CAP) {
          additionalErrors = reducedErrors.length - 20;
          reducedErrors = reducedErrors.slice(0, 20);
        }
      } catch (error) {
        // If we failed to stringify the API definition to look at its size then we should process
        // all of its errors as-is.
      }
    }

    let message = `${getSpecificationName(api)} schema validation failed.\n`;
    message += '\n';
    message += betterAjvErrors(schema, api, reducedErrors, {
      colorize: options.validate.colorizeErrors,
      indent: 2,
    });

    if (additionalErrors) {
      message += '\n\n';
      message += `Plus an additional ${additionalErrors} errors. Please resolve the above and re-run validation to see more.`;
    }

    throw ono.syntax(err, { details: err, totalErrors }, message);
  }
}

/**
 * Determines which version of Ajv to load and prepares it for use.
 *
 * @param {bool} draft04
 * @returns {Ajv}
 */
function initializeAjv(draft04 = true) {
  const opts = {
    allErrors: true,
    strict: false,
    validateFormats: false,
  };

  if (draft04) {
    return new AjvDraft4(opts);
  }

  return new Ajv(opts);
}

/**
 * Because of the way that Ajv works, if a validation error occurs deep within a schema there's a chance that errors
 * will also be thrown for its immediate parents, leading to a case where we'll eventually show the error indecipherable
 * errors like "$ref is missing here!" instance of what's _actually_ going on where they may have mistyped `enum` as
 * `enumm`.
 *
 * To alleviate this confusing noise, we're compressing Ajv errors down to only surface the deepest point for each
 * lineage, so that if a user typos `enum` as `enumm` we'll surface just that error for them (because really that's
 * **the** error).
 *
 * @param {Array} errors
 * @returns {Array}
 */
function reduceAjvErrors(errors) {
  const flattened = new Map();

  errors.forEach(err => {
    // These two errors appear when a child schema of them has a problem and instead of polluting the user with
    // indecipherable noise we should instead relay the more specific error to them. If this is all that's present in
    // the stack then as a safety net before we wrap up we'll just return the original `errors` stack.
    if (["must have required property '$ref'", 'must match exactly one schema in oneOf'].includes(err.message)) {
      return;
    }

    // If this is our first run through let's initialize our dataset and move along.
    if (!flattened.size) {
      flattened.set(err.instancePath, err);
      return;
    } else if (flattened.has(err.instancePath)) {
      // If we already have an error recorded for this `instancePath` we can ignore it because we (likely) already have
      // recorded the more specific error.
      return;
    }

    // If this error hasn't already been recorded, maybe it's an error against the same `instancePath` stack, in which
    // case we should ignore it because the more specific error has already been recorded.
    let shouldRecordError = true;
    flattened.forEach(flat => {
      if (flat.instancePath.includes(err.instancePath)) {
        shouldRecordError = false;
      }
    });

    if (shouldRecordError) {
      flattened.set(err.instancePath, err);
    }
  });

  // If we weren't able to fold errors down for whatever reason just return the original stack.
  if (!flattened.size) {
    return errors;
  }

  return [...flattened.values()];
}
