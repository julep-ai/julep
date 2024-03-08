// env.ts
import { config } from "dotenv";

config();

export const JULEP_API_KEY = process.env.JULEP_API_KEY;
export const JULEP_API_URL = process.env.JULEP_API_URL;
