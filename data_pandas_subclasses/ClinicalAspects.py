# subclassing of Pandas
# see: https://pandas.pydata.org/pandas-docs/stable/development/extending.html#override-constructor-properties
from io import BytesIO

import pandas as pd
import requests


class ClinicalAspectsSeries(pd.Series):
    @property
    def _constructor(self):
        return ClinicalAspectsSeries

    @property
    def _constructor_expanddim(self):
        return ClinicalAspectsDataFrame


class ClinicalAspectsDataFrame(pd.DataFrame):

    _path = "data/clinical_aspects.csv"

    @property
    def _constructor(self):
        return ClinicalAspectsDataFrame

    @property
    def _constructor_sliced(self):
        return ClinicalAspectsSeries

    def _set_path(self, path: str):
        self._path = path

    @staticmethod
    def from_csv(path: str=None) -> 'ClinicalAspectsDataFrame':
        if path is None:
            path = ClinicalAspectsDataFrame._path
        clinical_aspects = ClinicalAspectsDataFrame(pd.read_csv(path, index_col="calendar week"))

        if path is not None:
            clinical_aspects._set_path(path)

        return clinical_aspects

    @staticmethod
    def update_csv_with_new_data_from_rki(path: str=None):

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

        if path is None:
            path = ClinicalAspectsDataFrame._path
        else:
            clinical_aspects._set_path(path)
        clinical_aspects.to_csv(path)
        # TODO clinical_aspects.to_csv('./data/clinical_aspects.csv')
        return clinical_aspects

    def _convert_from_float_to_percent_for(self, column_name) -> float:
        return self.loc[:, column_name] * 100

    def combine_columns_reporting_year_and_reporting_week(self) -> str:
        return self.loc[:, 'reporting year'].astype(str) + ' - ' + self.loc[:, 'reporting week'].astype(str)
