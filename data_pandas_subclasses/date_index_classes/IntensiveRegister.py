# subclassing of Pandas
# see: https://pandas.pydata.org/pandas-docs/stable/development/extending.html#override-constructor-properties
import logging
from dotenv import load_dotenv

from typing import TypeVar

import pandas as pd
import numpy as np

from datetime import datetime

from api.IntensiveRegisterAPI import IntensiveRegisterAPI
from data_pandas_subclasses.date_index_classes.CoronaBaseDateIndex import CoronaBaseDateIndexSeries, CoronaBaseDateIndexDataFrame

load_dotenv()
logging.basicConfig(level=logging.INFO)
TNum = TypeVar('TNum', int, float)


class IntensiveRegisterSeries(CoronaBaseDateIndexSeries):
    @property
    def _constructor(self):
        return IntensiveRegisterSeries

    @property
    def _constructor_expanddim(self):
        return IntensiveRegisterDataFrame


class IntensiveRegisterDataFrame(CoronaBaseDateIndexDataFrame):
    _filename = "intensive_register_total.csv"
    api = IntensiveRegisterAPI()

    @property
    def _constructor(self):
        return IntensiveRegisterDataFrame

    @property
    def _constructor_sliced(self):
        return IntensiveRegisterSeries

    @staticmethod
    def from_csv(filename: str = None,
                 s3_bucket: str = None,
                 folder_path: str = None,
                 class_name: str = None) -> 'IntensiveRegisterDataFrame':

        if filename is None:
            filename = IntensiveRegisterDataFrame._filename
        if class_name is None:
            class_name = IntensiveRegisterDataFrame.__name__
        df = CoronaBaseDateIndexDataFrame.from_csv(filename, s3_bucket, folder_path, class_name)

        return IntensiveRegisterDataFrame(df)

    def last_r_value_by_mean_cases(self) -> float:
        last_date = self.last_date_for_mean_values()
        return self.loc[last_date,
                        "R value calculated by newly admitted intensive care patients with a " \
                        "positive COVID-19 test (mean ±3 days)"]

    def second_last_r_value_by_mean_cases(self) -> float:
        second_last_date = self.second_last_date_for_mean_values()
        return self.loc[second_last_date,
                        "R value calculated by newly admitted intensive care patients with a " \
                        "positive COVID-19 test (mean ±3 days)"]

    def change_from_second_last_to_last_date_for_r_value_by_mean_cases(self) -> float:
        return self.last_r_value_by_mean_cases() - self.second_last_r_value_by_mean_cases()

    @staticmethod
    def update_csv_with_intensive_register_data(s3_bucket: str = None,
                                                folder_path: str = None,
                                                url_pdf: str = None,
                                                url_csv: str = None,
                                                days_incubation_period: int = 5,
                                                days_from_symptoms_to_intensive_care: int = 9) \
            -> 'IntensiveRegisterDataFrame':

        logging.info("START UPDATE PROCESS FOR INTENSIVE REGISTER")

        intensive_register = IntensiveRegisterDataFrame.from_csv(folder_path)
        logging.info("initial loading of CSV finished")

        intensive_register._update_intensive_register_data(s3_bucket=s3_bucket,
                                                           folder_path=folder_path,
                                                           url_pdf=url_pdf,
                                                           url_csv=url_csv,
                                                           days_incubation_period=days_incubation_period,
                                                           days_from_symptoms_to_intensiv_care=
                                                           days_from_symptoms_to_intensive_care,
                                                           to_csv=True)

        logging.info("FINISHED UPDATE PROCESS FOR INTENSIVE REGISTER")
        return intensive_register

    def _update_intensive_register_data(self,
                                        s3_bucket: str = None,
                                        folder_path: str = None,
                                        url_pdf: str = None,
                                        url_csv: str = None,
                                        days_incubation_period: int = 5,
                                        days_from_symptoms_to_intensiv_care: int = 9,
                                        to_csv: bool = True) -> None:

        logging.info("start update with new data from RKI API")

        self._get_cases_and_capacities_from_intensive_register_report(url_pdf, url_csv)
        self._calculate_changes_from_previous_day()
        self._calculate_number_of_used_and_unused_intensive_care_beds()
        self._delete_outliers()
        self._calculate_7_day_moving_means()
        self._calculate_r_value_by_moving_mean_newly_admitted_covid_19_intensive_care_patients()
        self._calculate_possible_infection_date(days_from_symptoms_to_intensiv_care, days_incubation_period)
        self._calculate_proportional_columns()

        logging.info("finished update with new data from RKI API")

        self = self.dropna(how="all", axis=0)

        if to_csv:
            self.save_as_csv(s3_bucket=s3_bucket, folder_path=folder_path)

    def _delete_outliers(self) -> None:
        """The 'DIVI Intensivregister' reports outliers because of bigger corrections of some hospitals or
        anomalies in the figures for some dates. This method deletes these outliers.
        see: https://www.intensivregister.de/#/aktuelle-lage/reports"""

        logging.info("delete outliers")

        outlier_dates = [pd.to_datetime("2021-01-15"),
                         pd.to_datetime("2021-01-20"),
                         pd.to_datetime("2021-06-23")]

        outlier_columns = ['newly admitted intensive care patients with a positive COVID-19 test',
                           'with treatment completed']

        for outlier_date in outlier_dates:
            for outlier_column in outlier_columns:
                self.loc[outlier_date, outlier_column] = np.nan
        logging.info("outliers has been removed")

    def _calculate_proportional_columns(self) -> None:

        logging.info("calculate proportional columns")

        def calculate_invasively_ventilated_in_percent():
            return [self.iloc[i]['invasively ventilated'] /
                    self.iloc[i]['intensive care patients with positive COVID-19 test'] * 100
                    for i in range(len(self))]

        def calculate_proportion_intensive_care_beds():
            return self.loc[:, 'occupied intensive care beds'] / \
                   (self.loc[:, 'occupied intensive care beds'] + self.loc[:, 'free intensive care beds']) * 100

        def calculate_proportion_intensive_care_beds_incl_emergency_reserve():
            return self.loc[:, 'occupied intensive care beds'] / \
                   (self.loc[:, 'occupied intensive care beds'] +
                    self.loc[:, 'emergency reserve'] +
                    self.loc[:, 'free intensive care beds']) * 100

        def calculate_proportion_covid19_intensive_care_patients_to_occupied_intensive_care_beds():
            return self.loc[:, 'COVID-19 cases'] / \
                   self.loc[:, 'occupied intensive care beds'] \
                   * 100

        def calculate_proportion_covid19_intensive_care_patients_to_available_beds_without_emergency_reserve():
            return self.loc[:, 'COVID-19 cases'] / \
                   (self.loc[:, 'occupied intensive care beds'] +
                    self.loc[:, 'free intensive care beds']) \
                   * 100

        def calculate_proportion_covid19_intensive_care_patients_to_available_beds_incl_emergency_reserve():
            return self.loc[:, 'COVID-19 cases'] / \
                   (self.loc[:, 'occupied intensive care beds'] +
                    self.loc[:, 'free intensive care beds'] +
                    self.loc[:, 'emergency reserve']) \
                   * 100

        self.loc[:, 'invasively ventilated (%)'] = calculate_invasively_ventilated_in_percent()
        self.loc[:, 'Proportion of occupied intensive care beds (%)'] = calculate_proportion_intensive_care_beds()
        self.loc[:, 'Proportion of occupied intensive care beds incl. emergency reserve (%)'] = \
            calculate_proportion_intensive_care_beds_incl_emergency_reserve()
        self.loc[:, 'Proportion of patients with positive COVID-19 test in occupied intensive care beds (%)'] = \
            calculate_proportion_covid19_intensive_care_patients_to_occupied_intensive_care_beds()
        self.loc[:,
        'Proportion of patients with positive COVID-19 test in available intensive care beds without emergency reserve (%)'] = \
            calculate_proportion_covid19_intensive_care_patients_to_available_beds_without_emergency_reserve()
        self.loc[:,
        'Proportion of patients with positive COVID-19 test in available intensive care beds incl. emergency reserve (%)'] = \
            calculate_proportion_covid19_intensive_care_patients_to_available_beds_incl_emergency_reserve()

        logging.info("calculated proportional columns has been added")

    def _calculate_possible_infection_date(self, days_from_symptoms_to_intensiv_care, days_incubation_period) -> None:

        logging.info("calculate possible infection date")

        intensive_register_by_infection_date = \
            self.loc[:,
            ['newly admitted intensive care patients with a positive COVID-19 test',
             'newly admitted intensive care patients with a positive COVID-19 test (mean ±3 days)',
             'R value calculated by newly admitted intensive care patients with a positive COVID-19 test (mean ±3 days)']]

        intensive_register_by_infection_date = intensive_register_by_infection_date.reset_index()
        intensive_register_by_infection_date.loc[:, "date"] = \
            intensive_register_by_infection_date.loc[:, "date"] - \
            pd.DateOffset(days_incubation_period + days_from_symptoms_to_intensiv_care)

        intensive_register_by_infection_date = intensive_register_by_infection_date.set_index("date")
        intensive_register_by_infection_date = intensive_register_by_infection_date.rename(columns={
            'newly admitted intensive care patients with a positive COVID-19 test':
                'calculated start of infection of newly admitted intensive care patients with a positive COVID-19 test',
            'newly admitted intensive care patients with a positive COVID-19 test (mean ±3 days)':
                'calculated start of infection of newly admitted intensive care patients with a positive COVID-19 test (mean ±3 days)',
            'R value calculated by newly admitted intensive care patients with a positive COVID-19 test (mean ±3 days)':
                'R value by calculated onset of infection of newly admitted intensive care patients with a positive COVID-19 test (mean ±3 days)'
        })
        self. \
            drop(
            ['calculated start of infection of newly admitted intensive care patients with a positive COVID-19 test',
             'calculated start of infection of newly admitted intensive care patients with a positive COVID-19 test (mean ±3 days)',
             'R value by calculated onset of infection of newly admitted intensive care patients with a positive COVID-19 test (mean ±3 days)'],
            axis=1, inplace=True)
        self.__dict__.update(self.merge(intensive_register_by_infection_date,
                                        how="outer",
                                        left_index=True,
                                        right_index=True).__dict__)
        logging.info("calculated possible infection date has been added")

    def _calculate_r_value_by_moving_mean_newly_admitted_covid_19_intensive_care_patients(self) -> None:

        logging.info("calculate R value by moving mean newly admitted covid-19 intensive care patients")

        moving_mean_newly_admitted_covid_19_intensive_care_patients_column_name = \
            'newly admitted intensive care patients with a positive COVID-19 test (mean ±3 days)'

        cases_sum_7d_to_4d_before = self. \
            calculate_sum_7d_to_4d_before_for(moving_mean_newly_admitted_covid_19_intensive_care_patients_column_name)
        cases_sum_3d_to_0d_before = self. \
            calculate_sum_3d_to_0d_before_for(moving_mean_newly_admitted_covid_19_intensive_care_patients_column_name)

        self.loc[:,
        'R value calculated by newly admitted intensive care patients with a positive COVID-19 test (mean ±3 days)'] = \
            [cases_sum_3d_to_0d_before[i] / cases_sum_7d_to_4d_before[i]
             if cases_sum_7d_to_4d_before[i] != 0
             else np.nan
             for i in range(len(cases_sum_3d_to_0d_before))]
        logging.info("calculated R value by moving mean newly admitted covid-19 intensive care patients has been added")

    def _calculate_7_day_moving_means(self) -> None:

        logging.info("calculate 7 day moving means")

        self.loc[:, 'intensive care patients with positive COVID-19 test (change from previous day, mean ±3 days)'] = \
            self.calculate_7d_moving_mean_for_column(
                'intensive care patients with positive COVID-19 test (change from previous day)')

        self.loc[:, 'number of occupied intensive care beds (mean ±3 days)'] = \
            self.calculate_7d_moving_mean_for_column('occupied intensive care beds')

        self.loc[:, 'newly admitted intensive care patients with a positive COVID-19 test (mean ±3 days)'] = \
            self.calculate_7d_moving_mean_for_column(
                'newly admitted intensive care patients with a positive COVID-19 test')

        self.loc[:, 'intensive care patients with positive COVID-19 test (mean ±3 days)'] = \
            self.calculate_7d_moving_mean_for_column('intensive care patients with positive COVID-19 test')

        self.loc[:, 'invasively ventilated (mean ±3 days)'] = \
            self.calculate_7d_moving_mean_for_column('invasively ventilated')

        self.loc[:, 'with treatment completed (change from previous day, mean ±3 days)'] = \
            self.calculate_7d_moving_mean_for_column('with treatment completed (change from previous day)')

        logging.info("calculated 7 day moving means has been added")

    def _calculate_number_of_used_and_unused_intensive_care_beds(self) -> None:

        logging.info("calculate number of uses and unused intensive care beds")

        def calculate_intensive_care_patients_without_positive_covid19_test():
            return self.loc[:, 'occupied intensive care beds'] - self.loc[:, 'COVID-19 cases']

        def calculate_number_of_intensive_care_beds():
            return self.loc[:, 'occupied intensive care beds'] + self.loc[:, 'free intensive care beds']

        def calculate_number_of_intensive_care_beds_incl_emergency_reserve():
            return self.loc[:, 'number of intensive care beds'] + self.loc[:, 'emergency reserve']

        def calculate_not_invasively_ventilated():
            return self.loc[:, 'intensive care patients with positive COVID-19 test'] - \
                   self.loc[:, 'invasively ventilated']

        self.loc[:, 'intensive care patients without positive COVID-19 test'] = \
            calculate_intensive_care_patients_without_positive_covid19_test()
        self.loc[:, 'number of intensive care beds'] = calculate_number_of_intensive_care_beds()
        self.loc[:, 'number of intensive care beds incl. emergency reserve'] = \
            calculate_number_of_intensive_care_beds_incl_emergency_reserve()
        self.loc[:, 'not invasively ventilated'] = calculate_not_invasively_ventilated()
        logging.info("calculated number of uses and unused intensive care beds has been added")

    def _calculate_changes_from_previous_day(self) -> None:

        logging.info("calculate changes from previous day")

        def calculate_change_from_previous_day_for(column_name: str):
            return [(self.loc[date, column_name]) - (self.loc[date - pd.DateOffset(1), column_name])
                    if (date - pd.DateOffset(1)) in self.index
                    else np.nan
                    for date
                    in self.index]

        def calculate_newly_admitted_covid19_intensive_care_patients():
            return [self.iloc[i]['in intensive care treatment (change from previous day)'] +
                    self.iloc[i]['with treatment completed (change from previous day)']
                    for i in range(len(self))]

        self.loc[:, 'intensive care patients with positive COVID-19 test (change from previous day)'] = \
            calculate_change_from_previous_day_for('COVID-19 cases')
        self.loc[:, 'with treatment completed (change from previous day)'] = \
            calculate_change_from_previous_day_for('with treatment completed')
        self.loc[:, 'in intensive care treatment (change from previous day)'] = \
            calculate_change_from_previous_day_for('intensive care patients with positive COVID-19 test')
        self.loc[:, 'invasively ventilated (change from previous day)'] = \
            calculate_change_from_previous_day_for('invasively ventilated')
        self.loc[:, 'thereof deceased (change from previous day)'] = \
            calculate_change_from_previous_day_for('thereof deceased')

        # self.loc[:, 'newly admitted intensive care patients with a positive COVID-19 test'] = \
        #     calculate_newly_admitted_covid19_intensive_care_patients()

        logging.info("calculated changes from previous day has been added")

    def _get_cases_and_capacities_from_intensive_register_report(self,
                                                                 url_pdf: str = None,
                                                                 url_csv: str = None) -> None:
        datetime_of_first_request = None
        datetime_of_last_request = None

        while ((datetime_of_first_request != datetime_of_last_request) |
               (datetime_of_first_request is None) | (datetime_of_last_request is None)):

            datetime_of_first_request = self._get_cases_from_intensive_register_report(url_pdf)
            datetime_of_last_request = self._get_capacities_from_intensive_register_report(url_pdf, url_csv)

    def _get_cases_from_intensive_register_report(self, url_pdf: str = None) -> datetime:
        logging.info("get cases from intensive register report")
        cases_dict = self.api.get_cases_from_intensive_register_report(url_pdf)
        date = cases_dict["reporting date"]
        date_day_before = date - pd.DateOffset(1)

        columns = ['intensive care patients with positive COVID-19 test',
                   'invasively ventilated',
                   'newly admitted intensive care patients with a positive COVID-19 test',
                   'thereof deceased (change from previous day)'
                   ]
        for column in columns:
            self.loc[date, column] = \
                cases_dict[column]

        self.loc[date, 'thereof deceased'] = \
            self.loc[date_day_before, 'thereof deceased'] + cases_dict['thereof deceased (change from previous day)']
        logging.info("cases from intensive register report has been added")
        return date

    def _get_capacities_from_intensive_register_report(self, url_pdf: str = None, url_csv: str = None) -> datetime:
        logging.info("get capacities from intensive register report")
        capacities_dict = self.api.get_capacities_from_intensive_register_report(url_pdf=url_pdf, url_csv=url_csv)
        date = capacities_dict["reporting date"]

        columns = ['emergency reserve',
                   'number of reporting areas',
                   'COVID-19 cases',
                   'invasively ventilated',
                   'free intensive care beds',
                   'occupied intensive care beds']
        for column in columns:
            self.loc[date, column] = \
                capacities_dict[column]

        logging.info("capacities from intensive register report has been added")
        return date
