# subclassing of Pandas
# see: https://pandas.pydata.org/pandas-docs/stable/development/extending.html#override-constructor-properties
from io import BytesIO
from typing import TypeVar, List

import pandas as pd
import numpy as np
import datetime as dt

from tabula import read_pdf
from pdftotext import PDF
import urllib
from datetime import datetime

TNum = TypeVar('TNum', int, float)


class IntensiveRegisterSeries(pd.Series):
    @property
    def _constructor(self):
        return IntensiveRegisterSeries

    @property
    def _constructor_expanddim(self):
        return IntensiveRegisterDataFrame


class IntensiveRegisterDataFrame(pd.DataFrame):
    _path = "data/intensive_register_total.csv"
    _url_pdf = "https://diviexchange.blob.core.windows.net/%24web/DIVI_Intensivregister_Report.pdf"
    _url_csv = "https://diviexchange.blob.core.windows.net/%24web/DIVI_Intensivregister_Auszug_pro_Landkreis.csv"

    @property
    def _constructor(self):
        return IntensiveRegisterDataFrame

    @property
    def _constructor_sliced(self):
        return IntensiveRegisterSeries

    def _set_path(self, path: str):
        self._path = path

    @staticmethod
    def from_csv(path: str = None) -> 'IntensiveRegisterDataFrame':
        if path is None:
            path = IntensiveRegisterDataFrame._path
        intensive_register = IntensiveRegisterDataFrame(pd.read_csv(path,
                                                                    parse_dates=['date'],
                                                                    index_col="date"))
        if path is not None:
            intensive_register._set_path(path)
        return intensive_register

    @staticmethod
    def update_csv_with_intensive_register_data(path: str = None,
                                                days_incubation_period: int = 5,
                                                days_from_symptoms_to_intensive_care: int = 9) \
            -> 'IntensiveRegisterDataFrame':

        intensive_register = IntensiveRegisterDataFrame.from_csv(path)
        intensive_register._update_intensive_register_data(path=path,
                                                           days_incubation_period=days_incubation_period,
                                                           days_from_symptoms_to_intensiv_care=
                                                           days_from_symptoms_to_intensive_care,
                                                           to_csv=True)

        return intensive_register

    def _update_intensive_register_data(self,
                                        path: str = None,
                                        days_incubation_period: int = 5,
                                        days_from_symptoms_to_intensiv_care: int = 9,
                                        to_csv: bool = True) -> None:

        self._get_cases_from_intensive_register_report()
        self._get_capacities_intensivregister_report()
        self._calculate_changes_from_previous_day()
        self._calculate_number_of_used_and_unused_intensive_care_beds()
        self._delete_outliers()
        self._calculate_7_day_moving_means()
        self._calculate_r0_by_moving_mean_newly_admitted_covid_19_intensive_care_patients()
        self._calculate_possible_infection_date(days_from_symptoms_to_intensiv_care, days_incubation_period)

        self._calculate_proportional_columns()

        self = self.dropna(how="all", axis=0)

        if to_csv:
            if path is None:
                path = IntensiveRegisterDataFrame._path
            self.to_csv(path)

    def _delete_outliers(self) -> None:
        """The 'DIVI Intensivregister' reports outliers because of bigger corrections of some hospitals or
        anomalies in the figures for some dates. This method deletes these outliers.
        see: https://www.intensivregister.de/#/aktuelle-lage/reports"""

        outlier_dates = [pd.to_datetime("2021-01-15"),
                         pd.to_datetime("2021-01-20")]

        outlier_columns = ['newly admitted intensive care patients with a positive COVID-19 test',
                           'with treatment completed']

        for outlier_date in outlier_dates:
            for outlier_column in outlier_columns:
                self.loc[outlier_date, outlier_column] = np.nan

    def _calculate_proportional_columns(self) -> None:

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

    def _calculate_possible_infection_date(self, days_from_symptoms_to_intensiv_care, days_incubation_period) -> None:
        intensive_register_by_infection_date = \
            self.loc[:,
            ['newly admitted intensive care patients with a positive COVID-19 test',
             'newly admitted intensive care patients with a positive COVID-19 test (mean ±3 days)',
             'R0 calculated by newly admitted intensive care patients with a positive COVID-19 test (mean ±3 days)']]

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
            'R0 calculated by newly admitted intensive care patients with a positive COVID-19 test (mean ±3 days)':
                'R0 by calculated onset of infection of newly admitted intensive care patients with a positive COVID-19 test (mean ±3 days)'
        })
        self. \
            drop(
            ['calculated start of infection of newly admitted intensive care patients with a positive COVID-19 test',
             'calculated start of infection of newly admitted intensive care patients with a positive COVID-19 test (mean ±3 days)',
             'R0 by calculated onset of infection of newly admitted intensive care patients with a positive COVID-19 test (mean ±3 days)'],
            axis=1, inplace=True)
        self.__dict__.update(self.merge(intensive_register_by_infection_date,
                                        how="outer",
                                        left_index=True,
                                        right_index=True).__dict__)

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

    def _calculate_r0_by_moving_mean_newly_admitted_covid_19_intensive_care_patients(self) -> None:

        moving_mean_newly_admitted_covid_19_intensive_care_patients_column_name = \
            'newly admitted intensive care patients with a positive COVID-19 test (mean ±3 days)'

        cases_sum_7d_to_4d_before = self. \
            calculate_sum_7d_to_4d_before_for(moving_mean_newly_admitted_covid_19_intensive_care_patients_column_name)
        cases_sum_3d_to_0d_before = self. \
            calculate_sum_3d_to_0d_before_for(moving_mean_newly_admitted_covid_19_intensive_care_patients_column_name)

        self.loc[:,
        'R0 calculated by newly admitted intensive care patients with a positive COVID-19 test (mean ±3 days)'] = \
            [cases_sum_3d_to_0d_before[i] / cases_sum_7d_to_4d_before[i]
             if cases_sum_7d_to_4d_before[i] != 0
             else np.nan
             for i in range(len(cases_sum_3d_to_0d_before))]

    def _calculate_7_day_moving_means(self) -> List[TNum]:

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

    def _calculate_number_of_used_and_unused_intensive_care_beds(self) -> None:

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

    def _calculate_changes_from_previous_day(self) -> None:

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

        self.loc[:, 'newly admitted intensive care patients with a positive COVID-19 test'] = \
            calculate_newly_admitted_covid19_intensive_care_patients()

    def _get_cases_from_intensive_register_report(self) -> None:

        def get_cases_table_from_pdf():
            pdf_table_area_cases = (262, 34, 366, 561)
            # pdf_table_area_cases = (277, 34, 380, 561)
            pdf = read_pdf(self._url_pdf,
                           encoding='utf-8',
                           guess=False,
                           stream=True,
                           multiple_tables=False,
                           pages=1,
                           area=pdf_table_area_cases,
                           pandas_options={
                               "names": ["Zeitpunkt", "Art", "Anzahl", "prozentualer Anteil", "Veränderung zum Vortag"],
                               'decimal': ",",
                               "thousands": "."}
                           )

            return pdf[0]

        def intensive_care_patients_with_positive_covid19_test(pdf):
            intensive_care_patients_with_positive_covid19_test = \
                pdf.loc[pdf.loc[:, "Art"] == "in intensivmedizinischer Behandlung", "Anzahl"].values[0]

            if isinstance(intensive_care_patients_with_positive_covid19_test, str):
                intensive_care_patients_with_positive_covid19_test = \
                    intensive_care_patients_with_positive_covid19_test.replace(".", "")
            return int(intensive_care_patients_with_positive_covid19_test)

        def invasively_ventilated(pdf):
            invasively_ventilated = pdf.loc[pdf.loc[:, "Art"] == "davon invasiv beatmet", "Anzahl"].values[0]
            if isinstance(invasively_ventilated, str):
                invasively_ventilated = invasively_ventilated.replace(".", "")
            return int(invasively_ventilated)

        def with_treatment_completed(pdf):
            with_treatment_completed = pdf.loc[pdf.loc[:, "Art"] == "mit abgeschlossener Behandlung", "Anzahl"].values[
                0]
            if isinstance(with_treatment_completed, str):
                with_treatment_completed = with_treatment_completed.replace(".", "")
            return int(with_treatment_completed)

        def thereof_deceased(pdf):
            thereof_deceased = pdf.loc[pdf.loc[:, "Art"] == "davon verstorben", "Anzahl"].values[0]
            if isinstance(thereof_deceased, str):
                thereof_deceased = thereof_deceased.replace(".", "")
            return int(thereof_deceased)

        date = self._get_date_from_intensive_register_pdf()
        pdf = get_cases_table_from_pdf()

        self.loc[date, 'intensive care patients with positive COVID-19 test'] = \
            intensive_care_patients_with_positive_covid19_test(pdf)
        self.loc[date, 'invasively ventilated'] = invasively_ventilated(pdf)
        self.loc[date, 'with treatment completed'] = with_treatment_completed(pdf)
        self.loc[date, 'thereof deceased'] = thereof_deceased(pdf)

    def _get_capacities_intensivregister_report(self) -> None:

        def get_capacities_table_from_pdf():
            pdf_table_area_capacities = (422, 34, 465, 561)
            # pdf_table_area_capacities = (437, 34, 481, 561)
            pdf = read_pdf(self._url_pdf,
                           encoding='utf-8',
                           guess=False,
                           stream=True,
                           multiple_tables=False,
                           pages=1,
                           area=pdf_table_area_capacities,
                           pandas_options={"names": ["Status", "Low-Care", "High-Care", "ECMO", "ITS-Betten gesamt",
                                                     "ITS-Betten gesamt (nur Erwachsene)",
                                                     "ITS-Betten Veränderung zum Vortag",
                                                     "ITS-Betten (nur Erwachsene) Veränderung zum Vortag",
                                                     "7-Tage-Notfallreserve", "7-Tage-Notfallreserve (nur Erwachsene)"],
                                           'decimal': ",",
                                           "thousands": "."}
                           )
            return pdf[0].set_index("Status")

        def get_last_csv_from_intensive_register_and_date():
            csv = pd.read_csv(self._url_csv)
            csv.daten_stand = pd.to_datetime(csv.daten_stand)
            csv.daten_stand = csv.daten_stand.dt.strftime('%Y-%m-%d')
            csv.daten_stand = pd.to_datetime(csv.daten_stand)
            date = csv.iloc[0]["daten_stand"]
            csv = csv.groupby("daten_stand").sum()
            return csv, date

        def emergency_reserve(pdf):
            emergency_reserve = pdf.loc["Aktuell frei", "7-Tage-Notfallreserve"]
            if isinstance(emergency_reserve, str):
                emergency_reserve = emergency_reserve.replace(".", "")
            return int(emergency_reserve)

        def number_of_reporting_areas(csv):
            return csv.iloc[0]["anzahl_meldebereiche"]

        def covid19_cases(csv):
            return csv.iloc[0]["faelle_covid_aktuell"]

        def invasively_ventilated(csv):
            return csv.iloc[0]["faelle_covid_aktuell_beatmet"]

        def free_intensive_care_beds(csv):
            return csv.iloc[0]["betten_frei"]

        date = self._get_date_from_intensive_register_pdf()
        pdf = get_capacities_table_from_pdf()

        self.loc[date, 'emergency reserve'] = emergency_reserve(pdf)

        csv, date = get_last_csv_from_intensive_register_and_date()

        self.loc[date, 'number of reporting areas'] = number_of_reporting_areas(csv)
        self.loc[date, 'COVID-19 cases'] = covid19_cases(csv)
        self.loc[date, 'invasively ventilated'] = invasively_ventilated(csv)
        self.loc[date, 'free intensive care beds'] = free_intensive_care_beds(csv)
        self.loc[date, 'occupied intensive care beds'] = csv.iloc[0]["betten_belegt"]

    def _get_date_from_intensive_register_pdf(self) -> dt.datetime:
        file = urllib.request.urlopen(self._url_pdf).read()
        file = BytesIO(file)
        pdf = PDF(file)
        date_as_str_german = pdf[0].split("bundesweit am ")[1].split(" um ")[0].replace(" ", "")
        date = pd.to_datetime(date_as_str_german, dayfirst=True)
        return date

    def get_last_date(self) -> dt.datetime:
        return self.index.max()

    def get_second_last_date(self) -> dt.datetime:
        return self.get_last_date() - pd.DateOffset(1)

    def get_last_date_for_mean_values(self) -> dt.datetime:
        return self.index.max() - pd.DateOffset(3)

    def get_second_last_date_for_mean_values(self) -> dt.datetime:
        return self.get_last_date_for_mean_values() - pd.DateOffset(1)

    def get_last_r0_by_mean_cases(self) -> float:
        last_date = self.get_last_date_for_mean_values()
        return self.loc[last_date,
                        "R0 calculated by newly admitted intensive care patients with a " \
                        "positive COVID-19 test (mean ±3 days)"]

    def get_second_last_r0_by_mean_cases(self) -> float:
        second_last_date = self.get_second_last_date_for_mean_values()
        return self.loc[second_last_date,
                        "R0 calculated by newly admitted intensive care patients with a " \
                        "positive COVID-19 test (mean ±3 days)"]

    def get_change_from_second_last_to_last_date_for_r0_by_mean_cases(self) -> float:
        return self.get_last_r0_by_mean_cases() - self.get_second_last_r0_by_mean_cases()
