/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Chat_DefaultChatSettings = {
  description: `Default settings for the chat session (also used by the agent)`,
  properties: {
    preset: {
      type: "all-of",
      description: `Generation preset (one of: problem_solving, conversational, fun, prose, creative, business, deterministic, code, multilingual)`,
      contains: [
        {
          type: "Chat_GenerationPreset",
        },
      ],
    },
    frequency_penalty: {
      type: "number",
      description: `Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.`,
      format: "float",
      maximum: 2,
      minimum: -2,
    },
    presence_penalty: {
      type: "number",
      description: `Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.`,
      format: "float",
      maximum: 2,
      minimum: -2,
    },
    temperature: {
      type: "number",
      description: `What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.`,
      format: "float",
      maximum: 5,
    },
    top_p: {
      type: "number",
      description: `Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both.`,
      format: "float",
      maximum: 1,
    },
    repetition_penalty: {
      type: "number",
      description: `Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.`,
      format: "float",
      maximum: 2,
    },
    length_penalty: {
      type: "number",
      description: `Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated.`,
      format: "float",
      maximum: 2,
    },
    min_p: {
      type: "number",
      description: `Minimum probability compared to leading token to be considered`,
      format: "float",
      maximum: 1,
    },
  },
} as const;
