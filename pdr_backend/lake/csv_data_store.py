import os
from typing import Optional, Union

import polars as pl
from enforce_typing import enforce_types
from polars.type_aliases import SchemaDict


@enforce_types
def _pad_with_zeroes(number: int, length: int = 10) -> str:
    """
    Pads the given number with zeros to make it 10 digits long.
    @args:
        number: int - number to fill with zeros
    """
    number_str = str(number)
    return number_str.rjust(length, "0")


@enforce_types
def _get_to_value(file_path: str) -> Union[int, None]:
    """
    Returns the end time from the given file_path.

    This tries to solve for tables with variable name lengths.
    Table 1: "pdr_predictions"
    Table 2: "gold_summary_predictions_by_day"

    However, if a table has the keyword "from" or "to" it will fai.

    A better way to do this, would be to search back from end.
    split("_")[-1] = "1701503000000.csv"
    split("_")[-2] = "to"
    split("_")[-3] = "1701500000000"
    split("_")[-4] = "from"

    It's possible that csv files do not contain a to_value.
    In this case, the function returns None.

    @args:
        file_path: str - path of the file
    @returns:
        Union[int,None] - end time from the file_path
    """
    # let's split the string by "/" to get the last element
    file_signature = file_path.split("/")[-1]

    # let's find the "from" index inside the string split
    signature_str_split = file_signature.split("_")

    # let's find the from index and value
    from_index, to_index = None, None
    from_index = next(
        (
            index
            for index, str_value in enumerate(signature_str_split)
            if "from" in str_value
        ),
        None,
    )

    if from_index is not None:
        from_index += 1
        to_index = from_index + 2

    if from_index is None or to_index is None:
        return None

    # if to_index is out of bounds, return None
    if to_index >= len(signature_str_split):
        return None

    # if to_index is not out of bounds, but only `_to_.csv` there is no to_value, return None
    to_value = signature_str_split[to_index].replace(".csv", "")
    if to_value == "":
        return None

    # return the to_value
    return int(to_value)


@enforce_types
def _get_from_value(file_path: str) -> int:
    """
    Returns the start time from the given file_path.
    @args:
        file_path: str - path of the file
    @returns:
        int - start time from the file_path
    """
    # suppose the following file path
    # "folder1/folder2/pdr_predictions_from_1701503000000_to_1701503000000.csv"
    # now, we want to split the string, and then find
    # if there is a "from" value and a "to" value
    # keep in mind that the "to" value can be missing,
    # if the file hasn't yet closed due to row limit

    # let's split the string by "/" to get the last element
    file_signature = file_path.split("/")[-1]

    # let's find the "from" index inside the string split
    signature_str_split = file_signature.split("_")

    # let's find the from index and value
    from_index = next(
        (
            index
            for index, str_value in enumerate(signature_str_split)
            if "from" in str_value
        ),
        None,
    )

    if from_index is not None:
        return int(signature_str_split[from_index + 1])

    raise ValueError(f"File {file_path} does not contain a 'from' value")


class CSVDataStore:
    def __init__(self, base_path: str, dataset_identifier: str):
        self.base_path = base_path
        self.dataset_identifier = dataset_identifier

    @staticmethod
    def from_table(table):
        return CSVDataStore(table.base_path, table.table_name)

    @enforce_types
    def _create_file_name(self, start_time: int, end_time: Optional[int]) -> str:
        """
        Creates a file name using the given dataset_identifier,
        start_time, end_time, and row_count.
        @args:
            start_time: int - start time of the data TIMESTAMP
            end_time: int - end time of the data TIMESTAMP
        """
        start_time_str = _pad_with_zeroes(start_time)
        end_time_str = _pad_with_zeroes(end_time) if end_time else ""

        return f"{self.dataset_identifier}_from_{start_time_str}_to_{end_time_str}.csv"

    @enforce_types
    def _create_file_path(self, start_time: int, end_time: Optional[int]) -> str:
        """
        Creates the file path for the given dataset_identifier,
        start_time, end_time.
        @args:
            start_time: str - start time of the data
            end_time: str - end time of the data
        """
        file_name = self._create_file_name(start_time, end_time)
        folder_path = self._get_folder_path()

        return os.path.join(folder_path, file_name)

    def _get_folder_path(self) -> str:
        """
        Returns the folder path for the given dataset_identifier.
        If the folder does not exist, it will be created.
        """
        folder_path = os.path.join(self.base_path, self.dataset_identifier)
        os.makedirs(folder_path, exist_ok=True)

        return folder_path

    def get_file_paths(self, do_sort=True) -> list:
        """
        Returns the file paths for the given dataset_identifier.
        """
        folder_path = self._get_folder_path()
        file_names = os.listdir(folder_path)

        if do_sort:
            file_names = sorted(file_names)

        return [os.path.join(folder_path, file_name) for file_name in file_names]

    def has_data(self) -> bool:
        """
        Returns True if the csv files in the folder
        corresponding to the given dataset_identifier have data.
        @returns:
            bool - True if the csv files have data
        """
        file_paths = self.get_file_paths(do_sort=False)

        # check if the csv file has more than 0 bytes
        return any(os.path.getsize(file_path) > 0 for file_path in file_paths)

    def _get_last_file_row_count(self) -> Optional[int]:
        """
        Returns the row count of the last file for the given dataset_identifier.
        @returns:
            row_count: Optional[int] - The row count of the last file
        """
        last_file_path = self._get_last_file_path()

        if not last_file_path:
            return None

        # Read the last file
        last_file = pl.read_csv(last_file_path)
        row_count = last_file.shape[0]

        return row_count

    def _get_last_file_path(self) -> str:
        """
        Returns the path of the last file in the given folder_path.
        @args:
            folder_path: str - path of the folder
        @returns:
            str - path of the last file
        """
        file_paths = self.get_file_paths()

        return file_paths[-1] if file_paths else ""

    def _append_remaining_rows(
        self,
        data: pl.DataFrame,
        max_row_count: int,
        schema: Optional[SchemaDict] = None,
    ):
        last_file_row_count = self._get_last_file_row_count()
        if last_file_row_count is None or last_file_row_count >= max_row_count:
            return data

        remaining_rows = min(max_row_count - last_file_row_count, len(data))

        remaining_data = data.slice(0, remaining_rows)
        last_file_path = self._get_last_file_path()
        last_file_data = pl.read_csv(last_file_path, schema=schema)
        last_file_data = last_file_data.vstack(remaining_data).rechunk()

        t_start_time = last_file_data["timestamp"][0]
        t_end_time = last_file_data["timestamp"][-1]

        last_file_data.write_csv(last_file_path)
        # change the name of the file to reflect the new row count
        new_file_path = self._create_file_path(
            t_start_time,
            t_end_time if len(data) >= remaining_rows else None,
        )

        os.rename(last_file_path, new_file_path)

        return data.slice(remaining_rows, len(data) - remaining_rows)

    def read_all(self, schema: Optional[SchemaDict] = None) -> pl.DataFrame:
        """
        Reads all the data from the csv files in the folder
        corresponding to the given dataset_identifier.
        @returns:
            pl.DataFrame - data read from the csv files
        """
        file_paths = self.get_file_paths()

        if not file_paths:
            return pl.DataFrame([], schema=schema)

        # Read the first file to create the DataFrame
        data = pl.read_csv(file_paths[0], schema=schema)
        # Read the remaining files and append them to the DataFrame
        for file_path in file_paths[1:]:
            data = data.vstack(pl.read_csv(file_path, schema=schema))

        return data.rechunk()

    def read(
        self,
        start_time: int,
        end_time: int,
        schema: Optional[SchemaDict] = None,
        filter_args: Optional[bool] = True,
    ) -> pl.DataFrame:
        """
        Reads the data from the csv file in the folder
        corresponding to the given dataset_identifier,
        start_time, and end_time.
        @args:
            dataset_identifier: str - identifier of the dataset
            start_time: int - start time of the data
            end_time: int - end time of the data
        @returns:
            pl.DataFrame - data read from the csv file
        """
        data = self.read_all(schema=schema)
        # if the data is empty, return
        if len(data) == 0:
            return data

        # if the data is not empty,
        # check the timestamp column exists and is of type int64
        if "timestamp" not in data.columns or filter_args is False:
            return data

        return data.filter(
            (data["timestamp"] >= start_time) & (data["timestamp"] <= end_time)
        ).rechunk()

    def write(
        self,
        data: pl.DataFrame,
        schema: Optional[SchemaDict] = None,
    ):
        """
        Writes the given data to a csv file in the folder
        corresponding to the given dataset_identifier.
        @args:
            data: pl.DataFrame - The data to write, it has to be sorted by timestamp
            dataset_identifier: str - The dataset identifier
        """
        max_row_count = 1000
        data = data.sort("timestamp")
        data = self._append_remaining_rows(data, max_row_count, schema)

        chunks = [
            data.slice(i, min(max_row_count, len(data) - i))
            for i in range(0, len(data), max_row_count)
        ]

        for i, chunk in enumerate(chunks):
            start_time = int(chunk["timestamp"][0])
            end_time = int(chunk["timestamp"][-1])
            file_path = self._create_file_path(
                start_time,
                end_time if len(chunk) >= max_row_count else None,
            )
            chunk.write_csv(file_path)

    @enforce_types
    def get_last_timestamp(self) -> Optional[int]:
        """
        Returns the last timestamp from the last csv files in the folder
        corresponding to the given dataset_identifier.
        @returns:
            Optional[int] - last timestamp from the csv files
        """
        file_path = self._get_last_file_path()

        if not file_path:
            return None

        to_value = _get_to_value(file_path)
        if to_value is not None and to_value > 0:
            return to_value

        # read the last record from the file
        last_file = pl.read_csv(file_path)
        return int(last_file["timestamp"][-1])
