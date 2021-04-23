# subclassing of Pandas
# see: https://pandas.pydata.org/pandas-docs/stable/development/extending.html#override-constructor-properties
import logging

from dotenv import load_dotenv
from typing import List

import numpy as np

from api.RKIAPI import RKIAPI
from data_pandas_subclasses.week_index_classes.CoronaBaseWeekIndex import CoronaBaseWeekIndexSeries, CoronaBaseWeekIndexDataFrame

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
    api = RKIAPI()

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

        logging.info("START UPDATE PROCESS FOR NUMBER OF PCR TESTS")
        logging.info("start download of new file from RKI")

        number_pcr_tests = NumberPCRTestsDataFrame(NumberPCRTestsDataFrame.api.number_pcr_tests())
        number_pcr_tests["negative tested"] = number_pcr_tests.calculate_number_of_negative_tests()
        number_pcr_tests["change in number of tests compared to previous week (%)"] = number_pcr_tests. \
            calculate_change_in_number_of_tests_compared_to_previous_week_in_percent()

        if to_csv:
            number_pcr_tests.save_as_csv(s3_bucket=s3_bucket, folder_path=folder_path)

        logging.info("FINISHED UPDATE PROCESS FOR NUMBER OF PCR TESTS")
        return number_pcr_tests

    def calculate_change_in_number_of_tests_compared_to_previous_week_in_percent(self) -> List[float]:
        logging.info("calculate change in number of pcr tests compared to previous week in percent")
        column_index = self.columns.get_loc("number of tests")
        return 2 * [np.nan] + \
               [(self.iloc[i, column_index] / self.iloc[i - 1, column_index]) * 100 - 100
                for i in range(2, len(self) - 1)] \
               + [np.nan]

    def calculate_number_of_negative_tests(self) -> List[int]:
        logging.info("calculate number of negative tests")
        return [self.loc[index, "number of tests"] -
                self.loc[index, "positive tested"]
                for index in self.index]
