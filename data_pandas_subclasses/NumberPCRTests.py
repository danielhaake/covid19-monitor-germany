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

from data_pandas_subclasses.CoronaBaseWeekIndex import CoronaBaseWeekIndexSeries, CoronaBaseWeekIndexDataFrame

load_dotenv()
logging.basicConfig(level=logging.INFO)


class NumberPCRTestsSeries(CoronaBaseWeekIndexSeries):
    @property
    def _constructor(self):
        return NumberPCRTestsSeries

    @property
    def _constructor_expanddim(self):
        return NumberPCRTestsDataFrame


class NumberPCRTestsDataFrame(CoronaBaseWeekIndexDataFrame):

    _filename = "number_of_tests_germany.csv"

    @property
    def _constructor(self):
        return NumberPCRTestsDataFrame

    @property
    def _constructor_sliced(self):
        return NumberPCRTestsSeries

    @staticmethod
    def from_csv(filename: str=None,
                 s3_bucket: str=None,
                 folder_path: str=None,
                 class_name: str=None) -> 'NumberPCRTestsDataFrame':

        if filename is None:
            filename = NumberPCRTestsDataFrame._filename
        if class_name is None:
            class_name = NumberPCRTestsDataFrame.__name__
        df = CoronaBaseWeekIndexDataFrame.from_csv(filename, s3_bucket, folder_path, class_name)

        return NumberPCRTestsDataFrame(df)

    @staticmethod
    def update_csv_with_new_data_from_rki(to_csv: bool = True,
                                          s3_bucket: str = None,
                                          folder_path: str = None) -> 'NumberPCRTestsDataFrame':

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
            number_pcr_tests.save_as_csv(s3_bucket=s3_bucket, folder_path=folder_path)

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
