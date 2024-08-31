/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Executions_Transition = {
  type: "all-of",
  contains: [
    {
      type: "Executions_TransitionEvent",
    },
    {
      properties: {
        execution_id: {
          type: "all-of",
          contains: [
            {
              type: "Common_uuid",
            },
          ],
          isReadOnly: true,
          isRequired: true,
        },
        current: {
          type: "all-of",
          contains: [
            {
              type: "Executions_TransitionTarget",
            },
          ],
          isReadOnly: true,
          isRequired: true,
        },
        next: {
          type: "all-of",
          contains: [
            {
              type: "Executions_TransitionTarget",
            },
          ],
          isReadOnly: true,
          isRequired: true,
          isNullable: true,
        },
        id: {
          type: "all-of",
          contains: [
            {
              type: "Common_uuid",
            },
          ],
          isReadOnly: true,
          isRequired: true,
        },
        metadata: {
          type: "dictionary",
          contains: {
            properties: {},
          },
        },
      },
    },
  ],
} as const;
