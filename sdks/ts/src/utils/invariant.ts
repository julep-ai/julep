export function invariant(
  condition: any,
  message: string = "Invariant Violation",
): void {
  if (!condition) {
    throw new Error(message);
  }

  return;
}
