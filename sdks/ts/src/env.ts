// env.ts
import { config } from "dotenv";

if (typeof process !== "undefined" && process && process.cwd!) {
  config();

  if (!process.env.JULEP_API_KEY) {
    process.env.JULEP_API_KEY = "";
  }
  if (!process.env.JULEP_API_URL) {
    process.env.JULEP_API_URL = "";
  }
}

export const JULEP_API_KEY = process.env.JULEP_API_KEY || "";
export const JULEP_API_URL = process.env.JULEP_API_URL || "";
