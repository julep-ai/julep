/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_SleepFor = {
  properties: {
    seconds: {
      type: "number",
      description: `The number of seconds to sleep for`,
      isRequired: true,
      format: "uint16",
      maximum: 60,
    },
    minutes: {
      type: "number",
      description: `The number of minutes to sleep for`,
      isRequired: true,
      format: "uint16",
      maximum: 60,
    },
    hours: {
      type: "number",
      description: `The number of hours to sleep for`,
      isRequired: true,
      format: "uint16",
      maximum: 24,
    },
    days: {
      type: "number",
      description: `The number of days to sleep for`,
      isRequired: true,
      format: "uint16",
      maximum: 30,
    },
  },
} as const;
