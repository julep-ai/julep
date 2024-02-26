// utils.ts

import { validate as uuidValidate, version as uuidVersion } from 'uuid';

/**
 * Check if uuid_to_test is a valid UUID v4.
 *
 * @param {string} uuidToTest - String to test for valid UUID v4.
 * @returns {boolean} True if the input is a valid UUID v4, otherwise False.
 */

function is_valid_uuid4(uuid_to_test: string): boolean {
  return uuidValidate(uuid_to_test) && uuidVersion(uuid_to_test) === 4;
}