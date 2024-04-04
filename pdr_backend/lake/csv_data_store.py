import os
from typing import List, Optional, Union
import polars as pl
from polars.type_aliases import SchemaDict

from enforce_typing import enforce_types
from pdr_backend.lake.base_data_store import BaseDataStore
from pdr_backend.util.time_types import UnixTimeMs


class CSVDataStore(BaseDataStore):

    @enforce_types
    def _get_folder_path(self, dataset_identifier: str) -> str:
        """
        Returns the folder path for the given dataset_identifier.
        If the folder does not exist, it will be created.
        @args:
            dataset_identifier: str - identifier of the dataset
        """
        folder_path = os.path.join(self.base_path, dataset_identifier)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path

    @enforce_types
    def _fill_with_zero(self, number: int, length: int = 10) -> str:
        """
        Fills the given number with zeros to make it 10 digits long.
        @args:
            number: int - number to fill with zeros
        """
        number_str = str(number)
        return f"{(length - len(number_str)) * '0'}{number_str}"

    @enforce_types
    def _create_file_name(
        self, dataset_identifier: str, start_time: int, end_time: Optional[int]
    ) -> str:
        """
        Creates a file name using the given dataset_identifier,
        start_time, end_time, and row_count.
        @args:
            dataset_identifier: str - identifier of the dataset
            start_time: int - start time of the data TIMESTAMP
            end_time: int - end time of the data TIMESTAMP
        """
        start_time_str = self._fill_with_zero(start_time)

        start_phrase = f"_from_{start_time_str}"

        end_phrase = f"_to_{self._fill_with_zero(end_time)}" if end_time else "_to_"

        return f"{dataset_identifier}{start_phrase}{end_phrase}.csv"

    @enforce_types
    def _create_file_path(
        self, dataset_identifier: str, start_time: int, end_time: Optional[int]
    ) -> str:
        """
        Creates the file path for the given dataset_identifier,
        start_time, end_time.
        @args:
            dataset_identifier: str - identifier of the dataset
            start_time: str - start time of the data
            end_time: str - end time of the data
        """

        file_name = self._create_file_name(dataset_identifier, start_time, end_time)
        folder_path = self._get_folder_path(dataset_identifier)
        return os.path.join(folder_path, file_name)

    @enforce_types
    def _chunk_data(self, data: pl.DataFrame) -> List[pl.DataFrame]:
        """
        Splits the given data into chunks of up to 1000 rows each.
        @args:
            data: pl.DataFrame - data to be chunked
        """
        return [
            data.slice(i, min(1000, len(data) - i)) for i in range(0, len(data), 1000)
        ]

    def write(
        self,
        dataset_identifier: str,
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
        last_file_row_count = self._get_last_file_row_count(dataset_identifier)
        if last_file_row_count is not None:
            if last_file_row_count < max_row_count:
                remaining_rows = max_row_count - last_file_row_count

                # get the first remaining_rows rows
                remaining_rows = min(remaining_rows, len(data))

                remaining_data = data.slice(0, remaining_rows)

                last_file_path = self._get_last_file_path(
                    self._get_folder_path(dataset_identifier)
                )
                last_file_data = pl.read_csv(last_file_path, schema=schema)
                last_file_data = last_file_data.vstack(remaining_data)

                t_start_time = last_file_data["timestamp"][0]
                t_end_time = last_file_data["timestamp"][-1]

                last_file_data.write_csv(last_file_path)
                # change the name of the file to reflect the new row count
                new_file_path = self._create_file_path(
                    dataset_identifier,
                    t_start_time,
                    t_end_time if len(data) >= remaining_rows else None,
                )

                os.rename(last_file_path, new_file_path)

                data = data.slice(remaining_rows, len(data) - remaining_rows)

        # check if the folder exists
        if not self.get_folder_exists(dataset_identifier):
            folder_path = self._get_folder_path(dataset_identifier)
            os.makedirs(folder_path, exist_ok=True)

        chunks = [
            data.slice(i, min(max_row_count, len(data) - i))
            for i in range(0, len(data), max_row_count)
        ]

        for i, chunk in enumerate(chunks):
            start_time = int(chunk["timestamp"][0])
            end_time = int(chunk["timestamp"][-1])
            file_path = self._create_file_path(
                dataset_identifier,
                start_time,
                end_time if len(chunk) >= max_row_count else None,
            )
            chunk.write_csv(file_path)

    @enforce_types
    def bulk_write(self, data_list: List[pl.DataFrame], dataset_identifier: str):
        """
        Writes the given list of data to csv files in the folder
        corresponding to the given dataset_identifier.
        @args:
            data_list: List[pl.DataFrame] - list of data to be written
            dataset_identifier: str - identifier of the dataset
        """
        for data in data_list:
            self.write(dataset_identifier, data)

    @enforce_types
    def _get_to_value(self, file_path: str) -> Union[int, None]:
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
    def _get_from_value(self, file_path: str) -> int:
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

    @enforce_types
    def _get_file_paths(
        self, folder_path: str, start_time: int, end_time: int
    ) -> List[str]:
        """
        Returns a list of file paths in the given folder_path
        that contain the given start_time and end_time.
        @args:
            folder_path: str - path of the folder
            start_time: int - start time of the data
            end_time: int end time of the data
        @returns:
            List[str] - list of file paths
        """

        file_names = os.listdir(folder_path)
        file_paths = [os.path.join(folder_path, file_name) for file_name in file_names]

        valid_paths = []
        for file_path in file_paths:
            _from_value = self._get_from_value(file_path)
            _to_value = self._get_to_value(file_path)

            if start_time <= _from_value <= end_time:
                valid_paths.append(file_path)
            elif _to_value is not None and start_time <= _to_value <= end_time:
                valid_paths.append(file_path)

        return valid_paths

    @enforce_types
    def has_data(self, dataset_identifier: str) -> bool:
        """
        Returns True if the csv files in the folder
        corresponding to the given dataset_identifier have data.
        @args:
            dataset_identifier: str - identifier of the dataset
        @returns:
            bool - True if the csv files have data
        """
        folder_path = self._get_folder_path(dataset_identifier)
        file_names = os.listdir(folder_path)
        file_paths = [os.path.join(folder_path, file_name) for file_name in file_names]

        # check if the csv file has more than 0 bytes
        return any(os.path.getsize(file_path) > 0 for file_path in file_paths)

    def read(
        self,
        dataset_identifier: str,
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
        data = self.read_all(dataset_identifier, schema=schema)
        # if the data is empty, return
        if len(data) == 0:
            return data

        # if the data is not empty,
        # check the timestamp column exists and is of type int64
        if "timestamp" not in data.columns or filter_args is False:
            return data

        return data.filter(data["timestamp"] >= start_time).filter(
            data["timestamp"] <= end_time
        )

    def read_all(
        self, dataset_identifier: str, schema: Optional[SchemaDict] = None
    ) -> pl.DataFrame:
        """
        Reads all the data from the csv files in the folder
        corresponding to the given dataset_identifier.
        @args:
            dataset_identifier: str - identifier of the dataset
        @returns:
            pl.DataFrame - data read from the csv files
        """

        folder_path = self._get_folder_path(dataset_identifier)
        file_names = os.listdir(folder_path)
        file_paths = [os.path.join(folder_path, file_name) for file_name in file_names]
        file_paths.sort()

        # print("read_all_file_paths", file_paths)
        if file_paths:
            # Read the first file to create the DataFrame
            data = pl.read_csv(file_paths[0], schema=schema)
            # Read the remaining files and append them to the DataFrame
            for file_path in file_paths[1:]:
                data = data.vstack(pl.read_csv(file_path, schema=schema))
            return data

        return pl.DataFrame([], schema=schema)

    def _get_last_file_path(self, folder_path: str) -> str:
        """
        Returns the path of the last file in the given folder_path.
        @args:
            folder_path: str - path of the folder
        @returns:
            str - path of the last file
        """

        file_names = sorted(os.listdir(folder_path))
        return os.path.join(folder_path, file_names[-1]) if file_names else ""

    @enforce_types
    def get_last_timestamp(self, dataset_identifier: str) -> Optional[int]:
        """
        Returns the last timestamp from the last csv files in the folder
        corresponding to the given dataset_identifier.
        @args:
            dataset_identifier: str - identifier of the dataset
        @returns:
            Optional[int] - last timestamp from the csv files
        """
        file_path = self._get_last_file_path(self._get_folder_path(dataset_identifier))
        if len(file_path):
            to_value = self._get_to_value(file_path)
            if to_value is not None and to_value > 0:
                return UnixTimeMs(to_value)

            # read the last record from the file
            last_file = pl.read_csv(file_path)
            return UnixTimeMs(int(last_file["timestamp"][-1]))
        return None

    def _get_last_file_row_count(self, dataset_identifier: str) -> Optional[int]:
        """
        Returns the row count of the last file for the given dataset_identifier.
        @args:
            dataset_identifier: str - The dataset identifier
        @returns:
            row_count: Optional[int] - The row count of the last file
        """

        folder_path = self._get_folder_path(dataset_identifier)
        file_names = os.listdir(folder_path)

        # Sort by file name
        file_names.sort()
        if len(file_names) == 0:
            return None

        last_file_path = os.path.join(folder_path, file_names[-1])

        # Read the last file
        last_file = pl.read_csv(last_file_path)
        row_count = last_file.shape[0]

        return row_count

    def get_first_timestamp(self, dataset_identifier: str) -> Optional[int]:
        """
        Returns the first timestamp from the first csv file in the folder
        corresponding to the given dataset_identifier.
        @args:
            dataset_identifier: str - identifier of the dataset
        @returns:
            Optional[int] - first timestamp from the csv files
        """
        folder_path = self._get_folder_path(dataset_identifier)
        file_names = os.listdir(folder_path)
        if len(file_names) == 0:
            return None

        file_path = os.path.join(folder_path, file_names[0])
        return UnixTimeMs(self._get_from_value(file_path))

    def get_folder_exists(self, dataset_identifier: str) -> bool:
        """
        Returns True if the folder corresponding to the given dataset_identifier exists.
        @args:
            dataset_identifier: str - identifier of the dataset
        @returns:
            bool - True if the folder exists
        """
        return os.path.exists(self._get_folder_path(dataset_identifier))

    def truncate(self, dataset_identifier: str):
        """
        Deletes all the csv files in the folder corresponding
        to the given dataset_identifier.
        @args:
            dataset_identifier: str - identifier of the dataset
        """
        folder_path = self._get_folder_path(dataset_identifier)
        for file_name in os.listdir(folder_path):
            os.remove(os.path.join(folder_path, file_name))
