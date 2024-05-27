/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type ChatMLImageContentPart = {
  /**
   * Fixed to 'image_url'
   */
  type: "image_url";
  /**
   * Image content part, can be a URL or a base64-encoded image
   */
  image_url: {
    /**
     * URL or base64 data url (e.g. `data:image/jpeg;base64,<the base64 encoded image>`)
     */
    url: string;
    /**
     * image detail to feed into the model can be low | high | auto
     */
    detail?: "low" | "high" | "auto";
  };
};
