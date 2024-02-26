// env.ts
import * as dotenv from 'dotenv';

dotenv.config();

const JULEP_API_KEY: string | undefined = process.env.JULEP_API_KEY;
const JULEP_API_URL: string = process.env.JULEP_API_URL || "https://api-alpha.julep.ai";