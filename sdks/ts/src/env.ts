// env.ts

let JULEP_API_KEY = "";
let JULEP_API_URL = "";

if (typeof process !== "undefined" && process && process.cwd!) {
  JULEP_API_KEY = process.env.JULEP_API_KEY || "";
  JULEP_API_URL = process.env.JULEP_API_URL || "";
}

export { JULEP_API_KEY, JULEP_API_URL };
