/**
 * Ensures that a condition is met, throwing a custom error message if not.
 * @param condition The condition to test. If falsy, an error is thrown.
 * @param message Optional. The error message to throw if the condition is not met. Defaults to "Invariant Violation".
 */
export function invariant(
  condition: any,
  message: string = "Invariant Violation",
): void {
  // Throw an error with the provided message if the condition is falsy
  if (!condition) {
    throw new Error(message);
  }

  return;
}
