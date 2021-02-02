# subclassing of Pandas
# see: https://pandas.pydata.org/pandas-docs/stable/development/extending.html#override-constructor-properties

from io import BytesIO

import datetime as dt
from typing import TypeVar, List

import pandas as pd
import numpy as np
import requests

TNum = TypeVar('TNum', int, float)


class NowcastRKISeries(pd.Series):
    @property
    def _constructor(self):
        return NowcastRKISeries

    @property
    def _constructor_expanddim(self):
        return NowcastRKIDataFrame


class NowcastRKIDataFrame(pd.DataFrame):
    _path = "data/nowcast_rki.csv"

    @property
    def _constructor(self):
        return NowcastRKIDataFrame

    @property
    def _constructor_sliced(self):
        return NowcastRKISeries

    def _set_path(self, path: str):
        self._path = path

    @staticmethod
    def from_csv(path: str=None) -> 'NowcastRKIDataFrame':
        if path is None:
            path = NowcastRKIDataFrame._path
        nowcast_rki = NowcastRKIDataFrame(pd.read_csv(path,
                                                      parse_dates=['date'],
                                                      index_col="date"))
        if path is not None:
            nowcast_rki._set_path(path)

        return nowcast_rki


    @staticmethod
    def update_with_new_data_from_rki(to_csv: bool=True, path: str=None) -> 'NowcastRKIDataFrame':

        def select_and_rename_german_columns_and_set_index_after_download_from_rki(df):
            df = df.loc[:, ["Datum des Erkrankungsbeginns",
                            "Punktschätzer der Anzahl Neuerkrankungen",
                            "Untere Grenze des 95%-Prädiktionsintervalls der Anzahl Neuerkrankungen",
                            "Obere Grenze des 95%-Prädiktionsintervalls der Anzahl Neuerkrankungen",
                            "Punktschätzer des 7-Tage-R Wertes",
                            "Untere Grenze des 95%-Prädiktionsintervalls des 7-Tage-R Wertes",
                            "Obere Grenze des 95%-Prädiktionsintervalls des 7-Tage-R Wertes"]
                 ]
            df.loc[:, "Datum des Erkrankungsbeginns"] = pd.to_datetime(df.loc[:, "Datum des Erkrankungsbeginns"])
            return df.rename(columns={"Datum des Erkrankungsbeginns": "date",
                                      "Punktschätzer der Anzahl Neuerkrankungen":
                                          "cases (Nowcast RKI)",
                                      "Untere Grenze des 95%-Prädiktionsintervalls der Anzahl Neuerkrankungen":
                                          "min cases (Nowcast RKI)",
                                      "Obere Grenze des 95%-Prädiktionsintervalls der Anzahl Neuerkrankungen":
                                          "max cases (Nowcast RKI)",
                                      "Punktschätzer des 7-Tage-R Wertes":
                                          "7 day R0 (Nowcast RKI)",
                                      "Untere Grenze des 95%-Prädiktionsintervalls des 7-Tage-R Wertes":
                                          "min 7 day R0 (Nowcast RKI)",
                                      "Obere Grenze des 95%-Prädiktionsintervalls des 7-Tage-R Wertes":
                                          "max 7 day R0 (Nowcast RKI)"
                                      }
                             ).set_index("date")


        url = 'https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Projekte_RKI/Nowcasting_Zahlen.xlsx?__blob=publicationFile'
        response = requests.get(url)
        file_object = BytesIO(response.content)

        nowcast_rki = NowcastRKIDataFrame(pd.read_excel(file_object,
                                                        sheet_name=1,
                                                        header=0))

        nowcast_rki = select_and_rename_german_columns_and_set_index_after_download_from_rki(nowcast_rki)
        nowcast_rki.loc[:, "cases (mean of ±3 days of Nowcast RKI)"] = \
            nowcast_rki.calculate_7d_moving_mean_for_column("cases (Nowcast RKI)")

        nowcast_rki_infections = nowcast_rki.calculate_df_with_shifted_date_because_of_incubation_period()
        nowcast_rki = pd.concat([nowcast_rki, nowcast_rki_infections], axis=1)

        if to_csv:
            if path is None:
                path = NowcastRKIDataFrame._path
            nowcast_rki.to_csv(path)

        return nowcast_rki


    def calculate_df_with_shifted_date_because_of_incubation_period(self, incubation_period_in_days=5) \
            -> 'NowcastRKIDataFrame':

        self_copy = self.copy(deep=True)

        self_copy = self_copy.set_index(self_copy.index - pd.DateOffset(incubation_period_in_days))
        return self_copy.rename(columns={
            "cases (Nowcast RKI)":
                "Infections (based on 7 day nowcast of RKI - 5 days regarding incubation period)",
            "cases (mean of ±3 days of Nowcast RKI)":
                "Infections (mean of ±3 days based on 7 day nowcast of RKI - 5 days regarding incubation period)",
            "min cases (Nowcast RKI)":
                "min Infections (based on 7 day nowcast of RKI - 5 days regarding incubation period)",
            "max cases (Nowcast RKI)":
                "max Infections (based on 7 day nowcast of RKI - 5 days regarding incubation period)",
            "7 day R0 (Nowcast RKI)":
                "7 day R0 (Nowcast RKI, -5 days incubation period)",
            "min 7 day R0 (Nowcast RKI)":
                "min 7 day R0 (Nowcast RKI, -5 days incubation period)",
            "max 7 day R0 (Nowcast RKI)":
                "max 7 day R0 (Nowcast RKI, -5 days incubation period)"
        })

    def calculate_7d_moving_mean_for_column(self, column_name: str) -> List[TNum]:
        return [self._calculate_sum_or_mean_for_period_of_days_and_column_and_specific_day(column_name,
                                                                                           date,
                                                                                           days_backwards=3,
                                                                                           period_in_days=7,
                                                                                           type="mean")
                for date
                in self.index]

    def _calculate_sum_or_mean_for_period_of_days_and_column_and_specific_day(self,
                                                                              column_name: str,
                                                                              date: dt.datetime,
                                                                              days_backwards: int,
                                                                              period_in_days: int,
                                                                              type: str="sum") -> TNum:
        date_range = pd.date_range(date - pd.DateOffset(days_backwards), periods=period_in_days)
        cases = self.loc[self.index.isin(date_range), column_name]
        if len(cases) == period_in_days & cases.notna().sum() == period_in_days:
            if type == "sum":
                return cases.sum()
            elif type == "mean":
                return cases.mean()
        return np.nan

    def get_last_date(self) -> dt.datetime:
        return self.index.max()

    def get_second_last_date(self) -> dt.datetime:
        return self.get_last_date() - pd.DateOffset(1)

    def get_third_last_date(self) -> dt.datetime:
        return self.get_last_date() - pd.DateOffset(2)

    def get_last_date_for_mean_values(self) -> dt.datetime:
        return self.index.max() - pd.DateOffset(3)

    def get_second_last_date_for_mean_values(self) -> dt.datetime:
        return self.get_last_date_for_mean_values() - pd.DateOffset(1)

    def get_third_last_date_for_mean_values(self) -> dt.datetime:
        return self.get_last_date_for_mean_values() - pd.DateOffset(2)

    def get_last_r0(self) -> float:
        second_last_date = self.get_second_last_date()
        return self.loc[second_last_date, "7 day R0 (Nowcast RKI)"]

    def get_second_last_r0(self) -> float:
        third_last_date = self.get_third_last_date()
        return self.loc[third_last_date, "7 day R0 (Nowcast RKI)"]

    def get_change_from_second_last_to_last_date_for_r0(self) -> float:
        return self.get_last_r0() - self.get_second_last_r0()
