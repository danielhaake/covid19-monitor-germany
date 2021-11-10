# subclassing of Pandas
# see: https://pandas.pydata.org/pandas-docs/stable/development/extending.html#override-constructor-properties
import logging
from typing import List

import numpy as np
from dotenv import load_dotenv

from api.RKIAPI import RKIAPI
from data_pandas_subclasses.week_index_classes.CoronaBaseWeekIndex import CoronaBaseWeekIndexDataFrame, CoronaBaseWeekIndexSeries

load_dotenv()
logging.basicConfig(level=logging.INFO)


class MedianAndMeanAgesSeries(CoronaBaseWeekIndexSeries):
    @property
    def _constructor(self):
        return MedianAndMeanAgesSeries

    @property
    def _constructor_expanddim(self):
        return MedianAndMeanAgesDataFrame


class MedianAndMeanAgesDataFrame(CoronaBaseWeekIndexDataFrame):

    _filename = "median_and_mean_ages.csv"
    api = RKIAPI()

    @property
    def _constructor(self):
        return MedianAndMeanAgesDataFrame

    @property
    def _constructor_sliced(self):
        return MedianAndMeanAgesSeries

    @staticmethod
    def from_csv(filename: str=None,
                 s3_bucket: str=None,
                 folder_path: str=None,
                 class_name: str=None) -> 'MedianAndMeanAgesDataFrame':

        if filename is None:
            filename = MedianAndMeanAgesDataFrame._filename
        if class_name is None:
            class_name = MedianAndMeanAgesDataFrame.__name__
        df = CoronaBaseWeekIndexDataFrame.from_csv(filename, s3_bucket, folder_path, class_name)

        return MedianAndMeanAgesDataFrame(df)

    @staticmethod
    def update_csv_with_new_data_from_rki(to_csv: bool = True,
                                          s3_bucket: str = None,
                                          folder_path: str = None):

        logging.info("START UPDATE PROCESS FOR MEDIAN AND MEAN AGES")
        logging.info("start downloading file from RKI")

        median_and_mean_ages = MedianAndMeanAgesDataFrame(MedianAndMeanAgesDataFrame.api.
                                                          median_and_mean_age_for_cases_hospitalization_its_and_death())
        if to_csv:
            median_and_mean_ages.save_as_csv(s3_bucket=s3_bucket, folder_path=folder_path)

        logging.info("FINISHED UPDATE PROCESS FOR MEDIAN AND MEAN AGES")
        return median_and_mean_ages

