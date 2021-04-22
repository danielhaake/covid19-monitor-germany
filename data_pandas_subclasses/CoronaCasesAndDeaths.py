# subclassing of Pandas
# see: https://pandas.pydata.org/pandas-docs/stable/development/extending.html#override-constructor-properties
import logging

from datetime import datetime
from dotenv import load_dotenv
from typing import List, TypeVar

import datetime as dt
import pandas as pd
import numpy as np

from api.RKIAPI import RKIAPI
from data_pandas_subclasses.CoronaBaseDateIndex import CoronaBaseDateIndexSeries, CoronaBaseDateIndexDataFrame

load_dotenv()
logging.basicConfig(level=logging.INFO)
TNum = TypeVar('TNum', int, float)


class CoronaCasesAndDeathsSeries(CoronaBaseDateIndexSeries):
    @property
    def _constructor(self):
        return CoronaCasesAndDeathsSeries

    @property
    def _constructor_expanddim(self):
        return CoronaCasesAndDeathsDataFrame


class CoronaCasesAndDeathsDataFrame(CoronaBaseDateIndexDataFrame):
    _filename = "corona_cases_and_deaths.csv"
    _inhabitants_germany = 83_166_711
    api = RKIAPI()

    @property
    def _constructor(self):
        return CoronaCasesAndDeathsDataFrame

    @property
    def _constructor_sliced(self):
        return CoronaCasesAndDeathsSeries

    @staticmethod
    def from_csv(filename: str = None,
                 s3_bucket: str = None,
                 folder_path: str = None,
                 class_name: str = None) -> 'CoronaCasesAndDeathsDataFrame':

        if filename is None:
            filename = CoronaCasesAndDeathsDataFrame._filename
        if class_name is None:
            class_name = CoronaCasesAndDeathsDataFrame.__name__
        df = CoronaBaseDateIndexDataFrame.from_csv(filename, s3_bucket, folder_path, class_name)

        return CoronaCasesAndDeathsDataFrame(df)

    @staticmethod
    def update_csv_with_data_from_rki_api(s3_bucket: str = None, folder_path: str = None) -> None:
        logging.info("START UPDATE PROCESS FOR CORONA CASES AND DEATHS")
        corona_cases_and_deaths = CoronaCasesAndDeathsDataFrame.from_csv(folder_path=folder_path)
        logging.info("initial loading of CSV finished")
        corona_cases_and_deaths.update_with_new_data_from_rki_api(to_csv=True,
                                                                  s3_bucket=s3_bucket,
                                                                  folder_path=folder_path)
        logging.info("FINISHED UPDATE PROCESS FOR CORONA CASES AND DEATHS")

    def update_with_new_data_from_rki_api(self,
                                          to_csv: bool = True,
                                          s3_bucket: str = None,
                                          folder_path: str = None) -> 'CoronaCasesAndDeathsDataFrame':

        def update_self_with_new_data(df: CoronaCasesAndDeathsDataFrame,
                                      updates_df: pd.DataFrame) -> CoronaCasesAndDeathsDataFrame:
            df = df.drop(columns=updates_df.columns)
            df = df.merge(updates_df, how='outer', left_index=True, right_index=True)
            return df

        logging.info("start update with new data from RKI API")
        datetime_of_first_request = None
        datetime_of_last_request = None

        retries = 0
        max_retries = 5

        while (retries < max_retries) & \
              ((datetime_of_first_request != datetime_of_last_request) |
               (datetime_of_first_request is None) | (datetime_of_last_request is None)):
            daily_figures = self.api.figures_of_last_day()
            datetime_of_first_request = daily_figures["reporting date"]
            cases_and_deaths_by_reference_and_reporting_date, datetime_of_last_request = \
                self.api.cases_and_deaths_by_reference_and_reporting_date()
            retries += 1

        self = update_self_with_new_data(self, cases_and_deaths_by_reference_and_reporting_date)
        logging.info("new and total cases and deaths by reporting and reference date were added")

        self._upsert_cases_and_deaths_for_date(rki_reporting_date=daily_figures["reporting date"],
                                               new_reported_cases=daily_figures["new reported cases"],
                                               new_reported_deaths=daily_figures["new reported deaths"],
                                               cases_cumulative=daily_figures["cases cumulative"],
                                               deaths_cumulative=daily_figures["deaths cumulative"],
                                               to_csv=to_csv,
                                               s3_bucket=s3_bucket,
                                               folder_path=folder_path)

        logging.info("finished update with new data from RKI API")
        return self

    def upsert_cases_and_deaths_for_date(self,
                                         rki_reporting_date: datetime,
                                         new_reported_cases: int,
                                         new_reported_deaths: int,
                                         cases_cumulative: int = None,
                                         deaths_cumulative: int = None,
                                         to_csv: bool = True,
                                         s3_bucket: str = None,
                                         folder_path: str = None) -> 'CoronaCasesAndDeathsDataFrame':
        self_copy = self.copy(deep=True)
        self_copy._upsert_cases_and_deaths_for_date(rki_reporting_date=rki_reporting_date,
                                                    new_reported_cases=new_reported_cases,
                                                    new_reported_deaths=new_reported_deaths,
                                                    cases_cumulative=cases_cumulative,
                                                    deaths_cumulative=deaths_cumulative,
                                                    to_csv=to_csv,
                                                    s3_bucket=s3_bucket,
                                                    folder_path=folder_path)
        return self_copy

    def _upsert_cases_and_deaths_for_date(self,
                                          rki_reporting_date: datetime,
                                          new_reported_cases: int,
                                          new_reported_deaths: int,
                                          cases_cumulative: int = None,
                                          deaths_cumulative: int = None,
                                          to_csv: bool = True,
                                          s3_bucket: str = None,
                                          folder_path: str = None) -> None:

        date = rki_reporting_date - pd.DateOffset(1)
        date_minus_1d = date - pd.DateOffset(1)

        if cases_cumulative is None:
            cases_cumulative = self.loc[date_minus_1d, "cases cumulative"] + new_reported_cases
        if deaths_cumulative is None:
            deaths_cumulative = self.loc[date_minus_1d, "deaths cumulative"] + new_reported_deaths
        cfr = np.round(deaths_cumulative / cases_cumulative, 6)
        non_deceased_reported_cases = cases_cumulative - deaths_cumulative

        self.loc[date, "RKI reporting date"] = rki_reporting_date
        self.loc[date, "cases cumulative"] = cases_cumulative
        self.loc[date, "deaths cumulative"] = deaths_cumulative
        self.loc[date, "cases"] = new_reported_cases
        self.loc[date, "deaths"] = new_reported_deaths
        self.loc[date, "case fatility rate (CFR)"] = cfr
        self.loc[date, "non-deceased reported cases"] = non_deceased_reported_cases

        logging.info("new cases and deaths for date were added")

        self._upsert_statistics()

        if to_csv:
            self.save_as_csv(s3_bucket=s3_bucket, folder_path=folder_path)

    def upsert_statistics(self) -> 'CoronaCasesAndDeathsDataFrame':
        self_copy = self.copy(deep=True)
        self_copy._upsert_statistics()
        return self_copy

    def _upsert_statistics(self) -> None:
        self._calculate_7d_moving_mean_columns()
        self._calculate_r_value_and_daily_increase_columns()
        self._calculate_last_7_day_columns()
        self._calculate_7_day_incidence_and_deaths_columns()
        self._calculate_last_365_day_columns()

    def _calculate_7d_moving_mean_columns(self) -> None:
        self.loc[:, "cases (mean of ±3 days)"] = self.calculate_7d_moving_mean_for_column("cases")
        self.loc[:, "deaths (mean of ±3 days)"] = self.calculate_7d_moving_mean_for_column("deaths")
        self.loc[:, "cases (mean of ±3 days) by reference date (start of illness, alternatively reporting date)"] = \
            self.calculate_7d_moving_mean_for_column(
                "cases by reference date (start of illness, alternatively reporting date)")
        self.loc[:,
        "deaths (mean of ±3 days) by reference date (start of illness, alternatively reporting date)"] = \
            self.calculate_7d_moving_mean_for_column(
                "deaths by reference date (start of illness, alternatively reporting date)")
        self.loc[:, "cases (mean of ±3 days) by reporting date"] = \
            self.calculate_7d_moving_mean_for_column("cases by reporting date")
        self.loc[:, "deaths (mean of ±3 days) by reporting date"] = \
            self.calculate_7d_moving_mean_for_column("deaths by reporting date")

    def _calculate_r_value_and_daily_increase_columns(self) -> None:
        self.loc[:, "R value by cases (mean of ±3 days)"] = self.calculate_r_value_by_moving_mean_cases()
        self.loc[:, "daily proportionate increase of cases (mean of ±3 days)"] = self. \
            calculate_daily_proportionate_increase_for("cases (mean of ±3 days)")

    def _calculate_last_7_day_columns(self) -> None:
        self.loc[:, "cases last 7 days"] = self.calculate_sum_last_7_days_for("cases")
        self.loc[:, "deaths last 7 days"] = self.calculate_sum_last_7_days_for("deaths")

    def _calculate_last_365_day_columns(self) -> None:
        self.loc[:, "cases last 365 days"] = self.calculate_sum_last_365_days_for("cases")
        self.loc[:, "deaths last 365 days"] = self.calculate_sum_last_365_days_for("deaths")

    def _calculate_7_day_incidence_and_deaths_columns(self) -> None:
        self.loc[:, "7 day incidence per 100,000 inhabitants"] = self.calculate_7_day_incidence_for_column("cases")
        self.loc[:, "7 day incidence (by cases (mean of ±3 days)) per 100,000 inhabitants"] = \
            self.calculate_7_day_incidence_for_column("cases (mean of ±3 days)")
        self.loc[:, "7 day incidence per 100,000 inhabitants by reporting date (RKI version)"] = \
            self.calculate_7_day_incidence_for_column("cases by reporting date")
        self.loc[:,
        "7 day incidence (by cases (mean of ±3 days)) per 100,000 inhabitants by reporting date (RKI version)"] = \
            self.calculate_7_day_incidence_for_column("cases (mean of ±3 days) by reporting date")
        self.loc[:, "7 day deaths per 1,000,000 inhabitants"] = self.calculate_7_day_incidence_for_column("deaths")
        self.loc[:, "7 day deaths (by cases (mean of ±3 days)) per 1,000,000 inhabitants"] = \
            self.calculate_7_day_incidence_for_column("deaths (mean of ±3 days)")

    def calculate_r_value_by_moving_mean_cases(self) -> List[float]:
        moving_mean_cases_column_name = "cases (mean of ±3 days)"

        cases_sum_7d_to_4d_before = self.calculate_sum_7d_to_4d_before_for(moving_mean_cases_column_name)
        cases_sum_3d_to_0d_before = self.calculate_sum_3d_to_0d_before_for(moving_mean_cases_column_name)

        return [cases_sum_3d_to_0d_before[i] / cases_sum_7d_to_4d_before[i]
                if cases_sum_7d_to_4d_before[i] != 0
                else np.nan
                for i in range(len(cases_sum_3d_to_0d_before))]

    def calculate_daily_proportionate_increase_for(self, column_name: str) -> List[float]:
        return [(self.loc[date, column_name]) / (self.loc[date - pd.DateOffset(1), column_name])
                if (date - pd.DateOffset(1)) in self.index
                else np.nan
                for date
                in self.index]

    def calculate_7_day_incidence_for_column(self, column_name: str) -> List[float]:
        inhabitants = self._inhabitants_germany
        per_n_inhabitants = 100_000
        if "deaths" in column_name:
            per_n_inhabitants = 1_000_000
        return list(np.array(self.calculate_sum_last_7_days_for(column_name)) / inhabitants * per_n_inhabitants)

    def last_rki_reporting_date(self) -> dt.datetime:
        return self.loc[:, "RKI reporting date"].max()

    def last_reported_cases(self) -> int:
        last_date = self.last_date()
        return self.loc[last_date, "cases"]

    def second_last_reported_cases(self) -> int:
        second_last_date = self.second_last_date()
        return self.loc[second_last_date, "cases"]

    def change_from_second_last_to_last_date_for_reported_cases(self) -> int:
        return self.last_reported_cases() - self.second_last_reported_cases()

    def last_mean_cases(self) -> float:
        last_date_for_mean_values = self.last_date_for_mean_values()
        return self.loc[last_date_for_mean_values, "cases (mean of ±3 days)"]

    def second_last_mean_cases(self) -> float:
        second_last_date_for_mean_values = self.second_last_date_for_mean_values()
        return self.loc[second_last_date_for_mean_values, "cases (mean of ±3 days)"]

    def change_from_second_last_to_last_date_for_mean_cases(self) -> float:
        return self.last_mean_cases() - self.second_last_mean_cases()

    def last_cases_cumulative(self) -> int:
        last_date = self.last_date()
        return self.loc[last_date, "cases cumulative"]

    def last_reported_deaths(self) -> int:
        last_date = self.last_date()
        return self.loc[last_date, "deaths"]

    def second_last_reported_deaths(self) -> int:
        second_last_date = self.second_last_date()
        return self.loc[second_last_date, "deaths"]

    def change_from_second_last_to_last_date_for_reported_deaths(self) -> int:
        return self.last_reported_deaths() - self.second_last_reported_deaths()

    def last_mean_deaths(self) -> float:
        last_date_for_mean_values = self.last_date_for_mean_values()
        return self.loc[last_date_for_mean_values, "deaths (mean of ±3 days)"]

    def second_last_mean_deaths(self) -> float:
        second_last_date_for_mean_values = self.second_last_date_for_mean_values()
        return self.loc[second_last_date_for_mean_values, "deaths (mean of ±3 days)"]

    def change_from_second_last_to_last_date_for_mean_deaths(self) -> float:
        return self.last_mean_deaths() - self.second_last_mean_deaths()

    def last_deaths_cumulative(self) -> int:
        last_date = self.last_date()
        return self.loc[last_date, "deaths cumulative"]

    def last_r_value_by_mean_cases(self) -> float:
        last_date_for_mean_values = self.last_date_for_mean_values()
        return self.loc[last_date_for_mean_values, "R value by cases (mean of ±3 days)"]

    def second_last_r_value_by_mean_cases(self) -> float:
        second_last_date_for_mean_values = self.second_last_date_for_mean_values()
        return self.loc[second_last_date_for_mean_values, "R value by cases (mean of ±3 days)"]

    def change_from_second_last_to_last_date_for_r_value_by_mean_cases(self) -> float:
        return self.last_r_value_by_mean_cases() - self.second_last_r_value_by_mean_cases()

    def cases_last_7_days(self) -> int:
        last_date = self.last_date()
        return self.loc[last_date, "cases last 7 days"]

    def deaths_last_7_days(self) -> int:
        last_date = self.last_date()
        return self.loc[last_date, "deaths last 7 days"]

    def last_7_day_incidence_per_100_000_inhabitants(self) -> float:
        last_date = self.last_date()
        return self.loc[last_date, "7 day incidence per 100,000 inhabitants"]

    def second_last_7_day_incidence_per_100_000_inhabitants(self) -> float:
        second_last_date = self.second_last_date()
        return self.loc[second_last_date, "7 day incidence per 100,000 inhabitants"]

    def change_from_second_last_to_last_date_for_7_day_incidence_per_100_000_inhabitants(self) -> float:
        return self.last_7_day_incidence_per_100_000_inhabitants() - \
               self.second_last_7_day_incidence_per_100_000_inhabitants()

    def last_7_day_incidence_per_100_000_inhabitants_by_reporting_date(self) -> float:
        last_date = self.last_date()
        return self.loc[last_date, "7 day incidence per 100,000 inhabitants by reporting date (RKI version)"]

    def second_last_7_day_incidence_per_100_000_inhabitants_by_reporting_date(self) -> float:
        second_last_date = self.second_last_date()
        return self.loc[second_last_date, "7 day incidence per 100,000 inhabitants by reporting date (RKI version)"]

    def change_from_second_last_to_last_date_for_7_day_incidence_per_100_000_inhabitants_by_reporting_date(self) \
            -> float:
        return self.last_7_day_incidence_per_100_000_inhabitants() - \
               self.second_last_7_day_incidence_per_100_000_inhabitants()

    def last_7_day_deaths_per_1_000_000_inhabitants(self) -> float:
        last_date = self.last_date()
        return self.loc[last_date, "7 day deaths per 1,000,000 inhabitants"]

    def second_last_7_day_deaths_per_1_000_000_inhabitants(self) -> float:
        second_last_date = self.second_last_date()
        return self.loc[second_last_date, "7 day deaths per 1,000,000 inhabitants"]

    def change_from_second_last_to_last_date_for_7_day_deaths_per_1_000_000_inhabitants(self) -> float:
        return self.last_7_day_deaths_per_1_000_000_inhabitants() - \
               self.second_last_7_day_deaths_per_1_000_000_inhabitants()

    def last_7_day_incidence_by_mean_cases_per_100_000_inhabitants(self) -> float:
        last_date_for_mean_values = self.last_date_for_mean_values()
        return self.loc[last_date_for_mean_values,
                        "7 day incidence (by cases (mean of ±3 days)) per 100,000 inhabitants"]

    def second_last_7_day_incidence_by_mean_cases_per_100_000_inhabitants(self) -> float:
        second_last_date_for_mean_values = self.second_last_date_for_mean_values()
        return self.loc[second_last_date_for_mean_values,
                        "7 day incidence (by cases (mean of ±3 days)) per 100,000 inhabitants"]

    def change_from_second_last_to_last_date_for_7_day_incidence_by_mean_cases_per_100_000_inhabitants(self) \
            -> float:
        return self.last_7_day_incidence_by_mean_cases_per_100_000_inhabitants() - \
               self.second_last_7_day_incidence_by_mean_cases_per_100_000_inhabitants()

    def last_7_day_deaths_by_mean_cases_per_1_000_000_inhabitants(self) -> float:
        last_date_for_mean_values = self.last_date_for_mean_values()
        return self.loc[last_date_for_mean_values,
                        "7 day deaths (by cases (mean of ±3 days)) per 1,000,000 inhabitants"]

    def second_last_7_day_deaths_by_mean_cases_per_1_000_000_inhabitants(self) -> float:
        second_last_date_for_mean_values = self.second_last_date_for_mean_values()
        return self.loc[second_last_date_for_mean_values,
                        "7 day deaths (by cases (mean of ±3 days)) per 1,000,000 inhabitants"]

    def change_from_second_last_to_last_date_for_7_day_deaths_by_mean_cases_per_1_000_000_inhabitants(self) \
            -> float:
        return self.last_7_day_deaths_by_mean_cases_per_1_000_000_inhabitants() - \
               self.second_last_7_day_deaths_by_mean_cases_per_1_000_000_inhabitants()

    def cases_last_365_days(self) -> int:
        last_date = self.last_date()
        return self.loc[last_date, "cases last 365 days"]

    def cases_last_365_days_of_second_last_date(self) -> int:
        second_last_date = self.second_last_date()
        return self.loc[second_last_date, "cases last 365 days"]

    def change_from_second_last_to_last_date_for_cases_last_365_days(self) -> int:
        return self.cases_last_365_days() - self.cases_last_365_days_of_second_last_date()

    def deaths_last_365_days(self) -> int:
        last_date = self.last_date()
        return self.loc[last_date, "deaths last 365 days"]

    def deaths_last_365_days_of_second_last_date(self) -> int:
        second_last_date = self.second_last_date()
        return self.loc[second_last_date, "deaths last 365 days"]

    def change_from_second_last_to_last_date_for_deaths_last_365_days(self) -> int:
        return self.deaths_last_365_days() - self.deaths_last_365_days_of_second_last_date()
