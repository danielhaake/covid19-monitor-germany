# subclassing of Pandas
# see: https://pandas.pydata.org/pandas-docs/stable/development/extending.html#override-constructor-properties
import boto3
import logging
import os

from dotenv import load_dotenv
from io import BytesIO, StringIO
from typing import List

import pandas as pd
import numpy as np
import requests

load_dotenv()
logging.basicConfig(level=logging.INFO)


class NumberPCRTestsSeries(pd.Series):
    @property
    def _constructor(self):
        return NumberPCRTestsSeries

    @property
    def _constructor_expanddim(self):
        return NumberPCRTestsDataFrame


class NumberPCRTestsDataFrame(pd.DataFrame):
    _folder_path = "data/"
    _filename = "number_of_tests_germany.csv"
    _path = _folder_path + _filename

    @property
    def _constructor(self):
        return NumberPCRTestsDataFrame

    @property
    def _constructor_sliced(self):
        return NumberPCRTestsSeries

    @staticmethod
    def from_csv(s3_bucket: str = None, path: str = None) -> 'NumberPCRTestsDataFrame':

        if (os.environ.get('S3_BUCKET') is not None) | (s3_bucket is not None):
            if s3_bucket is None:
                s3_bucket = os.environ.get('S3_BUCKET')
            s3 = boto3.client('s3')
            filename = NumberPCRTestsDataFrame._filename
            logging.info(f"start loading NumberPCRTestsDataFrame with filename {filename} "
                         f"from S3 Bucket {s3_bucket}")
            read_file = s3.get_object(Bucket=s3_bucket, Key=filename)
            number_pcr_tests = NumberPCRTestsDataFrame(pd.read_csv(read_file['Body'],
                                                                   index_col="calendar week"))
            logging.info(f"NumberPCRTestsDataFrame with filename {filename} successfully loaded "
                         f"from S3 Bucket {s3_bucket}")
        else:
            if path is None:
                if os.environ.get('FOLDER_PATH') is not None:
                    path = os.environ.get('FOLDER_PATH') + NumberPCRTestsDataFrame._filename
                else:
                    path = NumberPCRTestsDataFrame._path

            logging.info(f"start loading NumberPCRTestsDataFrame from {path}")
            number_pcr_tests = NumberPCRTestsDataFrame(pd.read_csv(path,
                                                                   index_col="calendar week"))
            logging.info(f"NumberPCRTestsDataFrame successfully loaded from {path}")

        if os.environ.get('FOLDER_PATH') is not None:
            number_pcr_tests._set_folder_path(os.environ.get('FOLDER_PATH'))

        if path is not None:
            number_pcr_tests._set_path(path)

        return number_pcr_tests

    def _set_path(self, path: str):
        self._path = path

    def _set_folder_path(self, folder_path: str):
        self._folder_path = folder_path

    @staticmethod
    def update_csv_with_new_data_from_rki(to_csv: bool = True,
                                          s3_bucket: str = None,
                                          path: str = None) -> 'NumberPCRTestsDataFrame':

        def rename_columns_german_to_english(df: NumberPCRTestsDataFrame) -> NumberPCRTestsDataFrame:
            logging.info("rename columns from german to english of downloaded file")
            return df.rename(columns={'Anzahl Testungen': 'number of tests',
                                      'Positiv getestet': 'positive tested',
                                      'Kalenderwoche': 'calendar week',
                                      'Positivenquote (%)': 'positive rate (%)',
                                      'Anzahl übermittelnder Labore': 'number of transmitting laboratories'
                                      })

        logging.info("START UPDATE PROCESS FOR NUMBER OF PCR TESTS")

        logging.info("start download of new file from RKI")
        url = 'https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Daten/Testzahlen-gesamt.xlsx?__blob=publicationFile'
        response = requests.get(url)
        file_object = BytesIO(response.content)

        # sheet name and position of header was changing over time
        number_pcr_tests = NumberPCRTestsDataFrame(pd.read_excel(file_object,
                                                                 sheet_name="1_Testzahlerfassung"))

        number_pcr_tests = rename_columns_german_to_english(number_pcr_tests)

        number_pcr_tests["negative tested"] = number_pcr_tests.calculate_number_of_negative_tests()

        number_pcr_tests["change in number of tests compared to previous week (%)"] = number_pcr_tests. \
            calculate_change_in_number_of_tests_compared_to_previous_week_in_percent()

        number_pcr_tests = number_pcr_tests._cleaning_because_of_calendar_week_column()
        number_pcr_tests = number_pcr_tests.set_index("calendar week")

        if to_csv:
            if (os.environ.get('S3_BUCKET') is not None) | (s3_bucket is not None):
                if s3_bucket is None:
                    s3_bucket = os.environ.get('S3_BUCKET')
                    csv_buffer = StringIO()
                    number_pcr_tests.to_csv(csv_buffer)
                    s3 = boto3.client('s3')
                    logging.info(f"try writing NumberPCRTestsDataFrame "
                                 f"with filename {number_pcr_tests._filename} "
                                 f"to S3 Bucket {s3_bucket}")
                    s3.put_object(Bucket=s3_bucket, Key=number_pcr_tests._filename, Body=csv_buffer.getvalue())
                    logging.info(f"updated NumberPCRTestsDataFrame "
                                 f"with filename {number_pcr_tests._filename} "
                                 f"has been written to S3 Bucket {s3_bucket}")
            else:
                if path is None:
                    if os.environ.get('FOLDER_PATH') is not None:
                        path = os.environ.get('FOLDER_PATH') + NumberPCRTestsDataFrame._filename
                        number_pcr_tests._set_folder_path(os.environ.get('FOLDER_PATH'))
                        number_pcr_tests._set_path(path)
                    else:
                        path = NumberPCRTestsDataFrame._path
                logging.info(f"try writing NumberPCRTestsDataFrame to {path}")
                number_pcr_tests.to_csv(path)
                logging.info(f"new NumberPCRTestsDataFrame has been written to {path}")

        logging.info("FINISHED UPDATE PROCESS FOR NUMBER OF PCR TESTS")

        return number_pcr_tests

    def calculate_change_in_number_of_tests_compared_to_previous_week_in_percent(self) -> List[float]:
        logging.info("calculate change in number of pcr tests compared to previous week in percent")
        return 2 * [np.nan] + \
               [(self.loc[i, "number of tests"] / self.loc[i - 1, "number of tests"]) * 100 - 100
                for i in range(2, len(self) - 1)] \
               + [np.nan]

    def calculate_number_of_negative_tests(self) -> List[int]:
        logging.info("calculate number of negative tests")
        return [self.loc[i, "number of tests"] -
                self.loc[i, "positive tested"]
                for i in range(len(self))]

    def _cleaning_because_of_calendar_week_column(self) -> 'NumberPCRTestsDataFrame':
        logging.info("cleaning because of calendar week column")
        self.loc[self.loc[:, "calendar week"] == "Bis einschließlich KW10, 2020", :"calendar week"] = "≤10"
        first_not_included_row = self.loc[self.loc[:, "calendar week"] == "Summe"].index[0]
        self.loc[:, "calendar week"] = self.loc[:, "calendar week"].astype("str")
        self.loc[:, "calendar week"] = self.loc[:, "calendar week"].str.replace("*", "", regex=True)
        calendar_week_splitted = self.loc[:, "calendar week"].str.split("/")
        self.loc[:, "week of year"] = calendar_week_splitted.str[0]
        self.loc[:, "year"] = calendar_week_splitted.str[1]
        self.loc[:, "calendar week"] = self.loc[:, "year"] + " - " + self.loc[:, "week of year"]
        return self.iloc[:first_not_included_row, :]
