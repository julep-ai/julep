import "../common";

using Common;

namespace Tools;

/** Setup parameters for Google Sheets integration */
model GoogleSheetsSetup {
    /** 
     * Whether to use Julep's built-in Google Sheets service account.
     * If true, no credentials needed. If false, service_account_json is required.
     */
    use_julep_service: boolean;
    
    /** 
     * Base64 encoded service account JSON for authentication.
     * Required when use_julep_service is false.
     * Users can provide their own service account for better isolation and quota management.
     */
    service_account_json?: string;
    
    /** Default number of retry attempts for API calls */
    @minValue(1)
    @maxValue(10)
    default_retry_count?: uint8 = 3;
}

/** Arguments for reading values from a spreadsheet */
model GoogleSheetsReadArguments {
    /** The ID of the spreadsheet to read from */
    spreadsheet_id: string;
    
    /** The A1 notation of the range to read */
    range: string;
    
    /** The major dimension that results should use */
    major_dimension?: "ROWS" | "COLUMNS" = "ROWS";
    
    /** How values should be represented in the output */
    value_render_option?: "FORMATTED_VALUE" | "UNFORMATTED_VALUE" | "FORMULA" = "FORMATTED_VALUE";
    
    /** How dates, times, and durations should be represented */
    date_time_render_option?: "SERIAL_NUMBER" | "FORMATTED_STRING" = "FORMATTED_STRING";
}

/** Arguments for writing values to a spreadsheet */
model GoogleSheetsWriteArguments {
    /** The ID of the spreadsheet to write to */
    spreadsheet_id: string;
    
    /** The A1 notation of the range to write to */
    range: string;
    
    /** The values to write (2D array) */
    values: unknown[][];
    
    /** How the input data should be interpreted */
    value_input_option?: "RAW" | "USER_ENTERED" = "USER_ENTERED";
    
    /** How the input data should be inserted */
    insert_data_option?: "OVERWRITE" | "INSERT_ROWS" = "OVERWRITE";
    
    /** Whether to include the values in the response */
    include_values_in_response?: boolean = false;
}

/** Arguments for appending values to a spreadsheet */
model GoogleSheetsAppendArguments {
    /** The ID of the spreadsheet to append to */
    spreadsheet_id: string;
    
    /** The A1 notation of the range to start appending from */
    range: string;
    
    /** The values to append (2D array) */
    values: unknown[][];
    
    /** How the input data should be interpreted */
    value_input_option?: "RAW" | "USER_ENTERED" = "USER_ENTERED";
    
    /** How the input data should be inserted */
    insert_data_option?: "OVERWRITE" | "INSERT_ROWS" = "INSERT_ROWS";
    
    /** Whether to include the values in the response */
    include_values_in_response?: boolean = false;
}

/** Arguments for clearing values from a spreadsheet */
model GoogleSheetsClearArguments {
    /** The ID of the spreadsheet to clear values from */
    spreadsheet_id: string;
    
    /** The A1 notation of the range to clear */
    range: string;
}

/** Arguments for batch reading values from multiple ranges */
model GoogleSheetsBatchReadArguments {
    /** The ID of the spreadsheet to read from */
    spreadsheet_id: string;
    
    /** The A1 notation of the ranges to read */
    ranges: string[];
    
    /** The major dimension that results should use */
    major_dimension?: "ROWS" | "COLUMNS" = "ROWS";
    
    /** How values should be represented in the output */
    value_render_option?: "FORMATTED_VALUE" | "UNFORMATTED_VALUE" | "FORMULA" = "FORMATTED_VALUE";
    
    /** How dates, times, and durations should be represented */
    date_time_render_option?: "SERIAL_NUMBER" | "FORMATTED_STRING" = "FORMATTED_STRING";
}

/** Arguments for batch updating values in multiple ranges */
model GoogleSheetsBatchWriteArguments {
    /** The ID of the spreadsheet to write to */
    spreadsheet_id: string;
    
    /** The data to write to each range */
    data: GoogleSheetsValueRange[];
    
    /** How the input data should be interpreted */
    value_input_option?: "RAW" | "USER_ENTERED" = "USER_ENTERED";
    
    /** Whether to include the values in the response */
    include_values_in_response?: boolean = false;
}

/** Represents a range of values to write */
model GoogleSheetsValueRange {
    /** The A1 notation of the range */
    range: string;
    
    /** The values for the range (2D array) */
    values: unknown[][];
    
    /** The major dimension of the values */
    major_dimension?: "ROWS" | "COLUMNS" = "ROWS";
}

alias GoogleSheetsMethod =
    | /** Read values from a specific range */
      "read_values"
    | /** Write values to a specific range */
      "write_values"
    | /** Append values to a spreadsheet */
      "append_values"
    | /** Clear values from a range */
      "clear_values"
    | /** Read values from multiple ranges */
      "batch_read"
    | /** Write values to multiple ranges */
      "batch_write";

/** Google Sheets integration definition */
model GoogleSheetsIntegrationDef extends BaseIntegrationDef {
    /** The provider must be "google_sheets" */
    provider: "google_sheets" = "google_sheets";
    
    /** The specific method of the integration to call */
    method?: GoogleSheetsMethod;
    
    /** The setup parameters for Google Sheets */
    setup?: GoogleSheetsSetup;
    
    /** The arguments for the method */
    arguments?: GoogleSheetsReadArguments | GoogleSheetsWriteArguments | GoogleSheetsAppendArguments | GoogleSheetsClearArguments | GoogleSheetsBatchReadArguments | GoogleSheetsBatchWriteArguments;
}

/** Google Sheets Provider Card */
model GoogleSheetsProviderCard extends BaseProviderCard {
    provider: "google_sheets" = "google_sheets";
    setup: GoogleSheetsSetup;
    methods: ProviderMethod<unknown, unknown>[] = #[
        #{
            method: "read_values",
            description: "Read values from a specific range in a Google Sheets spreadsheet",
        },
        #{
            method: "write_values",
            description: "Write or update values in a specific range in a Google Sheets spreadsheet",
        },
        #{
            method: "append_values",
            description: "Append new rows of data to a Google Sheets spreadsheet",
        },
        #{
            method: "clear_values",
            description: "Clear values from a specific range in a Google Sheets spreadsheet",
        },
        #{
            method: "batch_read",
            description: "Read values from multiple ranges in a Google Sheets spreadsheet",
        },
        #{
            method: "batch_write",
            description: "Write values to multiple ranges in a Google Sheets spreadsheet",
        }
    ];
    info: ProviderInfo = #{
        url: "https://sheets.google.com/",
        docs: "https://developers.google.com/sheets/api",
        icon: "https://www.gstatic.com/images/branding/product/1x/sheets_2020q4_48dp.png",
        friendly_name: "Google Sheets",
    };
}

/** Output for reading values from Google Sheets */
model GoogleSheetsReadOutput {
    /** The range that was read */
    range: string;
    
    /** The major dimension of the values */
    major_dimension: string;
    
    /** The values read from the spreadsheet */
    values: unknown[][];
}

/** Output for writing/appending values to Google Sheets */
model GoogleSheetsWriteOutput {
    /** The spreadsheet ID that was updated */
    spreadsheet_id: string;
    
    /** The range that was updated */
    updated_range?: string;
    
    /** The number of rows updated */
    updated_rows?: int32;
    
    /** The number of columns updated */
    updated_columns?: int32;
    
    /** The number of cells updated */
    updated_cells?: int32;
    
    /** The values that were written (if requested) */
    updated_values?: unknown[][];
}

/** Output for clearing values from Google Sheets */
model GoogleSheetsClearOutput {
    /** The spreadsheet ID that was cleared */
    spreadsheet_id: string;
    
    /** The range that was cleared */
    cleared_range: string;
}

/** Output for batch reading from Google Sheets */
model GoogleSheetsBatchReadOutput {
    /** The spreadsheet ID that was read */
    spreadsheet_id: string;
    
    /** The value ranges that were read */
    value_ranges: GoogleSheetsValueRangeOutput[];
}

/** Represents a range of values that was read */
model GoogleSheetsValueRangeOutput {
    /** The range that was read */
    range: string;
    
    /** The major dimension of the values */
    major_dimension: string;
    
    /** The values read from the range */
    values: unknown[][];
}

/** Output for batch writing to Google Sheets */
model GoogleSheetsBatchWriteOutput {
    /** The spreadsheet ID that was updated */
    spreadsheet_id: string;
    
    /** Total number of sheets updated */
    total_updated_sheets?: int32;
    
    /** Total number of rows updated */
    total_updated_rows?: int32;
    
    /** Total number of columns updated */
    total_updated_columns?: int32;
    
    /** Total number of cells updated */
    total_updated_cells?: int32;
    
    /** Details about each range that was updated */
    responses?: GoogleSheetsUpdateResponse[];
}

/** Details about a single range update */
model GoogleSheetsUpdateResponse {
    /** The range that was updated */
    updated_range?: string;
    
    /** The number of rows updated */
    updated_rows?: int32;
    
    /** The number of columns updated */
    updated_columns?: int32;
    
    /** The number of cells updated */
    updated_cells?: int32;
}