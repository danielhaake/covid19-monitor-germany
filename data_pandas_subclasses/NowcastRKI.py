# subclassing of Pandas
# see: https://pandas.pydata.org/pandas-docs/stable/development/extending.html#override-constructor-properties
import boto3
from datetime import datetime
import logging
import os

from dotenv import load_dotenv
from io import BytesIO, StringIO

import datetime as dt
from typing import TypeVar, List

import pandas as pd
import numpy as np
import requests

from data_pandas_subclasses.CoronaBaseDateIndex import CoronaBaseDateIndexSeries, CoronaBaseDateIndexDataFrame

load_dotenv()
logging.basicConfig(level=logging.INFO)
TNum = TypeVar('TNum', int, float)


class NowcastRKISeries(CoronaBaseDateIndexSeries):
    @property
    def _constructor(self):
        return NowcastRKISeries

    @property
    def _constructor_expanddim(self):
        return NowcastRKIDataFrame


class NowcastRKIDataFrame(CoronaBaseDateIndexDataFrame):

    _filename = "nowcast_rki.csv"

    @property
    def _constructor(self):
        return NowcastRKIDataFrame

    @property
    def _constructor_sliced(self):
        return NowcastRKISeries

    @staticmethod
    def from_csv(filename: str=None,
                 s3_bucket: str=None,
                 folder_path: str=None,
                 class_name: str=None) -> 'NowcastRKIDataFrame':

        if filename is None:
            filename = NowcastRKIDataFrame._filename
        if class_name is None:
            class_name = NowcastRKIDataFrame.__name__
        df = CoronaBaseDateIndexDataFrame.from_csv(filename, s3_bucket, folder_path, class_name)

        return NowcastRKIDataFrame(df)

    @staticmethod
    def update_with_new_data_from_rki(to_csv: bool = True,
                                      s3_bucket: str = None,
                                      folder_path: str = None) -> 'NowcastRKIDataFrame':

        logging.info("START UPDATE PROCESS FOR NOWCAST RKI")

        def select_and_rename_german_columns_and_set_index_after_download_from_rki(df):

            logging.info("select and rename german columns into english of downloaded file")

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
                                          "7 day R value (Nowcast RKI)",
                                      "Untere Grenze des 95%-Prädiktionsintervalls des 7-Tage-R Wertes":
                                          "min 7 day R value (Nowcast RKI)",
                                      "Obere Grenze des 95%-Prädiktionsintervalls des 7-Tage-R Wertes":
                                          "max 7 day R value (Nowcast RKI)"
                                      }
                             ).set_index("date")

        logging.info("start download of new file from RKI")

        url = 'https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Projekte_RKI/Nowcasting_Zahlen.xlsx?__blob=publicationFile'
        response = requests.get(url)
        file_object = BytesIO(response.content)

        dateparse = lambda x: datetime.strptime(x, '%d.%m.%Y')

        nowcast_rki = NowcastRKIDataFrame(pd.read_excel(file_object,
                                                        sheet_name=1,
                                                        header=0,
                                                        thousands=".",
                                                        parse_dates=['Datum des Erkrankungsbeginns'],
                                                        date_parser=dateparse).replace(",", ".", regex=True))

        nowcast_rki = select_and_rename_german_columns_and_set_index_after_download_from_rki(nowcast_rki)

        logging.info("calculate 7 day moving mean for cases from Nowcast RKI")
        nowcast_rki.loc[:, "cases (mean of ±3 days of Nowcast RKI)"] = \
            nowcast_rki.calculate_7d_moving_mean_for_column("cases (Nowcast RKI)")

        nowcast_rki_infections = nowcast_rki.calculate_df_with_shifted_date_because_of_incubation_period()
        nowcast_rki = pd.concat([nowcast_rki, nowcast_rki_infections], axis=1)

        if to_csv:
            nowcast_rki.save_as_csv(s3_bucket=s3_bucket, folder_path=folder_path)

        logging.info("FINISHED UPDATE PROCESS FOR NOWCAST RKI")

        return nowcast_rki

    def calculate_df_with_shifted_date_because_of_incubation_period(self, incubation_period_in_days=5) \
            -> 'NowcastRKIDataFrame':

        logging.info("calculate DF with shifted date because of incubation period")

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
            "7 day R value (Nowcast RKI)":
                "7 day R value (Nowcast RKI, -5 days incubation period)",
            "min 7 day R value (Nowcast RKI)":
                "min 7 day R value (Nowcast RKI, -5 days incubation period)",
            "max 7 day R value (Nowcast RKI)":
                "max 7 day R value (Nowcast RKI, -5 days incubation period)"
        })


    def get_last_r_value(self) -> float:
        second_last_date = self.get_second_last_date()
        return self.loc[second_last_date, "7 day R value (Nowcast RKI)"]

    def get_second_last_r_value(self) -> float:
        third_last_date = self.get_third_last_date()
        return self.loc[third_last_date, "7 day R value (Nowcast RKI)"]

    def get_change_from_second_last_to_last_date_for_r_value(self) -> float:
        return self.get_last_r_value() - self.get_second_last_r_value()
