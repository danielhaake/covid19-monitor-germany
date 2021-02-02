# subclassing of Pandas
# see: https://pandas.pydata.org/pandas-docs/stable/development/extending.html#override-constructor-properties
from io import BytesIO
from typing import List

import pandas as pd
import numpy as np
import requests


class NumberPCRTestsSeries(pd.Series):
    @property
    def _constructor(self):
        return NumberPCRTestsSeries

    @property
    def _constructor_expanddim(self):
        return NumberPCRTestsDataFrame


class NumberPCRTestsDataFrame(pd.DataFrame):

    _path = "data/number_of_tests_germany.csv"

    @property
    def _constructor(self):
        return NumberPCRTestsDataFrame

    @property
    def _constructor_sliced(self):
        return NumberPCRTestsSeries

    @staticmethod
    def from_csv(path: str=None) -> 'NumberPCRTestsDataFrame':
        if path is None:
            path = NumberPCRTestsDataFrame._path
        number_pcr_tests = NumberPCRTestsDataFrame(pd.read_csv(path,
                                                               index_col="calendar week"))
        if path is not None:
            number_pcr_tests._set_path(path)

        return number_pcr_tests

    def _set_path(self, path: str):
        self._path = path

    @staticmethod
    def update_csv_with_new_data_from_rki(to_csv: bool=True, path: str=None) -> 'NumberPCRTestsDataFrame':

        def rename_columns_german_to_english(df: NumberPCRTestsDataFrame) -> NumberPCRTestsDataFrame:
            return df.rename(columns={'Anzahl Testungen': 'number of tests',
                                      'Positiv getestet': 'positive tested',
                                      'Kalenderwoche': 'calendar week',
                                      'Positiven-quote (%)': 'positive rate (%)',
                                      'Anzahl übermittelnde Labore': 'number of transmitting laboratories'
                                      })

        url = 'https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Daten/Testzahlen-gesamt.xlsx?__blob=publicationFile'
        response = requests.get(url)
        file_object = BytesIO(response.content)
        number_pcr_tests = NumberPCRTestsDataFrame(pd.read_excel(file_object, sheet_name="Testzahlen", header=2)\
                                                     .drop("Unnamed: 0", axis=1))

        number_pcr_tests = rename_columns_german_to_english(number_pcr_tests)

        number_pcr_tests["negative tested"] = number_pcr_tests.calculate_number_of_negative_tests()

        number_pcr_tests["change in number of tests compared to previous week (%)"] = number_pcr_tests.\
            calculate_change_in_number_of_tests_compared_to_previous_week_in_percent()

        number_pcr_tests = number_pcr_tests._cleaning_because_of_calendar_week_column()

        if to_csv:
            if path is None:
                path = NumberPCRTestsDataFrame._path
            number_pcr_tests.to_csv(path)
        # TODO number_pcr_tests.to_csv("./data/number_of_tests_germany.csv")
        return number_pcr_tests

    def calculate_change_in_number_of_tests_compared_to_previous_week_in_percent(self) -> List[float]:
        return 2 * [np.nan] + \
               [(self.loc[i, "number of tests"] / self.loc[i - 1, "number of tests"]) * 100 - 100
                for i in range(2, len(self) - 1)] \
               + [np.nan]

    def calculate_number_of_negative_tests(self) -> List[int]:
        return [self.loc[i, "number of tests"] -
                self.loc[i, "positive tested"]
                for i in range(len(self))]

    def _cleaning_because_of_calendar_week_column(self) -> 'NumberPCRTestsDataFrame':
        self.loc[self.loc[:, "calendar week"] == "Bis einschließlich KW10, 2020", :"calendar week"] = "≤10"
        first_not_included_row = self.loc[self.loc[:, "calendar week"] == "Summe"].index[0]
        self.loc[:, "calendar week"] = self.loc[:, "calendar week"].astype("str")
        self.loc[:, "calendar week"] = self.loc[:, "calendar week"].str.replace("*", "")
        calendar_week_splitted = self.loc[:, "calendar week"].str.split("/")
        self.loc[:, "week of year"] = calendar_week_splitted.str[0]
        self.loc[:, "year"] = calendar_week_splitted.str[1]
        self.loc[:, "calendar week"] = self.loc[:, "year"] + " - " + self.loc[:, "week of year"]
        return self.iloc[:first_not_included_row, :]
