from typing import Any

from pydantic import ConfigDict, Field

from .base_models import BaseOutput


class GoogleSheetsReadOutput(BaseOutput):
    """Output model for reading values from Google Sheets"""

    model_config = ConfigDict(extra="allow")

    range: str = Field(description="The range that was read")
    major_dimension: str = Field(description="The major dimension of the values")
    values: list[list[Any]] = Field(description="The values read from the spreadsheet")


class GoogleSheetsWriteOutput(BaseOutput):
    """Output model for writing/appending values to Google Sheets"""

    model_config = ConfigDict(extra="allow")

    spreadsheet_id: str = Field(description="The spreadsheet ID that was updated")
    updated_range: str | None = Field(default=None, description="The range that was updated")
    updated_rows: int | None = Field(default=None, description="The number of rows updated")
    updated_columns: int | None = Field(
        default=None, description="The number of columns updated"
    )
    updated_cells: int | None = Field(default=None, description="The number of cells updated")
    updated_values: list[list[Any]] | None = Field(
        default=None, description="The values that were written (if requested)"
    )


class GoogleSheetsClearOutput(BaseOutput):
    """Output model for clearing values from Google Sheets"""

    model_config = ConfigDict(extra="allow")

    spreadsheet_id: str = Field(description="The spreadsheet ID that was cleared")
    cleared_range: str = Field(description="The range that was cleared")


class GoogleSheetsValueRangeOutput(BaseOutput):
    """Represents a range of values that was read"""

    model_config = ConfigDict(extra="allow")

    range: str = Field(description="The range that was read")
    major_dimension: str = Field(description="The major dimension of the values")
    values: list[list[Any]] = Field(description="The values read from the range")


class GoogleSheetsBatchReadOutput(BaseOutput):
    """Output model for batch reading from Google Sheets"""

    model_config = ConfigDict(extra="allow")

    spreadsheet_id: str = Field(description="The spreadsheet ID that was read")
    value_ranges: list[GoogleSheetsValueRangeOutput] = Field(
        description="The value ranges that were read"
    )


class GoogleSheetsUpdateResponse(BaseOutput):
    """Details about a single range update in batch operations"""

    model_config = ConfigDict(extra="allow")

    updated_range: str | None = Field(default=None, description="The range that was updated")
    updated_rows: int | None = Field(default=None, description="The number of rows updated")
    updated_columns: int | None = Field(
        default=None, description="The number of columns updated"
    )
    updated_cells: int | None = Field(default=None, description="The number of cells updated")


class GoogleSheetsBatchWriteOutput(BaseOutput):
    """Output model for batch writing to Google Sheets"""

    model_config = ConfigDict(extra="allow")

    spreadsheet_id: str = Field(description="The spreadsheet ID that was updated")
    total_updated_sheets: int | None = Field(
        default=None, description="Total number of sheets updated"
    )
    total_updated_rows: int | None = Field(
        default=None, description="Total number of rows updated"
    )
    total_updated_columns: int | None = Field(
        default=None, description="Total number of columns updated"
    )
    total_updated_cells: int | None = Field(
        default=None, description="Total number of cells updated"
    )
    responses: list[GoogleSheetsUpdateResponse] | None = Field(
        default=None, description="Details about each range that was updated"
    )
