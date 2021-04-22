import datetime as dt
from datetime import datetime
from typing import List, TypeVar

import pandas as pd
import numpy as np

from data_pandas_subclasses.CoronaBase import CoronaBaseSeries, CoronaBaseDataFrame

TNum = TypeVar('TNum', int, float)


class CoronaBaseDateIndexSeries(CoronaBaseSeries):
    @property
    def _constructor(self):
        return CoronaBaseDateIndexSeries

    @property
    def _constructor_expanddim(self):
        return CoronaBaseDateIndexDataFrame


class CoronaBaseDateIndexDataFrame(CoronaBaseDataFrame):

    @property
    def _constructor(self):
        return CoronaBaseDateIndexDataFrame

    @property
    def _constructor_sliced(self):
        return CoronaBaseDateIndexSeries

    @staticmethod
    def from_csv(filename: str,
                 s3_bucket: str = None,
                 folder_path: str = None,
                 class_name: str = None) -> 'CoronaBaseDateIndexDataFrame':
        if class_name is None:
            class_name = 'CoronaBaseDateIndexDataFrame'
        df = CoronaBaseDataFrame.from_csv(filename, s3_bucket, folder_path, class_name)
        df = CoronaBaseDateIndexDataFrame.set_date_columns_to_type_datetime(df)

        return CoronaBaseDateIndexDataFrame(df.set_index("date"))

    @staticmethod
    def set_date_columns_to_type_datetime(df):
        for column in ["date", "RKI reporting date"]:
            if column in df.columns:
                df.loc[:, column] = pd.to_datetime(df.loc[:, column])
        return df

    def calculate_7d_moving_mean_for_column(self, column_name: str) -> List[TNum]:
        return [self._calculate_sum_or_mean_for(column_name,
                                                date,
                                                days_backwards=3,
                                                period_in_days=7,
                                                type="mean")
                for date
                in self.index]

    def calculate_sum_7d_to_4d_before_for(self, column_name: str) -> List[TNum]:
        return [self._calculate_sum_or_mean_for(column_name,
                                                date,
                                                days_backwards=7,
                                                period_in_days=4)
                for date
                in self.index]

    def calculate_sum_3d_to_0d_before_for(self, column_name: str) -> List[TNum]:
        return [self._calculate_sum_or_mean_for(column_name,
                                                date,
                                                days_backwards=3,
                                                period_in_days=4)
                for date
                in self.index]

    def _calculate_sum_or_mean_for(self,
                                   column_name: str,
                                   date: datetime,
                                   days_backwards: int,
                                   period_in_days: int,
                                   data_for_all_days_needed: bool = True,
                                   type: str = "sum") -> TNum:
        date_range = pd.date_range(date - pd.DateOffset(days_backwards), periods=period_in_days)
        cases = self.loc[self.index.isin(date_range), column_name]
        if (data_for_all_days_needed & (len(cases) == period_in_days) & (cases.notna().sum() == period_in_days))\
           | (not data_for_all_days_needed):
            if type == "sum":
                return cases.sum()
            elif type == "mean":
                return cases.mean()
        return np.nan

    def calculate_sum_last_7_days_for(self, column_name: str) -> List[TNum]:
        return [self._calculate_sum_or_mean_for(column_name,
                                                date,
                                                days_backwards=6,
                                                period_in_days=7)
                for date
                in self.index]

    def last_date(self) -> dt.datetime:
        return self.index.max()

    def second_last_date(self) -> dt.datetime:
        return self.last_date() - pd.DateOffset(1)

    def third_last_date(self) -> dt.datetime:
        return self.last_date() - pd.DateOffset(2)

    def last_date_for_mean_values(self) -> dt.datetime:
        return self.last_date() - pd.DateOffset(3)

    def second_last_date_for_mean_values(self) -> dt.datetime:
        return self.last_date_for_mean_values() - pd.DateOffset(1)

    def third_last_date_for_mean_values(self) -> dt.datetime:
        return self.last_date_for_mean_values() - pd.DateOffset(2)
