import { DataSchema, DataSchemaArray, IncrementalDataSchema, IncrementalDataSchemaArray } from '@mintlify/validation';
import { z } from 'zod';
type SchemaInput = DataSchema | IncrementalDataSchema;
export declare function dataSchemaArrayToZod(schemas: DataSchemaArray | IncrementalDataSchemaArray): z.ZodTypeAny;
export declare function dataSchemaToZod(schema: SchemaInput): z.ZodTypeAny;
export {};
