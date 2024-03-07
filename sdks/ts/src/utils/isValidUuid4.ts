import { validate as uuidValidate, version as uuidVersion } from "uuid";

/**
 * Checks if the input string is a valid UUID v4.
 * @param {string} uuidToTest The string to test for a valid UUID v4.
 * @returns {boolean} True if the input is a valid UUID v4, otherwise false.
 */
export function isValidUuid4(uuidToTest: string): boolean {
  return uuidValidate(uuidToTest) && uuidVersion(uuidToTest) === 4;
}
