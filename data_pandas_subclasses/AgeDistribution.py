# subclassing of Pandas
# see: https://pandas.pydata.org/pandas-docs/stable/development/extending.html#override-constructor-properties
import boto3
import logging
import os

from dotenv import load_dotenv
from io import BytesIO, StringIO

import pandas as pd
import requests

from api.RKIAPI import RKIAPI
from data_pandas_subclasses.CoronaBase import CoronaBaseSeries, CoronaBaseDataFrame

load_dotenv()
logging.basicConfig(level=logging.INFO)


class AgeDistributionSeries(CoronaBaseSeries):
    @property
    def _constructor(self):
        return AgeDistributionSeries

    @property
    def _constructor_expanddim(self):
        return AgeDistributionDataFrame


class AgeDistributionDataFrame(CoronaBaseDataFrame):

    _filename = "distribution_of_inhabitants_and_cases_and_deaths.csv"
    api = RKIAPI()

    @property
    def _constructor(self):
        return AgeDistributionDataFrame

    @property
    def _constructor_sliced(self):
        return AgeDistributionSeries

    @staticmethod
    def from_csv(filename: str=None,
                 s3_bucket: str=None,
                 folder_path: str=None,
                 class_name: str=None) -> 'AgeDistributionDataFrame':

        if filename is None:
            filename = AgeDistributionDataFrame._filename
        if class_name is None:
            class_name = AgeDistributionDataFrame.__name__
        df = CoronaBaseDataFrame.from_csv(filename, s3_bucket, folder_path, class_name)

        return AgeDistributionDataFrame(df.set_index("age group"))

    @staticmethod
    def get_age_distribution_of_cases_and_deaths(to_csv: bool = True,
                                                 s3_bucket: str=None,
                                                 folder_path: str = None) -> 'AgeDistributionDataFrame':

        def get_age_distribution_for_new_and_total_cases_and_deaths() -> 'AgeDistributionDataFrame':
            data_status_datetime_of_first_request = None
            data_status_datetime_of_last_request = None

            while ((data_status_datetime_of_first_request != data_status_datetime_of_last_request) |
                   (data_status_datetime_of_first_request is None) | (data_status_datetime_of_last_request is None)):

                inhabitants_per_age_group = AgeDistributionDataFrame.get_inhabitants_by_age_group()
                total_number_of_reported_cases_by_age_group, data_status_datetime_of_first_request = \
                    AgeDistributionDataFrame.api.total_number_of_reported_cases_by_age_group()
                new_reported_cases_by_age_group, _ = \
                    AgeDistributionDataFrame.api.new_reported_cases_by_age_group()
                total_number_of_reported_deaths_by_age_group, _ = \
                    AgeDistributionDataFrame.api.total_number_of_reported_deaths_by_age_group()
                new_reported_deaths_by_age_group, data_status_datetime_of_last_request = \
                    AgeDistributionDataFrame.api.new_reported_deaths_by_age_group()

            age_distribution = AgeDistributionDataFrame(
                pd.concat([inhabitants_per_age_group,
                           total_number_of_reported_cases_by_age_group,
                           new_reported_cases_by_age_group,
                           total_number_of_reported_deaths_by_age_group,
                           new_reported_deaths_by_age_group],
                          axis=1)) \
                .fillna(0) \
                .astype(int)
            age_distribution.index = age_distribution.index.rename('age group')
            return age_distribution

        def append_relative_values_per_n_inhabitants(age_distribution: AgeDistributionDataFrame) \
                -> 'AgeDistributionDataFrame':
            age_distribution.loc[:, "total reported cases per 100,000 inhabitants"] = \
                age_distribution.loc[:, "total reported cases"] / age_distribution.inhabitants * 100_000
            age_distribution.loc[:, "new reported cases per 100,000 inhabitants"] = \
                age_distribution.loc[:, "new reported cases"] / age_distribution.inhabitants * 100_000
            age_distribution.loc[:, "total reported deaths per 1,000,000 inhabitants"] = \
                age_distribution.loc[:, "total reported deaths"] / age_distribution.inhabitants * 1_000_000
            age_distribution.loc[:, "new reported deaths per 1,000,000 inhabitants"] = \
                age_distribution.loc[:, "new reported deaths"] / age_distribution.inhabitants * 1_000_000
            return age_distribution

        logging.info("START DOWNLOADING CASES AND DEATHS PER AGE GROUP")
        age_distribution = get_age_distribution_for_new_and_total_cases_and_deaths()
        age_distribution = append_relative_values_per_n_inhabitants(age_distribution)
        if to_csv:
            age_distribution.save_as_csv(s3_bucket=s3_bucket, folder_path=folder_path)
        logging.info("FINISHED DOWNLOADING CASES AND DEATHS PER AGE GROUP")

        return age_distribution

    @staticmethod
    def get_inhabitants_by_age_group() -> pd.DataFrame:
        return pd.DataFrame.from_dict({"A00-A04": 3961376,
                                       "A05-A14": 7429883,
                                       "A15-A34": 19117865,
                                       "A35-A59": 28919134,
                                       "A60-A79": 18057318,
                                       "A80+": 5681135},
                                      orient='index',
                                      columns=["inhabitants"])
