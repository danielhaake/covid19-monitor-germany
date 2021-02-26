# subclassing of Pandas
# see: https://pandas.pydata.org/pandas-docs/stable/development/extending.html#override-constructor-properties
import boto3
import logging
import os

from dotenv import load_dotenv
from io import BytesIO, StringIO

import pandas as pd
import requests

load_dotenv()
logging.basicConfig(level=logging.INFO)

class ClinicalAspectsSeries(pd.Series):
    @property
    def _constructor(self):
        return ClinicalAspectsSeries

    @property
    def _constructor_expanddim(self):
        return ClinicalAspectsDataFrame


class ClinicalAspectsDataFrame(pd.DataFrame):

    _folder_path = "data/"
    _filename = "clinical_aspects.csv"
    _path = _folder_path + _filename

    @property
    def _constructor(self):
        return ClinicalAspectsDataFrame

    @property
    def _constructor_sliced(self):
        return ClinicalAspectsSeries

    def _set_path(self, path: str):
        self._path = path

    def _set_folder_path(self, folder_path: str):
        self._folder_path = folder_path

    @staticmethod
    def from_csv(s3_bucket: str=None, path: str=None) -> 'ClinicalAspectsDataFrame':

        if (os.environ.get('S3_BUCKET') is not None) | (s3_bucket is not None):
            if s3_bucket is None:
                s3_bucket = os.environ.get('S3_BUCKET')
            s3 = boto3.client('s3')
            filename = ClinicalAspectsDataFrame._filename
            logging.info(f"start loading ClinicalAspectsDataFrame with filename {filename} "
                         f"from S3 Bucket {s3_bucket}")
            read_file = s3.get_object(Bucket=s3_bucket, Key=filename)
            clinical_aspects = ClinicalAspectsDataFrame(pd.read_csv(read_file['Body'], index_col="calendar week"))
            logging.info(f"ClinicalAspectsDataFrame with filename {filename} successfully loaded "
                         f"from S3 Bucket {s3_bucket}")
        else:
            if path is None:
                if os.environ.get('FOLDER_PATH') is not None:
                    path = os.environ.get('FOLDER_PATH') + ClinicalAspectsDataFrame._filename
                else:
                    path = ClinicalAspectsDataFrame._path

            logging.info(f"start loading ClinicalAspectsDataFrame from {path}")
            clinical_aspects = ClinicalAspectsDataFrame(pd.read_csv(path, index_col="calendar week"))
            logging.info(f"ClinicalAspectsDataFrame successfully loaded from {path}")

        if os.environ.get('FOLDER_PATH') is not None:
            clinical_aspects._set_folder_path(os.environ.get('FOLDER_PATH'))

        if path is not None:
            clinical_aspects._set_path(path)

        return clinical_aspects

    @staticmethod
    def update_csv_with_new_data_from_rki(s3_bucket: str=None, path: str=None):

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
          clinical_aspects = ClinicalAspectsDataFrame(pd.read_excel(file_object, sheet_name="Daten", header=2)
                                                        .dropna(how="all", axis=1))
        except:
          clinical_aspects = ClinicalAspectsDataFrame(pd.read_excel(file_object, sheet_name=0, header=2)
                                                        .dropna(how="all", axis=1))
          
        clinical_aspects = rename_columns_german_to_english(clinical_aspects)

        clinical_aspects.loc[:, 'no symptoms or no symptoms significant for COVID-19 in %'] = clinical_aspects.\
            _convert_from_float_to_percent_for("proportion of no symptoms or no symptoms significant for COVID-19")

        clinical_aspects.loc[:, 'hospitalized in %'] = clinical_aspects.\
            _convert_from_float_to_percent_for("proportion hospitalized")

        clinical_aspects.loc[:, 'deceased in %'] = clinical_aspects.\
            _convert_from_float_to_percent_for("proportion deceased")

        clinical_aspects.loc[:, 'calendar week'] = clinical_aspects.combine_columns_reporting_year_and_reporting_week()
        clinical_aspects = clinical_aspects.set_index('calendar week')

        if (os.environ.get('S3_BUCKET') is not None) | (s3_bucket is not None):
            if s3_bucket is None:
                s3_bucket = os.environ.get('S3_BUCKET')
                csv_buffer = StringIO()
                clinical_aspects.to_csv(csv_buffer)
                s3 = boto3.client('s3')
                logging.info(f"try writing ClinicalAspectsDataFrame "
                             f"with filename {clinical_aspects._filename} "
                             f"to S3 Bucket {s3_bucket}")
                s3.put_object(Bucket=s3_bucket, Key=clinical_aspects._filename, Body=csv_buffer.getvalue())
                logging.info(f"updated ClinicalAspectsDataFrame "
                             f"with filename {clinical_aspects._filename} "
                             f"has been written to S3 Bucket {s3_bucket}")
        else:
            if path is None:
                if os.environ.get('FOLDER_PATH') is not None:
                    path = os.environ.get('FOLDER_PATH') + ClinicalAspectsDataFrame._filename
                    clinical_aspects._set_folder_path(os.environ.get('FOLDER_PATH'))
                    clinical_aspects._set_path(path)
                else:
                    path = ClinicalAspectsDataFrame._path
            else:
                clinical_aspects._set_path(path)
            logging.info(f"try writing ClinicalAspectsDataFrame to {path}")
            clinical_aspects.to_csv(path)
            logging.info(f"new ClinicalAspectsDataFrame has been written to {path}")

        logging.info("FINISHED UPDATE PROCESS FOR CLINICAL ASPECTS")
        return clinical_aspects

    def _convert_from_float_to_percent_for(self, column_name) -> float:
        return self.loc[:, column_name] * 100

    def combine_columns_reporting_year_and_reporting_week(self) -> str:
        return self.loc[:, 'reporting year'].astype(str) + ' - ' + self.loc[:, 'reporting week'].astype(str)
