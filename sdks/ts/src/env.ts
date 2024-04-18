// env.ts

// Initialize JULEP_API_KEY and JULEP_API_URL with empty strings. These will be updated based on environment variables if available.
let JULEP_API_KEY = "";
let JULEP_API_URL = "";

if (typeof process !== "undefined" && process && process.cwd!) {
  JULEP_API_KEY = process.env.JULEP_API_KEY || "";
  JULEP_API_URL = process.env.JULEP_API_URL || "";
}

export { JULEP_API_KEY, JULEP_API_URL };
