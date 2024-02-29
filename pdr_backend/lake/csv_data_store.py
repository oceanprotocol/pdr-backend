import os
from typing import List, Optional
import polars as pl

from polars.type_aliases import SchemaDict


class CSVDataStore:
    def __init__(self, base_path: str):
        self.base_path = base_path

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

    def _fill_with_zero(self, number: int, length: int = 10) -> str:
        """
        Fills the given number with zeros to make it 10 digits long.
        @args:
            number: int - number to fill with zeros
        """
        number_str = str(number)
        return f"{(length - len(number_str)) * '0'}{number_str}"

    def _create_file_name(
        self, dataset_identifier: str, start_time: int, end_time: int, row_count: int
    ) -> str:
        """
        Creates a file name using the given dataset_identifier,
        start_time, end_time, and row_count.
        @args:
            dataset_identifier: str - identifier of the dataset
            start_time: int - start time of the data TIMESTAMP
            end_time: int - end time of the data TIMESTAMP
            row_count: int - number of rows in the data
        """
        start_time_str = self._fill_with_zero(start_time)
        end_time_str = self._fill_with_zero(end_time)

        return f"{dataset_identifier}_from_{start_time_str}_to_{end_time_str}_{row_count}.csv"

    def _create_file_path(
        self, dataset_identifier: str, start_time: int, end_time: int, row_count: int
    ) -> str:
        """
        Creates the file path for the given dataset_identifier,
        start_time, end_time, and row_count.
        @args:
            dataset_identifier: str - identifier of the dataset
            start_time: str - start time of the data
            end_time: str - end time of the data
            row_count: int - number of rows in the data
        """

        file_name = self._create_file_name(
            dataset_identifier, start_time, end_time, row_count
        )
        folder_path = self._get_folder_path(dataset_identifier)
        return os.path.join(folder_path, file_name)

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

        last_file_row_count = self._get_last_file_row_count(dataset_identifier)
        if last_file_row_count is not None:
            if last_file_row_count < 1000:
                remaining_rows = 1000 - last_file_row_count

                # get the first remaining_rows rows
                if len(data) < remaining_rows:
                    remaining_rows = len(data)

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
                    dataset_identifier, t_start_time, t_end_time, len(last_file_data)
                )

                print("new_file_path", new_file_path)
                os.rename(last_file_path, new_file_path)

                data = data.slice(remaining_rows, len(data) - remaining_rows)

        chunks = [
            data.slice(i, min(1000, len(data) - i)) for i in range(0, len(data), 1000)
        ]

        for i, chunk in enumerate(chunks):
            start_time = int(chunk["timestamp"][0])
            end_time = int(chunk["timestamp"][-1])
            file_path = self._create_file_path(
                dataset_identifier, start_time, end_time, len(chunk)
            )
            chunk.write_csv(file_path)

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

    def _get_file_paths(
        self, folder_path: str, start_time: str, end_time: str
    ) -> List[str]:
        """
        Returns a list of file paths in the given folder_path
        that contain the given start_time and end_time.
        @args:
            folder_path: str - path of the folder
            start_time: str - start time of the data
            end_time: str - end time of the data
        @returns:
            List[str] - list of file paths
        """

        file_names = os.listdir(folder_path)
        file_paths = [os.path.join(folder_path, file_name) for file_name in file_names]

        # find files which has a higher start time and lower end time
        print("file_paths_aaaa", file_paths)
        file_paths = [
            file_path
            for file_path in file_paths
            # firstly, take the filename from the path (/path/to/file.csv -> file.csv)
            # then, split the filename by "_" and take the 4th and 5th elements
            # then, convert them to int and check if they are in the range
            if int(file_path.split("/")[-1].split("_")[2]) >= int(start_time)
            and int(file_path.split("/")[-1].split("_")[4]) <= int(end_time)
        ]

        return file_paths

    def read(
        self,
        dataset_identifier: str,
        start_time: str,
        end_time: str,
        schema: Optional[SchemaDict] = None,
    ) -> pl.DataFrame:
        """
        Reads the data from the csv file in the folder
        corresponding to the given dataset_identifier,
        start_time, and end_time.
        @args:
            dataset_identifier: str - identifier of the dataset
            start_time: str - start time of the data
            end_time: str - end time of the data
        @returns:
            pl.DataFrame - data read from the csv file
        """
        data = self.read_all(dataset_identifier, schema=schema)
        # if the data is empty, return
        if len(data) == 0:
            return data

        # if the data is not empty,
        # check the timestamp column exists and is of type int64
        if "timestamp" not in data.columns:
            return data

        return data.filter(data["timestamp"] >= int(start_time)).filter(
            data["timestamp"] <= int(end_time)
        )
        # return pl.read_csv(file_paths[0]) if file_paths else pl.DataFrame()

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

        return pl.DataFrame()

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

    def get_last_timestamp(self, dataset_identifier: str) -> Optional[int]:
        """
        Returns the last timestamp from the csv files in the folder
        corresponding to the given dataset_identifier.
        @args:
            dataset_identifier: str - identifier of the dataset
        @returns:
            Optional[int] - last timestamp from the csv files
        """
        folder_path = self._get_folder_path(dataset_identifier)
        last_file_path = self._get_last_file_path(folder_path)
        if len(last_file_path):
            return int(last_file_path.split("_")[3])

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

        # parse the row count from the file name
        row_count = int(last_file_path.split("_")[-1].split(".")[0])
        return row_count
