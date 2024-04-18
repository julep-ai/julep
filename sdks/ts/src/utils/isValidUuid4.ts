import { validate as uuidValidate, version as uuidVersion } from "uuid";

/**
 * Validates if the input string is a valid UUID v4.
 * This function performs a two-step validation process:
 * 1. Validates the format of the UUID using `uuidValidate`.
 * 2. Checks that the version of the UUID is 4 using `uuidVersion`.
 * @param {string} uuidToTest The string to test for a valid UUID v4.
 * @returns {boolean} True if the input is a valid UUID v4, otherwise false.
 */
export function isValidUuid4(uuidToTest: string): boolean {
  // Validate the UUID format and check its version is 4
  return uuidValidate(uuidToTest) && uuidVersion(uuidToTest) === 4;
}
