// utils.js

const { validate: uuidValidate, version: uuidVersion } = require("uuid");

/**
 * Check if uuidToTest is a valid UUID v4.
 *
 * @param {string} uuidToTest - String to test for valid UUID v4.
 * @returns {boolean} True if the input is a valid UUID v4, otherwise False.
 */
function is_valid_uuid4(uuidToTest) {
  return uuidValidate(uuidToTest) && uuidVersion(uuidToTest) === 4;
}

module.exports = { is_valid_uuid4 };
