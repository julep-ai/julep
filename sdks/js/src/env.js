// env.js
const dotenv = require("dotenv");

const { JulepApiEnvironment } = require("./api/environments");

dotenv.config();

const JULEP_API_KEY = process.env.JULEP_API_KEY;
const JULEP_API_URL = process.env.JULEP_API_URL || JulepApiEnvironment.Default;

module.exports = {
  JULEP_API_KEY,
  JULEP_API_URL,
};
