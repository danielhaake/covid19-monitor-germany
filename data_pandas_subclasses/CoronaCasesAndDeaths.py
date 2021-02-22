# subclassing of Pandas
# see: https://pandas.pydata.org/pandas-docs/stable/development/extending.html#override-constructor-properties
import logging
import os

from datetime import datetime
from dotenv import load_dotenv
from io import BytesIO
from typing import List, TypeVar, Tuple

import datetime as dt
import pandas as pd
import numpy as np
import requests

load_dotenv()
logging.basicConfig(level=logging.INFO)
TNum = TypeVar('TNum', int, float)


class CoronaCasesAndDeathsSeries(pd.Series):
    @property
    def _constructor(self):
        return CoronaCasesAndDeathsSeries

    @property
    def _constructor_expanddim(self):
        return CoronaCasesAndDeathsDataFrame


class CoronaCasesAndDeathsDataFrame(pd.DataFrame):

    _folder_path = "data/"
    _filename = "corona_cases_and_deaths.csv"
    _path = _folder_path + _filename

    @property
    def _constructor(self):
        return CoronaCasesAndDeathsDataFrame

    @property
    def _constructor_sliced(self):
        return CoronaCasesAndDeathsSeries

    def _set_path(self, path: str):
        self._path = path

    def _set_folder_path(self, folder_path: str):
        self._folder_path = folder_path

    @staticmethod
    def from_csv(path: str = None) -> 'CoronaCasesAndDeathsDataFrame':

        if path is None:
            if os.environ.get('FOLDER_PATH') is not None:
                path = os.environ.get('FOLDER_PATH') + CoronaCasesAndDeathsDataFrame._filename
            else:
                path = CoronaCasesAndDeathsDataFrame._path

        logging.info(f"start loading CoronaCasesAndDeathsDataFrame from {path}")
        corona_cases_and_deaths = CoronaCasesAndDeathsDataFrame(pd.read_csv(path,
                                                                            parse_dates=['date', 'RKI reporting date'],
                                                                            index_col="date"))

        if os.environ.get('FOLDER_PATH') is not None:
            corona_cases_and_deaths._set_folder_path(os.environ.get('FOLDER_PATH'))

        if path is not None:
            corona_cases_and_deaths._set_path(path)

        logging.info(f"CoronaCasesAndDeathsDataFrame successfully loaded from {path}")
        return corona_cases_and_deaths

    @staticmethod
    def update_csv_with_data_from_rki_api(path: str = None):
        logging.info("START UPDATE PROCESS FOR CORONA CASES AND DEATHS")
        corona_cases_and_deaths = CoronaCasesAndDeathsDataFrame.from_csv(path)
        logging.info("initial loading of CSV finished")
        corona_cases_and_deaths._update_with_new_data_from_rki_api(to_csv=True, path=path)
        logging.info("FINISHED UPDATE PROCESS FOR CORONA CASES AND DEATHS")

    @staticmethod
    def initial_loading_from_rki() -> 'CoronaCasesAndDeathsDataFrame':
        url = 'https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Daten/Fallzahlen_Kum_Tab.xlsx?__blob=publicationFile'
        response = requests.get(url)

        file_object = BytesIO(response.content)
        rki_cases_and_deaths = CoronaCasesAndDeathsDataFrame(pd.read_excel(file_object,
                                                                           sheet_name="Fälle-Todesfälle-gesamt",
                                                                           header=2))

        rki_cases_and_deaths = rki_cases_and_deaths.dropna(how="all", axis=1)
        rki_cases_and_deaths = rki_cases_and_deaths.dropna(how="all", axis=0)

        rki_cases_and_deaths.Berichtsdatum = [rki_cases_and_deaths.Berichtsdatum[i]
                                              if isinstance(rki_cases_and_deaths.Berichtsdatum[i], datetime)
                                              else pd.to_datetime(rki_cases_and_deaths.Berichtsdatum[i], dayfirst=True)
                                              for i in range(len(rki_cases_and_deaths))]

        rki_cases_and_deaths = rki_cases_and_deaths. \
            rename(columns={'Berichtsdatum': 'RKI reporting date',
                            'Differenz Vortag Fälle': 'cases',
                            'Differenz Vortag Todesfälle': 'deaths',
                            'Anzahl COVID-19-Fälle': 'cases cumulative',
                            'Todesfälle': 'deaths cumulative',
                            'Fall-Verstorbenen-Anteil': 'case fatility rate (CFR)',
                            'Fälle ohne Todesfälle': 'non-deceased reported cases'})

        rki_cases_and_deaths.loc[:, 'RKI reporting date'] = \
            pd.to_datetime(rki_cases_and_deaths.loc[:, 'RKI reporting date'])

        # "RKI reporting date" is from beginning of the day (00:00),
        # so the cases and deaths are reported one day earlier to the RKI
        rki_cases_and_deaths.loc[:, 'date'] = rki_cases_and_deaths.loc[:, 'RKI reporting date'] - pd.DateOffset(1)
        rki_cases_and_deaths = rki_cases_and_deaths.sort_values("date")
        rki_cases_and_deaths = rki_cases_and_deaths.set_index("date")

        return rki_cases_and_deaths


    def update_with_new_data_from_rki_api(self, to_csv: bool = True, path: str = None) \
            -> 'CoronaCasesAndDeathsDataFrame':
        self_copy = self.copy(deep=True)
        self_copy._update_with_new_data_from_rki_api(to_csv=to_csv, path=path)
        return self_copy

    def _update_with_new_data_from_rki_api(self, to_csv: bool = True, path: str = None) -> None:

        # it is possible that we call the methods while the dataset is updated
        # then we could have different dates for reported cases and deaths
        # to have the the same date we rerun the methods until we have the same dates
        logging.info("start update with new data from RKI API")
        while True:

            # get last reported figures
            new_reported_cases, new_reported_cases_date = self.get_new_reported_cases_from_rki_api()
            cases_cumulative, _ = self.get_total_number_of_reported_cases_from_rki_api()
            deaths_cumulative, _ = self.get_total_number_of_reported_deaths_from_rki_api()
            new_reported_deaths, _ = self.get_new_reported_deaths_from_rki_api()

            # get cases and deaths by reference and reporting date
            overall_cases_by_reference_date, _ = self.get_total_number_of_cases_by_reference_date_from_rki_api()
            overall_cases_by_reporting_date, _ = self.get_total_number_of_cases_by_reporting_date_from_rki_api()
            new_reported_cases_by_reference_date, _ = self.get_new_reported_cases_by_reference_date_from_rki_api()
            new_reported_cases_by_reporting_date, _ = self.get_new_reported_cases_by_reporting_date_from_rki_api()

            overall_deaths_by_reference_date, _ = self.get_total_number_of_deaths_by_reference_date_from_rki_api()
            overall_deaths_by_reporting_date, _ = self.get_total_number_of_deaths_by_reporting_date_from_rki_api()
            new_reported_deaths_by_reference_date, _ = self.get_new_reported_deaths_by_reference_date_from_rki_api()
            new_reported_deaths_by_reporting_date, _ = self.get_new_reported_deaths_by_reporting_date_from_rki_api()

            new_reported_cases_with_known_start_of_illness, _ = \
                self.get_new_reported_cases_by_reference_date_with_known_start_of_illness_from_rki_api()
            new_reported_cases_with_unknown_start_of_illness, _ = \
                self.get_new_reported_cases_by_reference_date_with_unknown_start_of_illness_from_rki_api()
            new_reported_deaths_with_known_start_of_illness, _ = \
                self.get_new_reported_deaths_by_reference_date_with_known_start_of_illness_from_rki_api()
            new_reported_deaths_with_unknown_start_of_illness, _ = \
                self.get_new_reported_deaths_by_reference_date_with_unknown_start_of_illness_from_rki_api()

            overall_cases_with_known_start_of_illness, _ = \
                self.get_total_number_of_cases_by_reference_date_with_known_start_of_illness_from_rki_api()
            overall_cases_with_unknown_start_of_illness, _ = \
                self.get_total_number_of_cases_by_reference_date_with_unknown_start_of_illness_from_rki_api()
            overall_deaths_with_known_start_of_illness, _ = \
                self.get_total_number_of_deaths_by_reference_date_with_known_start_of_illness_from_rki_api()
            overall_deaths_with_unknown_start_of_illness, overall_deaths_with_unknown_start_of_illness_date = \
                self.get_total_number_of_deaths_by_reference_date_with_unknown_start_of_illness_from_rki_api()

            if new_reported_cases_date == overall_deaths_with_unknown_start_of_illness_date:
                break
        rki_reporting_date = new_reported_cases_date

        self = self.drop(columns=['cases by reference date (start of illness, alternatively reporting date)',
                                  'cases by reporting date',
                                  'deaths by reference date (start of illness, alternatively reporting date)',
                                  'deaths by reporting date',
                                  'new reported cases by reference date (start of illness, alternatively reporting date)',
                                  'new reported cases by reporting date',
                                  'new reported deaths by reference date (start of illness, alternatively reporting date)',
                                  'new reported deaths by reporting date',
                                  'cases with reported start of illness',
                                  'cases with unknown start of illness (reporting date)',
                                  'deaths with reported start of illness',
                                  'deaths with unknown start of illness (reporting date)',
                                  'new reported cases with known start of illness',
                                  'new reported cases with unknown start of illness (reporting date)',
                                  'new reported deaths with known start of illness',
                                  'new reported deaths with unknown start of illness (reporting date)'
                                  ])

        self = CoronaCasesAndDeathsDataFrame(pd.concat([self,
                                                        overall_cases_by_reference_date,
                                                        overall_cases_by_reporting_date,
                                                        new_reported_cases_by_reference_date,
                                                        new_reported_cases_by_reporting_date,
                                                        overall_deaths_by_reference_date,
                                                        overall_deaths_by_reporting_date,
                                                        new_reported_deaths_by_reference_date,
                                                        new_reported_deaths_by_reporting_date,
                                                        new_reported_cases_with_known_start_of_illness,
                                                        new_reported_cases_with_unknown_start_of_illness,
                                                        new_reported_deaths_with_known_start_of_illness,
                                                        new_reported_deaths_with_unknown_start_of_illness,
                                                        overall_cases_with_known_start_of_illness,
                                                        overall_cases_with_unknown_start_of_illness,
                                                        overall_deaths_with_known_start_of_illness,
                                                        overall_deaths_with_unknown_start_of_illness],
                                                       axis=1))

        logging.info("new and total cases and deaths by reporting and reference date were added")

        self.index = self.index.rename("date")

        self._upsert_cases_and_deaths_for_date(rki_reporting_date=rki_reporting_date,
                                               new_reported_cases=new_reported_cases,
                                               new_reported_deaths=new_reported_deaths,
                                               cases_cumulative=cases_cumulative,
                                               deaths_cumulative=deaths_cumulative,
                                               to_csv=to_csv,
                                               path=path)
        logging.info("finished update with new data from RKI API")

    def upsert_statistics(self, inhabitants: int = 83166711) -> 'CoronaCasesAndDeathsDataFrame':
        self_copy = self.copy(deep=True)
        self_copy._upsert_statistics(inhabitants)
        return self_copy

    def _upsert_statistics(self, inhabitants: int = 83166711) -> None:
        self.loc[:, "cases (mean of ±3 days)"] = self.calculate_7d_moving_mean_for_column("cases")
        self.loc[:, "deaths (mean of ±3 days)"] = self.calculate_7d_moving_mean_for_column("deaths")

        self.loc[:, "cases (mean of ±3 days) by reference date (start of illness, alternatively reporting date)"] = \
            self.calculate_7d_moving_mean_for_column("cases by reference date (start of illness, alternatively reporting date)")

        self.loc[:,
        "deaths (mean of ±3 days) by reference date (start of illness, alternatively reporting date)"] = \
            self.calculate_7d_moving_mean_for_column("deaths by reference date (start of illness, alternatively reporting date)")

        self.loc[:, "cases (mean of ±3 days) by reporting date"] = \
            self.calculate_7d_moving_mean_for_column("cases by reporting date")

        self.loc[:, "deaths (mean of ±3 days) by reporting date"] = \
            self.calculate_7d_moving_mean_for_column("deaths by reporting date")

        self.loc[:, "R value by cases (mean of ±3 days)"] = self.calculate_r_value_by_moving_mean_cases()

        self.loc[:, "daily proportionate increase of cases (mean of ±3 days)"] = self. \
            calculate_daily_proportionate_increase_for("cases (mean of ±3 days)")

        self.loc[:, "cases last 7 days"] = self.calculate_sum_last_7_days_for_column("cases")
        self.loc[:, "deaths last 7 days"] = self.calculate_sum_last_7_days_for_column("deaths")

        self.loc[:, "7 day incidence per 100,000 inhabitants"] = self. \
            calculate_7_day_incidence_for_column("cases", inhabitants)

        self.loc[:, "7 day incidence (by cases (mean of ±3 days)) per 100,000 inhabitants"] = self. \
            calculate_7_day_incidence_for_column("cases (mean of ±3 days)", inhabitants)

        self.loc[:, "7 day incidence per 100,000 inhabitants by reporting date (RKI version)"] = self. \
            calculate_7_day_incidence_for_column("cases by reporting date", inhabitants)

        self.loc[:, "7 day incidence (by cases (mean of ±3 days)) per 100,000 inhabitants by reporting date (RKI version)"] = self. \
            calculate_7_day_incidence_for_column("cases (mean of ±3 days) by reporting date", inhabitants)

        self.loc[:, "7 day deaths per 1,000,000 inhabitants"] = self. \
            calculate_7_day_incidence_for_column("deaths", inhabitants)

        self.loc[:, "7 day deaths (by cases (mean of ±3 days)) per 1,000,000 inhabitants"] = self. \
            calculate_7_day_incidence_for_column("deaths (mean of ±3 days)", inhabitants)



    def calculate_7d_moving_mean_for_column(self, column_name: str) -> List[TNum]:
        return [self._calculate_sum_or_mean_for_period_of_days_and_column_and_specific_day(column_name,
                                                                                           date,
                                                                                           days_backwards=3,
                                                                                           period_in_days=7,
                                                                                           type="mean")
                for date
                in self.index]

    def calculate_sum_7d_to_4d_before_for(self, column_name: str) -> List[TNum]:
        return [self._calculate_sum_or_mean_for_period_of_days_and_column_and_specific_day(column_name,
                                                                                           date,
                                                                                           days_backwards=7,
                                                                                           period_in_days=4)
                for date
                in self.index]

    def calculate_sum_3d_to_0d_before_for(self, column_name: str) -> List[TNum]:
        return [self._calculate_sum_or_mean_for_period_of_days_and_column_and_specific_day(column_name,
                                                                                           date,
                                                                                           days_backwards=3,
                                                                                           period_in_days=4)
                for date
                in self.index]

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

    def calculate_sum_last_7_days_for_column(self, column_name: str) -> List[TNum]:
        return [self._calculate_sum_or_mean_for_period_of_days_and_column_and_specific_day(column_name,
                                                                                           date,
                                                                                           days_backwards=6,
                                                                                           period_in_days=7)
                for date
                in self.index]

    def calculate_7_day_incidence_for_column(self, column_name: str, inhabitants: int) -> List[float]:
        per_n_inhabitants = 100_000
        if "deaths" in column_name:
            per_n_inhabitants = 1_000_000
        return list(np.array(self.calculate_sum_last_7_days_for_column(column_name)) / inhabitants * per_n_inhabitants)

    def _calculate_sum_or_mean_for_period_of_days_and_column_and_specific_day(self,
                                                                              column_name: str,
                                                                              date: datetime,
                                                                              days_backwards: int,
                                                                              period_in_days: int,
                                                                              type: str = "sum") -> TNum:
        date_range = pd.date_range(date - pd.DateOffset(days_backwards), periods=period_in_days)
        cases = self.loc[self.index.isin(date_range), column_name]
        if len(cases) == period_in_days & cases.notna().sum() == period_in_days:
            if type == "sum":
                return cases.sum()
            elif type == "mean":
                return cases.mean()
        return np.nan

    def upsert_cases_and_deaths_for_date(self,
                                         rki_reporting_date: datetime,
                                         new_reported_cases: int,
                                         new_reported_deaths: int,
                                         cases_cumulative: int = None,
                                         deaths_cumulative: int = None,
                                         to_csv: bool = True,
                                         path: str = None) -> 'CoronaCasesAndDeathsDataFrame':
        self_copy = self.copy(deep=True)
        self_copy._upsert_cases_and_deaths_for_date(rki_reporting_date=rki_reporting_date,
                                                    new_reported_cases=new_reported_cases,
                                                    new_reported_deaths=new_reported_deaths,
                                                    cases_cumulative=cases_cumulative,
                                                    deaths_cumulative=deaths_cumulative,
                                                    to_csv=to_csv,
                                                    path=path)
        return self_copy

    def _upsert_cases_and_deaths_for_date(self,
                                          rki_reporting_date: datetime,
                                          new_reported_cases: int,
                                          new_reported_deaths: int,
                                          cases_cumulative: int = None,
                                          deaths_cumulative: int = None,
                                          to_csv: bool = True,
                                          path: str = None) -> None:

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
            if path is None:
                if os.environ.get('FOLDER_PATH') is not None:
                    path = os.environ.get('FOLDER_PATH') + CoronaCasesAndDeathsDataFrame._filename
                    self._set_folder_path(os.environ.get('FOLDER_PATH'))
                    self._set_path(path)
                else:
                    path = CoronaCasesAndDeathsDataFrame._path
            logging.info(f"try writing CoronaCasesAndDeathsDataFrame to {path}")
            self.to_csv(path)
            logging.info(f"updated CoronaCasesAndDeathsDataFrame has been written to {path}")


    @staticmethod
    def get_new_reported_cases_from_rki_api() -> Tuple[int, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerFall IN(1,-1)' \
              '&objectIds=' \
              '&time=' \
              '&resultType=standard' \
              '&outFields=AnzahlFall,Datenstand' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&outStatistics=[' \
                '{"statisticType":"sum","onStatisticField":"AnzahlFall","outStatisticFieldName":"cases"},' \
                '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='
        response = requests.get(url)
        data = response.json()
        new_reported_cases = int(data["features"][0]["attributes"]["cases"])
        datetime_str_german = data["features"][0]["attributes"]["date"]
        date = pd.to_datetime(datetime_str_german.split(",")[0], dayfirst=True)

        return new_reported_cases, date

    @staticmethod
    def get_total_number_of_reported_cases_from_rki_api() -> Tuple[int, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerFall IN(1,0)' \
              '&objectIds=' \
              '&time=' \
              '&resultType=standard' \
              '&outFields=AnzahlFall,Datenstand' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&outStatistics=[' \
                '{"statisticType":"sum","onStatisticField":"AnzahlFall","outStatisticFieldName":"cases"},' \
                '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='
        response = requests.get(url)
        data = response.json()
        total_number_of_reported_cases = int(data["features"][0]["attributes"]["cases"])
        datetime_str_german = data["features"][0]["attributes"]["date"]
        date = pd.to_datetime(datetime_str_german.split(",")[0], dayfirst=True)

        return total_number_of_reported_cases, date

    @staticmethod
    def get_new_reported_deaths_from_rki_api() -> Tuple[int, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerTodesfall IN(1,-1)' \
              '&objectIds=' \
              '&time=' \
              '&resultType=standard' \
              '&outFields=AnzahlTodesfall,Datenstand' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&outStatistics=[' \
                '{"statisticType":"sum","onStatisticField":"AnzahlTodesfall","outStatisticFieldName":"deaths"},' \
                '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='
        response = requests.get(url)
        data = response.json()
        new_reported_deaths = int(data["features"][0]["attributes"]["deaths"])
        datetime_str_german = data["features"][0]["attributes"]["date"]
        date = pd.to_datetime(datetime_str_german.split(",")[0], dayfirst=True)

        return new_reported_deaths, date

    @staticmethod
    def get_total_number_of_reported_deaths_from_rki_api() -> Tuple[int, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerTodesfall IN(1,0)' \
              '&objectIds=' \
              '&time=' \
              '&resultType=standard' \
              '&outFields=AnzahlFall,Datenstand' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&outStatistics=[' \
                '{"statisticType":"sum","onStatisticField":"AnzahlFall","outStatisticFieldName":"deaths"},' \
                '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='
        response = requests.get(url)
        data = response.json()
        total_number_of_reported_deaths = int(data["features"][0]["attributes"]["deaths"])
        datetime_str_german = data["features"][0]["attributes"]["date"]
        date = pd.to_datetime(datetime_str_german.split(",")[0], dayfirst=True)

        return total_number_of_reported_deaths, date

    @staticmethod
    def get_total_number_of_cases_by_reference_date_from_rki_api() -> Tuple[pd.Series, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerFall IN(1,0)' \
              '&objectIds=&' \
              'time=' \
              '&resultType=standard' \
              '&outFields=AnzahlFall,Refdatum' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Refdatum' \
              '&outStatistics=[' \
                '{"statisticType":"sum","onStatisticField":"AnzahlFall","outStatisticFieldName":"cases"},' \
                '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='

        response = requests.get(url)
        data = response.json()
        overall_cases_by_reference_date = pd.json_normalize(data["features"])
        overall_cases_by_reference_date = overall_cases_by_reference_date.rename(
            columns={'attributes.cases': 'cases by reference date (start of illness, alternatively reporting date)',
                     'attributes.Refdatum': 'reference date',
                     'attributes.date': 'data status'})

        overall_cases_by_reference_date.loc[:, 'reference date'] = \
            pd.to_datetime(overall_cases_by_reference_date.loc[:, 'reference date'], unit='ms')
        overall_cases_by_reference_date = overall_cases_by_reference_date.set_index("reference date")
        overall_cases_by_reference_date = overall_cases_by_reference_date.sort_index()

        datetime_of_data_status_str_german = overall_cases_by_reference_date.iloc[0, :]["data status"]
        datetime_of_data_status = pd.to_datetime(datetime_of_data_status_str_german.split(",")[0], dayfirst=True)

        return overall_cases_by_reference_date.loc[:, 'cases by reference date ' \
                                                      '(start of illness, alternatively reporting date)'], \
               datetime_of_data_status

    @staticmethod
    def get_total_number_of_cases_by_reference_date_with_known_start_of_illness_from_rki_api() \
            -> Tuple[pd.Series, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerFall IN(1,0) AND IstErkrankungsbeginn=1' \
              '&objectIds=&' \
              'time=' \
              '&resultType=standard' \
              '&outFields=AnzahlFall,Refdatum' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Refdatum' \
              '&outStatistics=[' \
              '{"statisticType":"sum","onStatisticField":"AnzahlFall","outStatisticFieldName":"cases"},' \
              '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='

        response = requests.get(url)
        data = response.json()
        overall_cases_with_reported_start_of_illness = pd.json_normalize(data["features"])
        overall_cases_with_reported_start_of_illness = \
            overall_cases_with_reported_start_of_illness.rename(
                columns={'attributes.cases': 'cases with reported start of illness',
                         'attributes.Refdatum': 'reference date',
                         'attributes.date': 'data status'})

        overall_cases_with_reported_start_of_illness.loc[:, 'reference date'] = \
            pd.to_datetime(overall_cases_with_reported_start_of_illness.loc[:, 'reference date'], unit='ms')
        overall_cases_with_reported_start_of_illness = \
            overall_cases_with_reported_start_of_illness.set_index("reference date")
        overall_cases_with_reported_start_of_illness = overall_cases_with_reported_start_of_illness.sort_index()

        datetime_of_data_status_str_german = overall_cases_with_reported_start_of_illness.iloc[0, :]["data status"]
        datetime_of_data_status = pd.to_datetime(datetime_of_data_status_str_german.split(",")[0], dayfirst=True)

        return overall_cases_with_reported_start_of_illness.loc[:, 'cases with reported start of illness'], \
               datetime_of_data_status

    @staticmethod
    def get_total_number_of_cases_by_reference_date_with_unknown_start_of_illness_from_rki_api() \
            -> Tuple[pd.Series, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerFall IN(1,0) AND IstErkrankungsbeginn=0' \
              '&objectIds=&' \
              'time=' \
              '&resultType=standard' \
              '&outFields=AnzahlFall,Refdatum' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Refdatum' \
              '&outStatistics=[' \
              '{"statisticType":"sum","onStatisticField":"AnzahlFall","outStatisticFieldName":"cases"},' \
              '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='

        response = requests.get(url)
        data = response.json()
        overall_cases_with_unknown_start_of_illness = pd.json_normalize(data["features"])
        overall_cases_with_unknown_start_of_illness = \
            overall_cases_with_unknown_start_of_illness.rename(
                columns={'attributes.cases': 'cases with unknown start of illness (reporting date)',
                         'attributes.Refdatum': 'reference date',
                         'attributes.date': 'data status'})

        overall_cases_with_unknown_start_of_illness.loc[:, 'reference date'] = \
            pd.to_datetime(overall_cases_with_unknown_start_of_illness.loc[:, 'reference date'], unit='ms')
        overall_cases_with_unknown_start_of_illness = \
            overall_cases_with_unknown_start_of_illness.set_index("reference date")
        overall_cases_with_unknown_start_of_illness = overall_cases_with_unknown_start_of_illness.sort_index()

        datetime_of_data_status_str_german = overall_cases_with_unknown_start_of_illness.iloc[0, :]["data status"]
        datetime_of_data_status = pd.to_datetime(datetime_of_data_status_str_german.split(",")[0], dayfirst=True)

        return overall_cases_with_unknown_start_of_illness.loc[:, 'cases with unknown start of illness (reporting date)'], \
               datetime_of_data_status

    @staticmethod
    def get_total_number_of_cases_by_reporting_date_from_rki_api() -> Tuple[pd.Series, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerFall IN(1,0)' \
              '&objectIds=&' \
              'time=' \
              '&resultType=standard' \
              '&outFields=AnzahlFall,Meldedatum' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Meldedatum' \
              '&outStatistics=[' \
                '{"statisticType":"sum","onStatisticField":"AnzahlFall","outStatisticFieldName":"cases"},' \
                '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='

        response = requests.get(url)
        data = response.json()
        overall_cases_by_reporting_date = pd.json_normalize(data["features"])
        overall_cases_by_reporting_date = overall_cases_by_reporting_date.rename(
            columns={'attributes.cases': 'cases by reporting date',
                     'attributes.Meldedatum': 'reporting date',
                     'attributes.date': 'data status'})

        overall_cases_by_reporting_date.loc[:, 'reporting date'] = \
            pd.to_datetime(overall_cases_by_reporting_date.loc[:, 'reporting date'], unit='ms')
        overall_cases_by_reporting_date = overall_cases_by_reporting_date.set_index("reporting date")
        overall_cases_by_reporting_date = overall_cases_by_reporting_date.sort_index()

        datetime_of_data_status_str_german = overall_cases_by_reporting_date.iloc[0, :]["data status"]
        datetime_of_data_status = pd.to_datetime(datetime_of_data_status_str_german.split(",")[0], dayfirst=True)

        return overall_cases_by_reporting_date.loc[:, 'cases by reporting date'], \
               datetime_of_data_status


    @staticmethod
    def get_total_number_of_deaths_by_reference_date_from_rki_api() -> Tuple[pd.Series, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerTodesfall IN(1,0)' \
              '&objectIds=&' \
              'time=' \
              '&resultType=standard' \
              '&outFields=AnzahlTodesfall,Refdatum' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Refdatum' \
              '&outStatistics=[' \
                '{"statisticType":"sum","onStatisticField":"AnzahlTodesfall","outStatisticFieldName":"deaths"},' \
                '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='

        response = requests.get(url)
        data = response.json()
        overall_deaths_by_reference_date = pd.json_normalize(data["features"])
        overall_deaths_by_reference_date = overall_deaths_by_reference_date.rename(
            columns={'attributes.deaths': 'deaths by reference date (start of illness, alternatively reporting date)',
                     'attributes.Refdatum': 'reference date',
                     'attributes.date': 'data status'})

        overall_deaths_by_reference_date.loc[:, 'reference date'] = \
            pd.to_datetime(overall_deaths_by_reference_date.loc[:, 'reference date'], unit='ms')
        overall_deaths_by_reference_date = overall_deaths_by_reference_date.set_index("reference date")
        overall_deaths_by_reference_date = overall_deaths_by_reference_date.sort_index()

        datetime_of_data_status_str_german = overall_deaths_by_reference_date.iloc[0, :]["data status"]
        datetime_of_data_status = pd.to_datetime(datetime_of_data_status_str_german.split(",")[0], dayfirst=True)

        return overall_deaths_by_reference_date.loc[:, 'deaths by reference date ' \
                                                       '(start of illness, alternatively reporting date)'], \
               datetime_of_data_status

    @staticmethod
    def get_total_number_of_deaths_by_reference_date_with_known_start_of_illness_from_rki_api() \
            -> Tuple[pd.Series, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerTodesfall IN(1,0) AND IstErkrankungsbeginn=1' \
              '&objectIds=&' \
              'time=' \
              '&resultType=standard' \
              '&outFields=AnzahlTodesfall,Refdatum' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Refdatum' \
              '&outStatistics=[' \
              '{"statisticType":"sum","onStatisticField":"AnzahlTodesfall","outStatisticFieldName":"deaths"},' \
              '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='

        response = requests.get(url)
        data = response.json()
        overall_deaths_with_reported_start_of_illness = pd.json_normalize(data["features"])
        overall_deaths_with_reported_start_of_illness = overall_deaths_with_reported_start_of_illness.rename(
            columns={'attributes.deaths': 'deaths with reported start of illness',
                     'attributes.Refdatum': 'reference date',
                     'attributes.date': 'data status'})

        overall_deaths_with_reported_start_of_illness.loc[:, 'reference date'] = \
            pd.to_datetime(overall_deaths_with_reported_start_of_illness.loc[:, 'reference date'], unit='ms')
        overall_deaths_with_reported_start_of_illness = overall_deaths_with_reported_start_of_illness.set_index("reference date")
        overall_deaths_with_reported_start_of_illness = overall_deaths_with_reported_start_of_illness.sort_index()

        datetime_of_data_status_str_german = overall_deaths_with_reported_start_of_illness.iloc[0, :]["data status"]
        datetime_of_data_status = pd.to_datetime(datetime_of_data_status_str_german.split(",")[0], dayfirst=True)

        return overall_deaths_with_reported_start_of_illness.loc[:, 'deaths with reported start of illness'], \
               datetime_of_data_status

    @staticmethod
    def get_total_number_of_deaths_by_reference_date_with_unknown_start_of_illness_from_rki_api() \
            -> Tuple[pd.Series, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerTodesfall IN(1,0) AND IstErkrankungsbeginn=0' \
              '&objectIds=&' \
              'time=' \
              '&resultType=standard' \
              '&outFields=AnzahlTodesfall,Refdatum' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Refdatum' \
              '&outStatistics=[' \
              '{"statisticType":"sum","onStatisticField":"AnzahlTodesfall","outStatisticFieldName":"deaths"},' \
              '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='

        response = requests.get(url)
        data = response.json()
        overall_deaths_with_unknown_start_of_illness = pd.json_normalize(data["features"])
        overall_deaths_with_unknown_start_of_illness = overall_deaths_with_unknown_start_of_illness.rename(
            columns={'attributes.deaths': 'deaths with unknown start of illness (reporting date)',
                     'attributes.Refdatum': 'reference date',
                     'attributes.date': 'data status'})

        overall_deaths_with_unknown_start_of_illness.loc[:, 'reference date'] = \
            pd.to_datetime(overall_deaths_with_unknown_start_of_illness.loc[:, 'reference date'], unit='ms')
        overall_deaths_with_unknown_start_of_illness = overall_deaths_with_unknown_start_of_illness.set_index(
            "reference date")
        overall_deaths_with_unknown_start_of_illness = overall_deaths_with_unknown_start_of_illness.sort_index()

        datetime_of_data_status_str_german = overall_deaths_with_unknown_start_of_illness.iloc[0, :]["data status"]
        datetime_of_data_status = pd.to_datetime(datetime_of_data_status_str_german.split(",")[0], dayfirst=True)

        return overall_deaths_with_unknown_start_of_illness.loc[:, 'deaths with unknown start of illness' \
                                                                   ' (reporting date)'], \
               datetime_of_data_status

    @staticmethod
    def get_total_number_of_deaths_by_reporting_date_from_rki_api() -> Tuple[pd.Series, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerTodesfall IN(1,0)' \
              '&objectIds=&' \
              'time=' \
              '&resultType=standard' \
              '&outFields=AnzahlTodesfall,Meldedatum' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Meldedatum' \
              '&outStatistics=[' \
                '{"statisticType":"sum","onStatisticField":"AnzahlTodesfall","outStatisticFieldName":"deaths"},' \
                '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='

        response = requests.get(url)
        data = response.json()
        overall_deaths_by_reporting_date = pd.json_normalize(data["features"])
        overall_deaths_by_reporting_date = overall_deaths_by_reporting_date.rename(
            columns={'attributes.deaths': 'deaths by reporting date',
                     'attributes.Meldedatum': 'reporting date',
                     'attributes.date': 'data status'})

        overall_deaths_by_reporting_date.loc[:, 'reporting date'] = \
            pd.to_datetime(overall_deaths_by_reporting_date.loc[:, 'reporting date'], unit='ms')
        overall_deaths_by_reporting_date = overall_deaths_by_reporting_date.set_index("reporting date")
        overall_deaths_by_reporting_date = overall_deaths_by_reporting_date.sort_index()

        datetime_of_data_status_str_german = overall_deaths_by_reporting_date.iloc[0, :]["data status"]
        datetime_of_data_status = pd.to_datetime(datetime_of_data_status_str_german.split(",")[0], dayfirst=True)

        return overall_deaths_by_reporting_date.loc[:, 'deaths by reporting date'], \
               datetime_of_data_status

    @staticmethod
    def get_new_reported_cases_by_reference_date_from_rki_api() -> Tuple[pd.Series, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerFall IN(1,-1)' \
              '&objectIds=&' \
              'time=' \
              '&resultType=standard' \
              '&outFields=AnzahlFall,Refdatum' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Refdatum' \
              '&outStatistics=[' \
                '{"statisticType":"sum","onStatisticField":"AnzahlFall","outStatisticFieldName":"cases"},' \
                '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='

        response = requests.get(url)
        data = response.json()
        new_reported_cases_by_reference_date = pd.json_normalize(data["features"])
        new_reported_cases_by_reference_date = new_reported_cases_by_reference_date.rename(
            columns={'attributes.cases': 'new reported cases by reference date '
                                         '(start of illness, alternatively reporting date)',
                     'attributes.Refdatum': 'reference date',
                     'attributes.date': 'data status'})

        new_reported_cases_by_reference_date.loc[:, 'reference date'] = \
            pd.to_datetime(new_reported_cases_by_reference_date.loc[:, 'reference date'], unit='ms')
        new_reported_cases_by_reference_date = new_reported_cases_by_reference_date.set_index("reference date")
        new_reported_cases_by_reference_date = new_reported_cases_by_reference_date.sort_index()

        datetime_of_data_status_str_german = new_reported_cases_by_reference_date.iloc[0, :]["data status"]
        datetime_of_data_status = pd.to_datetime(datetime_of_data_status_str_german.split(",")[0], dayfirst=True)

        return new_reported_cases_by_reference_date.loc[:, 'new reported cases by reference date ' \
                                                           '(start of illness, alternatively reporting date)'], \
               datetime_of_data_status

    @staticmethod
    def get_new_reported_cases_by_reference_date_with_known_start_of_illness_from_rki_api() \
            -> Tuple[pd.Series, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerFall IN(1,-1) AND IstErkrankungsbeginn=1' \
              '&objectIds=&' \
              'time=' \
              '&resultType=standard' \
              '&outFields=AnzahlFall,Refdatum' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Refdatum' \
              '&outStatistics=[' \
              '{"statisticType":"sum","onStatisticField":"AnzahlFall","outStatisticFieldName":"cases"},' \
              '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='

        response = requests.get(url)
        data = response.json()
        new_reported_cases_with_known_start_of_illness = pd.json_normalize(data["features"])
        new_reported_cases_with_known_start_of_illness = new_reported_cases_with_known_start_of_illness.rename(
            columns={'attributes.cases': 'new reported cases with known start of illness',
                     'attributes.Refdatum': 'reference date',
                     'attributes.date': 'data status'})

        new_reported_cases_with_known_start_of_illness.loc[:, 'reference date'] = \
            pd.to_datetime(new_reported_cases_with_known_start_of_illness.loc[:, 'reference date'], unit='ms')
        new_reported_cases_with_known_start_of_illness = \
            new_reported_cases_with_known_start_of_illness.set_index("reference date")
        new_reported_cases_with_known_start_of_illness = new_reported_cases_with_known_start_of_illness.sort_index()

        datetime_of_data_status_str_german = new_reported_cases_with_known_start_of_illness.iloc[0, :]["data status"]
        datetime_of_data_status = pd.to_datetime(datetime_of_data_status_str_german.split(",")[0], dayfirst=True)

        return new_reported_cases_with_known_start_of_illness.loc[:, 'new reported cases with known start of illness'], \
               datetime_of_data_status

    @staticmethod
    def get_new_reported_cases_by_reference_date_with_unknown_start_of_illness_from_rki_api() \
            -> Tuple[pd.Series, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerFall IN(1,-1) AND IstErkrankungsbeginn=0' \
              '&objectIds=&' \
              'time=' \
              '&resultType=standard' \
              '&outFields=AnzahlFall,Refdatum' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Refdatum' \
              '&outStatistics=[' \
              '{"statisticType":"sum","onStatisticField":"AnzahlFall","outStatisticFieldName":"cases"},' \
              '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='

        response = requests.get(url)
        data = response.json()
        new_reported_cases_with_unknown_start_of_illness = pd.json_normalize(data["features"])
        new_reported_cases_with_unknown_start_of_illness = new_reported_cases_with_unknown_start_of_illness.rename(
            columns={'attributes.cases': 'new reported cases with unknown start of illness (reporting date)',
                     'attributes.Refdatum': 'reference date',
                     'attributes.date': 'data status'})

        new_reported_cases_with_unknown_start_of_illness.loc[:, 'reference date'] = \
            pd.to_datetime(new_reported_cases_with_unknown_start_of_illness.loc[:, 'reference date'], unit='ms')
        new_reported_cases_with_unknown_start_of_illness = \
            new_reported_cases_with_unknown_start_of_illness.set_index("reference date")
        new_reported_cases_with_unknown_start_of_illness = new_reported_cases_with_unknown_start_of_illness.sort_index()

        datetime_of_data_status_str_german = new_reported_cases_with_unknown_start_of_illness.iloc[0, :]["data status"]
        datetime_of_data_status = pd.to_datetime(datetime_of_data_status_str_german.split(",")[0], dayfirst=True)

        return new_reported_cases_with_unknown_start_of_illness.loc[:, 'new reported cases with unknown start of ' \
                                                                       'illness (reporting date)'], \
               datetime_of_data_status

    @staticmethod
    def get_new_reported_cases_by_reporting_date_from_rki_api() \
            -> Tuple[pd.Series, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerFall IN(1,-1)' \
              '&objectIds=&' \
              'time=' \
              '&resultType=standard' \
              '&outFields=AnzahlFall,Meldedatum' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Meldedatum' \
              '&outStatistics=[' \
                '{"statisticType":"sum","onStatisticField":"AnzahlFall","outStatisticFieldName":"cases"},' \
                '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='

        response = requests.get(url)
        data = response.json()
        new_reported_cases_by_reporting_date = pd.json_normalize(data["features"])
        new_reported_cases_by_reporting_date = new_reported_cases_by_reporting_date.rename(
            columns={'attributes.cases': 'new reported cases by reporting date',
                     'attributes.Meldedatum': 'reporting date',
                     'attributes.date': 'data status'})

        new_reported_cases_by_reporting_date.loc[:, 'reporting date'] = \
            pd.to_datetime(new_reported_cases_by_reporting_date.loc[:, 'reporting date'], unit='ms')
        new_reported_cases_by_reporting_date = new_reported_cases_by_reporting_date.set_index("reporting date")
        new_reported_cases_by_reporting_date = new_reported_cases_by_reporting_date.sort_index()

        datetime_of_data_status_str_german = new_reported_cases_by_reporting_date.iloc[0, :]["data status"]
        datetime_of_data_status = pd.to_datetime(datetime_of_data_status_str_german.split(",")[0], dayfirst=True)

        return new_reported_cases_by_reporting_date.loc[:, 'new reported cases by reporting date'], \
               datetime_of_data_status

    @staticmethod
    def get_new_reported_deaths_by_reference_date_from_rki_api() \
            -> Tuple[pd.Series, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerTodesfall IN(1,-1)' \
              '&objectIds=&' \
              'time=' \
              '&resultType=standard' \
              '&outFields=AnzahlTodesfall,Refdatum' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Refdatum' \
              '&outStatistics=[' \
                '{"statisticType":"sum","onStatisticField":"AnzahlTodesfall","outStatisticFieldName":"deaths"},' \
                '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='

        response = requests.get(url)
        data = response.json()
        new_reported_deaths_by_reference_date = pd.json_normalize(data["features"])
        new_reported_deaths_by_reference_date = new_reported_deaths_by_reference_date.rename(
            columns={'attributes.deaths': 'new reported deaths by reference date '
                                          '(start of illness, alternatively reporting date)',
                     'attributes.Refdatum': 'reference date',
                     'attributes.date': 'data status'})

        new_reported_deaths_by_reference_date.loc[:, 'reference date'] = \
            pd.to_datetime(new_reported_deaths_by_reference_date.loc[:, 'reference date'], unit='ms')
        new_reported_deaths_by_reference_date = new_reported_deaths_by_reference_date.set_index("reference date")
        new_reported_deaths_by_reference_date = new_reported_deaths_by_reference_date.sort_index()

        datetime_of_data_status_str_german = new_reported_deaths_by_reference_date.iloc[0, :]["data status"]
        datetime_of_data_status = pd.to_datetime(datetime_of_data_status_str_german.split(",")[0], dayfirst=True)

        return new_reported_deaths_by_reference_date.loc[:, 'new reported deaths by reference date ' \
                                                       '(start of illness, alternatively reporting date)'], \
               datetime_of_data_status

    @staticmethod
    def get_new_reported_deaths_by_reference_date_with_known_start_of_illness_from_rki_api() \
            -> Tuple[pd.Series, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerTodesfall IN(1,-1) AND IstErkrankungsbeginn=1' \
              '&objectIds=&' \
              'time=' \
              '&resultType=standard' \
              '&outFields=AnzahlTodesfall,Refdatum' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Refdatum' \
              '&outStatistics=[' \
              '{"statisticType":"sum","onStatisticField":"AnzahlTodesfall","outStatisticFieldName":"deaths"},' \
              '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='

        response = requests.get(url)
        data = response.json()
        new_reported_deaths_with_known_start_of_illness = pd.json_normalize(data["features"])
        new_reported_deaths_with_known_start_of_illness = new_reported_deaths_with_known_start_of_illness.rename(
            columns={'attributes.deaths': 'new reported deaths with known start of illness',
                     'attributes.Refdatum': 'reference date',
                     'attributes.date': 'data status'})

        new_reported_deaths_with_known_start_of_illness.loc[:, 'reference date'] = \
            pd.to_datetime(new_reported_deaths_with_known_start_of_illness.loc[:, 'reference date'], unit='ms')
        new_reported_deaths_with_known_start_of_illness = \
            new_reported_deaths_with_known_start_of_illness.set_index("reference date")
        new_reported_deaths_with_known_start_of_illness = new_reported_deaths_with_known_start_of_illness.sort_index()

        datetime_of_data_status_str_german = new_reported_deaths_with_known_start_of_illness.iloc[0, :]["data status"]
        datetime_of_data_status = pd.to_datetime(datetime_of_data_status_str_german.split(",")[0], dayfirst=True)

        return new_reported_deaths_with_known_start_of_illness.loc[:, 'new reported deaths with known start of illness'], \
               datetime_of_data_status

    @staticmethod
    def get_new_reported_deaths_by_reference_date_with_unknown_start_of_illness_from_rki_api() \
            -> Tuple[pd.Series, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerTodesfall IN(1,-1) AND IstErkrankungsbeginn=0' \
              '&objectIds=&' \
              'time=' \
              '&resultType=standard' \
              '&outFields=AnzahlTodesfall,Refdatum' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Refdatum' \
              '&outStatistics=[' \
              '{"statisticType":"sum","onStatisticField":"AnzahlTodesfall","outStatisticFieldName":"deaths"},' \
              '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='

        response = requests.get(url)
        data = response.json()
        new_reported_deaths_with_unknown_start_of_illness = pd.json_normalize(data["features"])
        new_reported_deaths_with_unknown_start_of_illness = new_reported_deaths_with_unknown_start_of_illness.rename(
            columns={'attributes.deaths': 'new reported deaths with unknown start of illness (reporting date)',
                     'attributes.Refdatum': 'reference date',
                     'attributes.date': 'data status'})

        new_reported_deaths_with_unknown_start_of_illness.loc[:, 'reference date'] = \
            pd.to_datetime(new_reported_deaths_with_unknown_start_of_illness.loc[:, 'reference date'], unit='ms')
        new_reported_deaths_with_unknown_start_of_illness = \
            new_reported_deaths_with_unknown_start_of_illness.set_index("reference date")
        new_reported_deaths_with_unknown_start_of_illness = \
            new_reported_deaths_with_unknown_start_of_illness.sort_index()

        datetime_of_data_status_str_german = new_reported_deaths_with_unknown_start_of_illness.iloc[0, :]["data status"]
        datetime_of_data_status = pd.to_datetime(datetime_of_data_status_str_german.split(",")[0], dayfirst=True)

        return new_reported_deaths_with_unknown_start_of_illness.loc[:, 'new reported deaths with unknown start of ' \
                                                                      'illness (reporting date)'], \
               datetime_of_data_status

    @staticmethod
    def get_new_reported_deaths_by_reporting_date_from_rki_api() -> Tuple[pd.Series, dt.datetime]:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerTodesfall IN(1,-1)' \
              '&objectIds=&' \
              'time=' \
              '&resultType=standard' \
              '&outFields=AnzahlTodesfall,Meldedatum' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Meldedatum' \
              '&outStatistics=[' \
                '{"statisticType":"sum","onStatisticField":"AnzahlTodesfall","outStatisticFieldName":"deaths"},' \
                '{"statisticType":"max","onStatisticField":"Datenstand","outStatisticFieldName":"date"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='

        response = requests.get(url)
        data = response.json()
        overall_deaths_by_reporting_date = pd.json_normalize(data["features"])
        overall_deaths_by_reporting_date = overall_deaths_by_reporting_date.rename(
            columns={'attributes.deaths': 'new reported deaths by reporting date',
                     'attributes.Meldedatum': 'reporting date',
                     'attributes.date': 'data status'})

        overall_deaths_by_reporting_date.loc[:, 'reporting date'] = \
            pd.to_datetime(overall_deaths_by_reporting_date.loc[:, 'reporting date'], unit='ms')
        overall_deaths_by_reporting_date = overall_deaths_by_reporting_date.set_index("reporting date")
        overall_deaths_by_reporting_date = overall_deaths_by_reporting_date.sort_index()

        datetime_of_data_status_str_german = overall_deaths_by_reporting_date.iloc[0, :]["data status"]
        datetime_of_data_status = pd.to_datetime(datetime_of_data_status_str_german.split(",")[0], dayfirst=True)

        return overall_deaths_by_reporting_date.loc[:, 'new reported deaths by reporting date'], \
               datetime_of_data_status

    def get_last_date(self) -> dt.datetime:
        return self.index.max()

    def get_second_last_date(self) -> dt.datetime:
        return self.get_last_date() - pd.DateOffset(1)

    def get_last_rki_reporting_date(self) -> dt.datetime:
        return self.loc[:, "RKI reporting date"].max()

    def get_last_date_for_mean_values(self) -> dt.datetime:
        return self.index.max() - pd.DateOffset(3)

    def get_second_last_date_for_mean_values(self) -> dt.datetime:
        return self.get_last_date_for_mean_values() - pd.DateOffset(1)

    def get_last_reported_cases(self) -> int:
        last_date = self.get_last_date()
        return self.loc[last_date, "cases"]

    def get_second_last_reported_cases(self) -> int:
        second_last_date = self.get_second_last_date()
        return self.loc[second_last_date, "cases"]

    def get_change_from_second_last_to_last_date_for_reported_cases(self) -> int:
        return self.get_last_reported_cases() - self.get_second_last_reported_cases()

    def get_last_mean_cases(self) -> float:
        last_date_for_mean_values = self.get_last_date_for_mean_values()
        return self.loc[last_date_for_mean_values, "cases (mean of ±3 days)"]

    def get_second_last_mean_cases(self) -> float:
        second_last_date_for_mean_values = self.get_second_last_date_for_mean_values()
        return self.loc[second_last_date_for_mean_values, "cases (mean of ±3 days)"]

    def get_change_from_second_last_to_last_date_for_mean_cases(self) -> float:
        return self.get_last_mean_cases() - self.get_second_last_mean_cases()

    def get_last_cases_cumulative(self) -> int:
        last_date = self.get_last_date()
        return self.loc[last_date, "cases cumulative"]

    def get_last_reported_deaths(self) -> int:
        last_date = self.get_last_date()
        return self.loc[last_date, "deaths"]

    def get_second_last_reported_deaths(self) -> int:
        second_last_date = self.get_second_last_date()
        return self.loc[second_last_date, "deaths"]

    def get_change_from_second_last_to_last_date_for_reported_deaths(self) -> int:
        return self.get_last_reported_deaths() - self.get_second_last_reported_deaths()

    def get_last_mean_deaths(self) -> float:
        last_date_for_mean_values = self.get_last_date_for_mean_values()
        return self.loc[last_date_for_mean_values, "deaths (mean of ±3 days)"]

    def get_second_last_mean_deaths(self) -> float:
        second_last_date_for_mean_values = self.get_second_last_date_for_mean_values()
        return self.loc[second_last_date_for_mean_values, "deaths (mean of ±3 days)"]

    def get_change_from_second_last_to_last_date_for_mean_deaths(self) -> float:
        return self.get_last_mean_deaths() - self.get_second_last_mean_deaths()

    def get_last_deaths_cumulative(self) -> int:
        last_date = self.get_last_date()
        return self.loc[last_date, "deaths cumulative"]

    def get_last_r_value_by_mean_cases(self) -> float:
        last_date_for_mean_values = self.get_last_date_for_mean_values()
        return self.loc[last_date_for_mean_values, "R value by cases (mean of ±3 days)"]

    def get_second_last_r_value_by_mean_cases(self) -> float:
        second_last_date_for_mean_values = self.get_second_last_date_for_mean_values()
        return self.loc[second_last_date_for_mean_values, "R value by cases (mean of ±3 days)"]

    def get_change_from_second_last_to_last_date_for_r_value_by_mean_cases(self) -> float:
        return self.get_last_r_value_by_mean_cases() - self.get_second_last_r_value_by_mean_cases()

    def get_cases_last_7_days(self) -> int:
        last_date = self.get_last_date()
        return self.loc[last_date, "cases last 7 days"]

    def get_deaths_last_7_days(self) -> int:
        last_date = self.get_last_date()
        return self.loc[last_date, "deaths last 7 days"]

    def get_last_7_day_incidence_per_100_000_inhabitants(self) -> float:
        last_date = self.get_last_date()
        return self.loc[last_date, "7 day incidence per 100,000 inhabitants"]

    def get_second_last_7_day_incidence_per_100_000_inhabitants(self) -> float:
        second_last_date = self.get_second_last_date()
        return self.loc[second_last_date, "7 day incidence per 100,000 inhabitants"]

    def get_change_from_second_last_to_last_date_for_7_day_incidence_per_100_000_inhabitants(self) -> float:
        return self.get_last_7_day_incidence_per_100_000_inhabitants() - \
               self.get_second_last_7_day_incidence_per_100_000_inhabitants()

    def get_last_7_day_incidence_per_100_000_inhabitants_by_reporting_date(self) -> float:
        last_date = self.get_last_date()
        return self.loc[last_date, "7 day incidence per 100,000 inhabitants by reporting date (RKI version)"]

    def get_second_last_7_day_incidence_per_100_000_inhabitants_by_reporting_date(self) -> float:
        second_last_date = self.get_second_last_date()
        return self.loc[second_last_date, "7 day incidence per 100,000 inhabitants by reporting date (RKI version)"]

    def get_change_from_second_last_to_last_date_for_7_day_incidence_per_100_000_inhabitants_by_reporting_date(self) \
            -> float:
        return self.get_last_7_day_incidence_per_100_000_inhabitants() - \
               self.get_second_last_7_day_incidence_per_100_000_inhabitants()

    def get_last_7_day_deaths_per_1_000_000_inhabitants(self) -> float:
        last_date = self.get_last_date()
        return self.loc[last_date, "7 day deaths per 1,000,000 inhabitants"]

    def get_second_last_7_day_deaths_per_1_000_000_inhabitants(self) -> float:
        second_last_date = self.get_second_last_date()
        return self.loc[second_last_date, "7 day deaths per 1,000,000 inhabitants"]

    def get_change_from_second_last_to_last_date_for_7_day_deaths_per_1_000_000_inhabitants(self) -> float:
        return self.get_last_7_day_deaths_per_1_000_000_inhabitants() - \
               self.get_second_last_7_day_deaths_per_1_000_000_inhabitants()

    def get_last_7_day_incidence_by_mean_cases_per_100_000_inhabitants(self) -> float:
        last_date_for_mean_values = self.get_last_date_for_mean_values()
        return self.loc[last_date_for_mean_values,
                        "7 day incidence (by cases (mean of ±3 days)) per 100,000 inhabitants"]

    def get_second_last_7_day_incidence_by_mean_cases_per_100_000_inhabitants(self) -> float:
        second_last_date_for_mean_values = self.get_second_last_date_for_mean_values()
        return self.loc[second_last_date_for_mean_values,
                        "7 day incidence (by cases (mean of ±3 days)) per 100,000 inhabitants"]

    def get_change_from_second_last_to_last_date_for_7_day_incidence_by_mean_cases_per_100_000_inhabitants(self) \
            -> float:
        return self.get_last_7_day_incidence_by_mean_cases_per_100_000_inhabitants() - \
               self.get_second_last_7_day_incidence_by_mean_cases_per_100_000_inhabitants()

    def get_last_7_day_deaths_by_mean_cases_per_1_000_000_inhabitants(self) -> float:
        last_date_for_mean_values = self.get_last_date_for_mean_values()
        return self.loc[last_date_for_mean_values,
                        "7 day deaths (by cases (mean of ±3 days)) per 1,000,000 inhabitants"]

    def get_second_last_7_day_deaths_by_mean_cases_per_1_000_000_inhabitants(self) -> float:
        second_last_date_for_mean_values = self.get_second_last_date_for_mean_values()
        return self.loc[second_last_date_for_mean_values,
                        "7 day deaths (by cases (mean of ±3 days)) per 1,000,000 inhabitants"]

    def get_change_from_second_last_to_last_date_for_7_day_deaths_by_mean_cases_per_1_000_000_inhabitants(self) \
            -> float:
        return self.get_last_7_day_deaths_by_mean_cases_per_1_000_000_inhabitants() - \
               self.get_second_last_7_day_deaths_by_mean_cases_per_1_000_000_inhabitants()
