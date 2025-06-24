import { OpenAPI } from '@mintlify/openapi-types';
import { AxiosResponse } from 'axios';
export type NestedRecord = string | {
    [key: string]: NestedRecord;
};
export type SimpleRecord = Record<string, NestedRecord>;
export declare function initializeObject(obj: SimpleRecord, path: string[]): SimpleRecord;
export declare function getFileId(spec: OpenAPI.Document, index: number): string | number;
export declare function throwOnAxiosError(response: AxiosResponse<any, any>, errMsg: string): void;
export declare function formatErr(err: unknown): any;
