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
from data_pandas_subclasses.CoronaBaseWeekIndex import CoronaBaseWeekIndexDataFrame, CoronaBaseWeekIndexSeries

load_dotenv()
logging.basicConfig(level=logging.INFO)


class ClinicalAspectsSeries(CoronaBaseWeekIndexSeries):
    @property
    def _constructor(self):
        return ClinicalAspectsSeries

    @property
    def _constructor_expanddim(self):
        return ClinicalAspectsDataFrame


class ClinicalAspectsDataFrame(CoronaBaseWeekIndexDataFrame):

    _filename = "clinical_aspects.csv"
    api = RKIAPI()

    @property
    def _constructor(self):
        return ClinicalAspectsDataFrame

    @property
    def _constructor_sliced(self):
        return ClinicalAspectsSeries

    @staticmethod
    def from_csv(filename: str=None,
                 s3_bucket: str=None,
                 folder_path: str=None,
                 class_name: str=None) -> 'ClinicalAspectsDataFrame':

        if filename is None:
            filename = ClinicalAspectsDataFrame._filename
        if class_name is None:
            class_name = ClinicalAspectsDataFrame.__name__
        df = CoronaBaseWeekIndexDataFrame.from_csv(filename, s3_bucket, folder_path, class_name)

        return ClinicalAspectsDataFrame(df)

    @staticmethod
    def update_csv_with_new_data_from_rki(to_csv: bool = True,
                                          s3_bucket: str = None,
                                          folder_path: str = None):

        logging.info("START UPDATE PROCESS FOR CLINICAL ASPECTS")
        logging.info("start downloading file from RKI")

        clinical_aspects = ClinicalAspectsDataFrame(ClinicalAspectsDataFrame.api.clinical_aspects())
        if to_csv:
            clinical_aspects.save_as_csv(s3_bucket=s3_bucket, folder_path=folder_path)

        logging.info("FINISHED UPDATE PROCESS FOR CLINICAL ASPECTS")
        return clinical_aspects
