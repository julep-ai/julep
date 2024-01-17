import { MaybeValid, Schema, SchemaType, ValidationError } from "../../Schema";
import { entries } from "../../utils/entries";
import { getErrorMessageForIncorrectType } from "../../utils/getErrorMessageForIncorrectType";
import { isPlainObject } from "../../utils/isPlainObject";
import { MaybePromise } from "../../utils/MaybePromise";
import { maybeSkipValidation } from "../../utils/maybeSkipValidation";
import { getSchemaUtils } from "../schema-utils";
import { BaseRecordSchema, RecordSchema } from "./types";

export function record<RawKey extends string | number, RawValue, ParsedValue, ParsedKey extends string | number>(
    keySchema: Schema<RawKey, ParsedKey>,
    valueSchema: Schema<RawValue, ParsedValue>
): RecordSchema<RawKey, RawValue, ParsedKey, ParsedValue> {
    const baseSchema: BaseRecordSchema<RawKey, RawValue, ParsedKey, ParsedValue> = {
        parse: async (raw, opts) => {
            return validateAndTransformRecord({
                value: raw,
                isKeyNumeric: (await keySchema.getType()) === SchemaType.NUMBER,
                transformKey: (key) =>
                    keySchema.parse(key, {
                        ...opts,
                        breadcrumbsPrefix: [...(opts?.breadcrumbsPrefix ?? []), `${key} (key)`],
                    }),
                transformValue: (value, key) =>
                    valueSchema.parse(value, {
                        ...opts,
                        breadcrumbsPrefix: [...(opts?.breadcrumbsPrefix ?? []), `${key}`],
                    }),
                breadcrumbsPrefix: opts?.breadcrumbsPrefix,
            });
        },
        json: async (parsed, opts) => {
            return validateAndTransformRecord({
                value: parsed,
                isKeyNumeric: (await keySchema.getType()) === SchemaType.NUMBER,
                transformKey: (key) =>
                    keySchema.json(key, {
                        ...opts,
                        breadcrumbsPrefix: [...(opts?.breadcrumbsPrefix ?? []), `${key} (key)`],
                    }),
                transformValue: (value, key) =>
                    valueSchema.json(value, {
                        ...opts,
                        breadcrumbsPrefix: [...(opts?.breadcrumbsPrefix ?? []), `${key}`],
                    }),
                breadcrumbsPrefix: opts?.breadcrumbsPrefix,
            });
        },
        getType: () => SchemaType.RECORD,
    };

    return {
        ...maybeSkipValidation(baseSchema),
        ...getSchemaUtils(baseSchema),
    };
}

async function validateAndTransformRecord<TransformedKey extends string | number, TransformedValue>({
    value,
    isKeyNumeric,
    transformKey,
    transformValue,
    breadcrumbsPrefix = [],
}: {
    value: unknown;
    isKeyNumeric: boolean;
    transformKey: (key: string | number) => MaybePromise<MaybeValid<TransformedKey>>;
    transformValue: (value: unknown, key: string | number) => MaybePromise<MaybeValid<TransformedValue>>;
    breadcrumbsPrefix: string[] | undefined;
}): Promise<MaybeValid<Record<TransformedKey, TransformedValue>>> {
    if (!isPlainObject(value)) {
        return {
            ok: false,
            errors: [
                {
                    path: breadcrumbsPrefix,
                    message: getErrorMessageForIncorrectType(value, "object"),
                },
            ],
        };
    }

    return entries(value).reduce<Promise<MaybeValid<Record<TransformedKey, TransformedValue>>>>(
        async (accPromise, [stringKey, value]) => {
            // skip nullish keys
            if (value == null) {
                return accPromise;
            }

            const acc = await accPromise;

            let key: string | number = stringKey;
            if (isKeyNumeric) {
                const numberKey = stringKey.length > 0 ? Number(stringKey) : NaN;
                if (!isNaN(numberKey)) {
                    key = numberKey;
                }
            }
            const transformedKey = await transformKey(key);

            const transformedValue = await transformValue(value, key);

            if (acc.ok && transformedKey.ok && transformedValue.ok) {
                return {
                    ok: true,
                    value: {
                        ...acc.value,
                        [transformedKey.value]: transformedValue.value,
                    },
                };
            }

            const errors: ValidationError[] = [];
            if (!acc.ok) {
                errors.push(...acc.errors);
            }
            if (!transformedKey.ok) {
                errors.push(...transformedKey.errors);
            }
            if (!transformedValue.ok) {
                errors.push(...transformedValue.errors);
            }

            return {
                ok: false,
                errors,
            };
        },
        Promise.resolve({ ok: true, value: {} as Record<TransformedKey, TransformedValue> })
    );
}
