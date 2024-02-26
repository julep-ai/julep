// env.js
const dotenv = require("dotenv");

dotenv.config();

const JULEP_API_KEY = process.env.JULEP_API_KEY;
const JULEP_API_URL = process.env.JULEP_API_URL || "https://api-alpha.julep.ai";
