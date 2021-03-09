import datetime as dt
import pandas as pd

from data_pandas_subclasses.CoronaBase import CoronaBaseSeries, CoronaBaseDataFrame


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
                 s3_bucket: str=None,
                 folder_path: str=None,
                 class_name: str=None) -> 'CoronaBaseDateIndexDataFrame':
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

    def get_last_date(self) -> dt.datetime:
        return self.index.max()

    def get_second_last_date(self) -> dt.datetime:
        return self.get_last_date() - pd.DateOffset(1)

    def get_third_last_date(self) -> dt.datetime:
        return self.get_last_date() - pd.DateOffset(2)

    def get_last_date_for_mean_values(self) -> dt.datetime:
        return self.get_last_date() - pd.DateOffset(3)

    def get_second_last_date_for_mean_values(self) -> dt.datetime:
        return self.get_last_date_for_mean_values() - pd.DateOffset(1)

    def get_third_last_date_for_mean_values(self) -> dt.datetime:
        return self.get_last_date_for_mean_values() - pd.DateOffset(2)
