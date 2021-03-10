# subclassing of Pandas
# see: https://pandas.pydata.org/pandas-docs/stable/development/extending.html#override-constructor-properties
import boto3
import logging
import os

from dotenv import load_dotenv
from io import BytesIO, StringIO

import pandas as pd
import requests

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
    def update_csv_with_new_data_from_rki(s3_bucket: str=None, folder_path: str=None):

        def rename_columns_german_to_english(df: ClinicalAspectsDataFrame) -> ClinicalAspectsDataFrame:
            return df.rename(columns={'Meldejahr': 'reporting year',
                                      'MW': 'reporting week',
                                      'Fälle gesamt': 'reported cases',
                                      'Mittelwert Alter (Jahre)': 'mean age',
                                      'Männer': 'men',
                                      'Frauen': 'women',
                                      'Anzahl mit Angaben zu Symptomen': 'number with information on symptoms',
                                      'Anteil keine, bzw. keine für COVID-19 bedeutsamen Symptome':
                                          'proportion of no symptoms or no symptoms significant for COVID-19',
                                      'Anzahl mit Angaben zur Hospitalisierung': 'number with hospitalization data',
                                      'Anzahl hospitalisiert': 'number hospitalized',
                                      'Anteil hospitalisiert': 'proportion hospitalized',
                                      'Anzahl Verstorben': 'number deceased',
                                      'Anteil Verstorben': 'proportion deceased'
                                      })

        logging.info("START UPDATE PROCESS FOR CLINICAL ASPECTS")
        logging.info("start downloading file from RKI")

        url = "https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Daten/Klinische_Aspekte.xlsx;jsessionid=7D837F724D8740A949BB7CB9F6BF4450.internet101?__blob=publicationFile"
        response = requests.get(url)
        file_object = BytesIO(response.content)

        try:
          clinical_aspects = ClinicalAspectsDataFrame(pd.read_excel(file_object, sheet_name="Daten", header=1)
                                                        .dropna(how="all", axis=1))
        except:
          clinical_aspects = ClinicalAspectsDataFrame(pd.read_excel(file_object, sheet_name=0, header=1)
                                                        .dropna(how="all", axis=1))
          
        clinical_aspects = rename_columns_german_to_english(clinical_aspects)

        clinical_aspects.loc[:, 'no symptoms or no symptoms significant for COVID-19 in %'] = clinical_aspects.\
            _convert_to_percent_for_column("proportion of no symptoms or no symptoms significant for COVID-19")

        clinical_aspects.loc[:, 'hospitalized in %'] = clinical_aspects.\
            _convert_to_percent_for_column("proportion hospitalized")

        clinical_aspects.loc[:, 'deceased in %'] = clinical_aspects.\
            _convert_to_percent_for_column("proportion deceased")

        clinical_aspects.loc[:, 'calendar week'] = clinical_aspects.combine_columns_reporting_year_and_reporting_week()
        clinical_aspects = clinical_aspects.set_index('calendar week')

        clinical_aspects.save_as_csv(s3_bucket=s3_bucket, folder_path=folder_path)

        logging.info("FINISHED UPDATE PROCESS FOR CLINICAL ASPECTS")
        return clinical_aspects

    def _convert_to_percent_for_column(self, column_name: str) -> float:
        if self.loc[:, column_name].dtype == "float64":
            return self.loc[:, column_name] * 100
        return self.loc[:, column_name].str.replace(" %", "")

    def combine_columns_reporting_year_and_reporting_week(self) -> str:
        return self.loc[:, 'reporting year'].astype(str) + ' - ' + self.loc[:, 'reporting week'].astype(str)
