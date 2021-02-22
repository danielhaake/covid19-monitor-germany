# subclassing of Pandas
# see: https://pandas.pydata.org/pandas-docs/stable/development/extending.html#override-constructor-properties
import logging
import os

from dotenv import load_dotenv
from io import BytesIO

import pandas as pd
import requests

load_dotenv()
logging.basicConfig(level=logging.INFO)

class AgeDistributionSeries(pd.Series):
    @property
    def _constructor(self):
        return AgeDistributionSeries

    @property
    def _constructor_expanddim(self):
        return AgeDistributionDataFrame


class AgeDistributionDataFrame(pd.DataFrame):

    _folder_path = "data/"
    _filename = "distribution_of_inhabitants_and_cases_and_deaths.csv"
    _path = _folder_path + _filename

    @property
    def _constructor(self):
        return AgeDistributionDataFrame

    @property
    def _constructor_sliced(self):
        return AgeDistributionSeries

    def _set_path(self, path):
        self._path = path

    def _set_folder_path(self, folder_path: str):
        self._folder_path = folder_path

    @staticmethod
    def from_csv(path: str=None) -> 'AgeDistributionDataFrame':

        if path is None:
            if os.environ.get('FOLDER_PATH') is not None:
                path = os.environ.get('FOLDER_PATH') + AgeDistributionDataFrame._filename
            else:
                path = AgeDistributionDataFrame._path

        logging.info(f"start loading AgeDistributionDataFrame from {path}")
        distribution = AgeDistributionDataFrame(pd.read_csv(path).set_index("age group"))

        if os.environ.get('FOLDER_PATH') is not None:
            distribution._set_folder_path(os.environ.get('FOLDER_PATH'))

        if path is not None:
            distribution._set_path(path)

        logging.info(f"AgeDistributionDataFrame successfully loaded from {path}")
        return distribution

    @staticmethod
    def get_age_distribution_of_cases_and_deaths(to_csv: bool = True, path: str = None) -> 'AgeDistributionDataFrame':

        logging.info("START DOWNLOADING CASES AND DEATHS PER AGE GROUP")

        inhabitants_per_age_group = AgeDistributionDataFrame.get_inhabitants_by_age_group()
        total_number_of_reported_cases_by_age_group = \
            AgeDistributionDataFrame.get_total_number_of_reported_cases_by_age_group()
        new_reported_cases_by_age_group = \
            AgeDistributionDataFrame.get_new_reported_cases_by_age_group()
        total_number_of_reported_deaths_by_age_group = \
            AgeDistributionDataFrame.get_total_number_of_reported_deaths_by_age_group()
        new_reported_deaths_by_age_group = \
            AgeDistributionDataFrame.get_new_reported_deaths_by_age_group()

        age_distribution = AgeDistributionDataFrame(
            pd.concat([inhabitants_per_age_group,
                       total_number_of_reported_cases_by_age_group,
                       new_reported_cases_by_age_group,
                       total_number_of_reported_deaths_by_age_group,
                       new_reported_deaths_by_age_group],
                      axis=1)) \
            .fillna(0) \
            .astype(int)

        age_distribution.loc[:, "total reported cases per 100,000 inhabitants"] = \
            age_distribution.loc[:, "total reported cases"] / age_distribution.inhabitants * 100_000
        age_distribution.loc[:, "new reported cases per 100,000 inhabitants"] = \
            age_distribution.loc[:, "new reported cases"] / age_distribution.inhabitants * 100_000
        age_distribution.loc[:, "total reported deaths per 1,000,000 inhabitants"] = \
            age_distribution.loc[:, "total reported deaths"] / age_distribution.inhabitants * 1_000_000
        age_distribution.loc[:, "new reported deaths per 1,000,000 inhabitants"] = \
            age_distribution.loc[:, "new reported deaths"] / age_distribution.inhabitants * 1_000_000

        age_distribution.index = age_distribution.index.rename('age group')

        if to_csv:
            if path is None:
                if os.environ.get('FOLDER_PATH') is not None:
                    path = os.environ.get('FOLDER_PATH') + AgeDistributionDataFrame._filename
                    age_distribution._set_folder_path(os.environ.get('FOLDER_PATH'))
                    age_distribution._set_path(path)
                else:
                    path = AgeDistributionDataFrame._path
            logging.info(f"try writing AgeDistributionDataFrame to {path}")
            age_distribution.to_csv(path)
            logging.info(f"new AgeDistributionDataFrame has been written to {path}")

        logging.info("FINISHED DOWNLOADING CASES AND DEATHS PER AGE GROUP")

        return age_distribution

    @staticmethod
    def get_new_reported_cases_by_age_group() -> pd.Series:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerFall IN(-1, 1)' \
              '&objectIds=' \
              '&time=' \
              '&resultType=standard' \
              '&outFields=AnzahlFall,Altersgruppe' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Altersgruppe' \
              '&outStatistics=[' \
                '{"statisticType":"sum","onStatisticField":"AnzahlFall","outStatisticFieldName":"cases"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='


        response = requests.get(url)
        data = response.json()
        new_reported_cases_per_age_group = pd.json_normalize(data["features"])
        new_reported_cases_per_age_group = new_reported_cases_per_age_group.rename(
            columns={'attributes.cases': 'new reported cases', 'attributes.Altersgruppe': 'age group'})
        new_reported_cases_per_age_group = new_reported_cases_per_age_group.set_index("age group")

        if "unbekannt" in new_reported_cases_per_age_group.index:
            new_reported_cases_per_age_group = new_reported_cases_per_age_group.rename(index={"unbekannt": "unknown"})

        #datetime_of_data_status_str_german = new_reported_cases_per_age_group.iloc[0, :]["data status"]
        #datetime_of_data_status = pd.to_datetime(datetime_of_data_status_str_german.split(",")[0], dayfirst=True)

        return new_reported_cases_per_age_group.sort_index() #, datetime_of_data_status

    @staticmethod
    def get_total_number_of_reported_cases_by_age_group() -> pd.Series:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerFall IN(1,0)' \
              '&objectIds=' \
              '&time=' \
              '&resultType=standard' \
              '&outFields=AnzahlFall,Altersgruppe' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Altersgruppe' \
              '&outStatistics=[' \
                '{"statisticType":"sum","onStatisticField":"AnzahlFall","outStatisticFieldName":"cases"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='

        response = requests.get(url)
        data = response.json()
        total_number_of_cases_by_age_group = pd.json_normalize(data["features"])
        total_number_of_cases_by_age_group = total_number_of_cases_by_age_group.rename(
            columns={'attributes.cases': 'total reported cases', 'attributes.Altersgruppe': 'age group'})

        # overall_deaths_per_age_group.loc[:, 'reference date'] = pd.to_datetime(overall_deaths_per_age_group.loc[:, 'reference date'], unit='ms')
        total_number_of_cases_by_age_group = total_number_of_cases_by_age_group.set_index("age group")

        if "unbekannt" in total_number_of_cases_by_age_group.index:
            total_number_of_cases_by_age_group = \
                total_number_of_cases_by_age_group.rename(index={"unbekannt": "unknown"})

        return total_number_of_cases_by_age_group.sort_index()


    @staticmethod
    def get_new_reported_deaths_by_age_group() -> pd.Series:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerTodesfall IN(1,-1)' \
              '&objectIds=' \
              '&time=' \
              '&resultType=standard' \
              '&outFields=AnzahlTodesfall,Altersgruppe' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Altersgruppe' \
              '&outStatistics=[' \
                '{"statisticType":"sum","onStatisticField":"AnzahlTodesfall","outStatisticFieldName":"deaths"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='

        response = requests.get(url)
        data = response.json()
        new_reported_deaths_per_age_group = pd.json_normalize(data["features"])
        new_reported_deaths_per_age_group = new_reported_deaths_per_age_group.rename(
            columns={'attributes.deaths': 'new reported deaths', 'attributes.Altersgruppe': 'age group'})

        new_reported_deaths_per_age_group = new_reported_deaths_per_age_group.set_index("age group")
        if "unbekannt" in new_reported_deaths_per_age_group.index:
            new_reported_deaths_per_age_group = \
                new_reported_deaths_per_age_group.rename(index={"unbekannt": "unknown"})

        return new_reported_deaths_per_age_group.sort_index()


    @staticmethod
    def get_total_number_of_reported_deaths_by_age_group() -> pd.Series:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_COVID19/FeatureServer/0/' \
              'query?where=' \
              'NeuerTodesfall IN(1,0)' \
              '&objectIds=' \
              '&time=' \
              '&resultType=standard' \
              '&outFields=AnzahlTodesfall%2CAltersgruppe' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              '&orderByFields=' \
              '&groupByFieldsForStatistics=Altersgruppe' \
              '&outStatistics=[' \
                '{"statisticType":"sum","onStatisticField":"AnzahlTodesfall","outStatisticFieldName":"deaths"}]' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='

        response = requests.get(url)
        data = response.json()
        total_number_of_deaths_per_age_group = pd.json_normalize(data["features"])
        total_number_of_deaths_per_age_group = total_number_of_deaths_per_age_group.rename(
            columns={'attributes.deaths': 'total reported deaths', 'attributes.Altersgruppe': 'age group'})

        total_number_of_deaths_per_age_group = total_number_of_deaths_per_age_group.set_index("age group")
        if "unbekannt" in total_number_of_deaths_per_age_group.index:
            total_number_of_deaths_per_age_group = \
                total_number_of_deaths_per_age_group.rename(index={"unbekannt": "unknown"})

        return total_number_of_deaths_per_age_group.sort_index()


    @staticmethod
    def get_inhabitants_by_age_group() -> pd.DataFrame:
        return pd.DataFrame.from_dict({"A00-A04": 3961376,
                                       "A05-A14": 7429883,
                                       "A15-A34": 19117865,
                                       "A35-A59": 28919134,
                                       "A60-A79": 18057318,
                                       "A80+": 5681135}, orient='index', columns=["inhabitants"])