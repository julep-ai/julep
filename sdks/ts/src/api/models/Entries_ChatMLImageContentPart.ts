/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Entries_BaseChatMLContentPart } from "./Entries_BaseChatMLContentPart";
import type { Entries_ImageURL } from "./Entries_ImageURL";
export type Entries_ChatMLImageContentPart = Entries_BaseChatMLContentPart & {
  image_url: Entries_ImageURL;
  /**
   * The image URL
   */
  image_url: Entries_ImageURL;
  /**
   * The type (fixed to 'image_url')
   */
  type: "image_url";
};
