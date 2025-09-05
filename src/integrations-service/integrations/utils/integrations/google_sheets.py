import base64
import json

from beartype import beartype
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import (
    GoogleSheetsAppendArguments,
    GoogleSheetsBatchReadArguments,
    GoogleSheetsBatchWriteArguments,
    GoogleSheetsClearArguments,
    GoogleSheetsReadArguments,
    GoogleSheetsSetup,
    GoogleSheetsWriteArguments,
)
from ...env import julep_google_sheets_service_account_json
from ...models import (
    GoogleSheetsBatchReadOutput,
    GoogleSheetsBatchWriteOutput,
    GoogleSheetsClearOutput,
    GoogleSheetsReadOutput,
    GoogleSheetsUpdateResponse,
    GoogleSheetsValueRangeOutput,
    GoogleSheetsWriteOutput,
)


def get_sheets_service(setup: GoogleSheetsSetup):
    """
    Create and return a Google Sheets service object using authentication credentials.

    Args:
        setup: The GoogleSheetsSetup containing authentication credentials

    Returns:
        A Google Sheets service object

    Raises:
        ValueError: If authentication configuration is invalid
        RuntimeError: If Julep's service account is not configured
    """
    if setup.use_julep_service:
        # Use Julep's built-in service account
        julep_service_account = julep_google_sheets_service_account_json
        if not julep_service_account:
            msg = (
                "Julep's Google Sheets service account is not configured. "
                "Please contact support or use your own service account by setting "
                "use_julep_service=false and providing service_account_json."
            )
            raise RuntimeError(msg)
        service_account_json = julep_service_account
    else:
        # Use user-provided service account
        if not setup.service_account_json:
            msg = (
                "service_account_json is required when use_julep_service is false. "
                "Either provide your own service account JSON (base64 encoded) or "
                "set use_julep_service=true to use Julep's built-in service account."
            )
            raise ValueError(msg)
        service_account_json = setup.service_account_json

    # Decode and use the service account JSON
    try:
        # Add padding if missing
        missing_padding = len(service_account_json) % 4
        if missing_padding:
            service_account_json += '=' * (4 - missing_padding)
        creds_dict = json.loads(base64.b64decode(service_account_json))
    except Exception as e:
        msg = f"Failed to decode service account JSON: {str(e)}"
        raise ValueError(msg) from e
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )

    # Build and return the sheets service
    return build("sheets", "v4", credentials=creds)


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def read_values(
    setup: GoogleSheetsSetup, arguments: GoogleSheetsReadArguments
) -> GoogleSheetsReadOutput:
    """
    Read values from a specific range in a Google Sheets spreadsheet.

    Args:
        setup: The GoogleSheetsSetup containing authentication credentials
        arguments: The GoogleSheetsReadArguments with spreadsheet ID and range

    Returns:
        GoogleSheetsReadOutput with the values read from the spreadsheet
    """
    try:
        service = get_sheets_service(setup)
        sheet = service.spreadsheets()

        # Call the Sheets API to read values
        result = (
            sheet.values()
            .get(
                spreadsheetId=arguments.spreadsheet_id,
                range=arguments.range,
                majorDimension=arguments.major_dimension,
                valueRenderOption=arguments.value_render_option,
                dateTimeRenderOption=arguments.date_time_render_option,
            )
            .execute()
        )

        # Extract values and metadata
        values = result.get("values", [])
        range_str = result.get("range", arguments.range)
        major_dimension = result.get("majorDimension", arguments.major_dimension)

        return GoogleSheetsReadOutput(
            range=range_str,
            major_dimension=major_dimension,
            values=values,
        )

    except HttpError as error:
        msg = f"An error occurred while reading from Google Sheets: {error}"
        raise RuntimeError(msg) from error


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def write_values(
    setup: GoogleSheetsSetup, arguments: GoogleSheetsWriteArguments
) -> GoogleSheetsWriteOutput:
    """
    Write or update values in a specific range in a Google Sheets spreadsheet.

    Args:
        setup: The GoogleSheetsSetup containing authentication credentials
        arguments: The GoogleSheetsWriteArguments with spreadsheet ID, range, and values

    Returns:
        GoogleSheetsWriteOutput with information about the update
    """
    try:
        service = get_sheets_service(setup)
        sheet = service.spreadsheets()

        # Prepare the request body
        body = {"values": arguments.values}

        # Call the Sheets API to update values
        result = (
            sheet.values()
            .update(
                spreadsheetId=arguments.spreadsheet_id,
                range=arguments.range,
                valueInputOption=arguments.value_input_option,
                body=body,
                includeValuesInResponse=arguments.include_values_in_response,
                responseValueRenderOption=(
                    "FORMATTED_VALUE" if arguments.include_values_in_response else None
                ),
            )
            .execute()
        )

        # Extract update information
        return GoogleSheetsWriteOutput(
            spreadsheet_id=arguments.spreadsheet_id,
            updated_range=result.get("updatedRange"),
            updated_rows=result.get("updatedRows"),
            updated_columns=result.get("updatedColumns"),
            updated_cells=result.get("updatedCells"),
            updated_values=(
                result.get("updatedData", {}).get("values")
                if arguments.include_values_in_response
                else None
            ),
        )

    except HttpError as error:
        msg = f"An error occurred while writing to Google Sheets: {error}"
        raise RuntimeError(msg) from error


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def append_values(
    setup: GoogleSheetsSetup, arguments: GoogleSheetsAppendArguments
) -> GoogleSheetsWriteOutput:
    """
    Append new rows of data to a Google Sheets spreadsheet.

    Args:
        setup: The GoogleSheetsSetup containing authentication credentials
        arguments: The GoogleSheetsAppendArguments with spreadsheet ID, range, and values

    Returns:
        GoogleSheetsWriteOutput with information about the append operation
    """
    try:
        service = get_sheets_service(setup)
        sheet = service.spreadsheets()

        # Prepare the request body
        body = {"values": arguments.values}

        # Call the Sheets API to append values
        result = (
            sheet.values()
            .append(
                spreadsheetId=arguments.spreadsheet_id,
                range=arguments.range,
                valueInputOption=arguments.value_input_option,
                insertDataOption=arguments.insert_data_option,
                body=body,
                includeValuesInResponse=arguments.include_values_in_response,
                responseValueRenderOption=(
                    "FORMATTED_VALUE" if arguments.include_values_in_response else None
                ),
            )
            .execute()
        )

        # Extract update information
        updates = result.get("updates", {})
        return GoogleSheetsWriteOutput(
            spreadsheet_id=arguments.spreadsheet_id,
            updated_range=updates.get("updatedRange"),
            updated_rows=updates.get("updatedRows"),
            updated_columns=updates.get("updatedColumns"),
            updated_cells=updates.get("updatedCells"),
            updated_values=(
                updates.get("updatedData", {}).get("values")
                if arguments.include_values_in_response
                else None
            ),
        )

    except HttpError as error:
        msg = f"An error occurred while appending to Google Sheets: {error}"
        raise RuntimeError(msg) from error


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def clear_values(
    setup: GoogleSheetsSetup, arguments: GoogleSheetsClearArguments
) -> GoogleSheetsClearOutput:
    """
    Clear values from a specific range in a Google Sheets spreadsheet.

    Args:
        setup: The GoogleSheetsSetup containing authentication credentials
        arguments: The GoogleSheetsClearArguments with spreadsheet ID and range

    Returns:
        GoogleSheetsClearOutput with information about the clear operation
    """
    try:
        service = get_sheets_service(setup)
        sheet = service.spreadsheets()

        # Call the Sheets API to clear values
        result = (
            sheet.values()
            .clear(
                spreadsheetId=arguments.spreadsheet_id,
                range=arguments.range,
                body={},
            )
            .execute()
        )

        # Extract clear information
        return GoogleSheetsClearOutput(
            spreadsheet_id=arguments.spreadsheet_id,
            cleared_range=result.get("clearedRange", arguments.range),
        )

    except HttpError as error:
        msg = f"An error occurred while clearing Google Sheets: {error}"
        raise RuntimeError(msg) from error


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def batch_read(
    setup: GoogleSheetsSetup, arguments: GoogleSheetsBatchReadArguments
) -> GoogleSheetsBatchReadOutput:
    """
    Read values from multiple ranges in a Google Sheets spreadsheet in a single request.

    Args:
        setup: The GoogleSheetsSetup containing authentication credentials
        arguments: The GoogleSheetsBatchReadArguments with spreadsheet ID and ranges

    Returns:
        GoogleSheetsBatchReadOutput with the values read from all specified ranges
    """
    try:
        service = get_sheets_service(setup)
        sheet = service.spreadsheets()

        # Call the Sheets API to batch get values
        result = (
            sheet.values()
            .batchGet(
                spreadsheetId=arguments.spreadsheet_id,
                ranges=arguments.ranges,
                majorDimension=arguments.major_dimension,
                valueRenderOption=arguments.value_render_option,
                dateTimeRenderOption=arguments.date_time_render_option,
            )
            .execute()
        )

        # Extract value ranges
        value_ranges = [
            GoogleSheetsValueRangeOutput(
                range=value_range.get("range", ""),
                major_dimension=value_range.get("majorDimension", arguments.major_dimension),
                values=value_range.get("values", []),
            )
            for value_range in result.get("valueRanges", [])
        ]

        return GoogleSheetsBatchReadOutput(
            spreadsheet_id=arguments.spreadsheet_id,
            value_ranges=value_ranges,
        )

    except HttpError as error:
        msg = f"An error occurred during batch read from Google Sheets: {error}"
        raise RuntimeError(msg) from error


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def batch_write(
    setup: GoogleSheetsSetup, arguments: GoogleSheetsBatchWriteArguments
) -> GoogleSheetsBatchWriteOutput:
    """
    Write values to multiple ranges in a Google Sheets spreadsheet in a single request.

    Args:
        setup: The GoogleSheetsSetup containing authentication credentials
        arguments: The GoogleSheetsBatchWriteArguments with spreadsheet ID and data

    Returns:
        GoogleSheetsBatchWriteOutput with information about all updates
    """
    try:
        service = get_sheets_service(setup)
        sheet = service.spreadsheets()

        # Prepare the value ranges for the request
        value_ranges = []
        for data_item in arguments.data:
            value_range = {
                "range": data_item.range,
                "values": data_item.values,
            }
            if data_item.major_dimension:
                value_range["majorDimension"] = data_item.major_dimension
            value_ranges.append(value_range)

        # Prepare the request body
        body = {
            "valueInputOption": arguments.value_input_option,
            "data": value_ranges,
            "includeValuesInResponse": arguments.include_values_in_response,
        }

        if arguments.include_values_in_response:
            body["responseValueRenderOption"] = "FORMATTED_VALUE"

        # Call the Sheets API to batch update values
        result = (
            sheet.values()
            .batchUpdate(
                spreadsheetId=arguments.spreadsheet_id,
                body=body,
            )
            .execute()
        )

        # Extract update information
        responses = [
            GoogleSheetsUpdateResponse(
                updated_range=response.get("updatedRange"),
                updated_rows=response.get("updatedRows"),
                updated_columns=response.get("updatedColumns"),
                updated_cells=response.get("updatedCells"),
            )
            for response in result.get("responses", [])
        ]

        return GoogleSheetsBatchWriteOutput(
            spreadsheet_id=arguments.spreadsheet_id,
            total_updated_sheets=result.get("totalUpdatedSheets"),
            total_updated_rows=result.get("totalUpdatedRows"),
            total_updated_columns=result.get("totalUpdatedColumns"),
            total_updated_cells=result.get("totalUpdatedCells"),
            responses=responses,
        )

    except HttpError as error:
        msg = f"An error occurred during batch write to Google Sheets: {error}"
        raise RuntimeError(msg) from error
