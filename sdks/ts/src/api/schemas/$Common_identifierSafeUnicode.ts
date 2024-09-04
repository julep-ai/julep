/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Common_identifierSafeUnicode = {
  type: "string",
  description: `For Unicode character safety
  See: https://unicode.org/reports/tr31/
  See: https://www.unicode.org/reports/tr39/#Identifier_Characters`,
  maxLength: 120,
  pattern:
    "^[\\p{L}\\p{Nl}\\p{Pattern_Syntax}\\p{Pattern_White_Space}]+[\\p{ID_Start}\\p{Mn}\\p{Mc}\\p{Nd}\\p{Pc}\\p{Pattern_Syntax}\\p{Pattern_White_Space}]*$",
} as const;
