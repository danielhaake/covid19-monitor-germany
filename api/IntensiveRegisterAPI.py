import urllib
from datetime import datetime
from io import BytesIO
from typing import Tuple

import numpy as np
import pandas as pd
from pdftotext import PDF
from tabula import read_pdf


class IntensiveRegisterAPI:

    _url_pdf = "https://diviexchange.blob.core.windows.net/%24web/DIVI_Intensivregister_Report.pdf"
    _url_csv = "https://diviexchange.blob.core.windows.net/%24web/DIVI_Intensivregister_Auszug_pro_Landkreis.csv"

    def get_cases_from_intensive_register_report(self, url_pdf: str = None) -> dict:

        def get_cases_df_from_pdf(pdf_bytesio: BytesIO) -> pd.DataFrame:
            pdf_table_area_cases = (231, 34, 345, 561)
            pandas_options = {"names": ["Zeitpunkt", "Art", "Anzahl", "prozentualer Anteil", "Veränderung zum Vortag"],
                              "decimal": ",",
                              "thousands": "."}
            return self._get_df_from_pdf_bytesio(pdf_bytesio, pdf_table_area_cases, pandas_options)

        def intensive_care_patients_with_positive_covid19_test(cases_df: pd.DataFrame) -> int:
            intensive_care_patients_with_positive_covid19_test = \
                cases_df.loc[cases_df.loc[:, "Art"] == "in intensivmedizinischer Behandlung", "Anzahl"].values[0]

            if isinstance(intensive_care_patients_with_positive_covid19_test, str):
                intensive_care_patients_with_positive_covid19_test = \
                    intensive_care_patients_with_positive_covid19_test.replace(".", "")
            return int(intensive_care_patients_with_positive_covid19_test)

        def invasively_ventilated(cases_df: pd.DataFrame) -> int:
            invasively_ventilated = cases_df.loc[cases_df.loc[:, "Art"] == "davon invasiv beatmet", "Anzahl"].values[0]
            if isinstance(invasively_ventilated, str):
                invasively_ventilated = invasively_ventilated.replace(".", "")
            return int(invasively_ventilated)

        def new_admissions_to_intensive_care_last_day(cases_df: pd.DataFrame) -> int:
            new_admissions_to_intensive_care = \
                cases_df.loc[cases_df.loc[:, "Art"] == "Neuaufnahmen (inkl. Verlegungen*)", "Veränderung zum Vortag"].values[0]
            if isinstance(new_admissions_to_intensive_care, str):
                new_admissions_to_intensive_care = new_admissions_to_intensive_care.replace(".", "").replace("+", "")
            return int(new_admissions_to_intensive_care)

        def with_treatment_completed(cases_df: pd.DataFrame) -> float:
            # with_treatment_completed = pdf.loc[pdf.loc[:, "Art"] == "mit abgeschlossener Behandlung", "Anzahl"].values[
            #    0]
            # if isinstance(with_treatment_completed, str):
            #    with_treatment_completed = with_treatment_completed.replace(".", "")
            # return int(with_treatment_completed)
            return np.nan

        def thereof_deceased_last_day(cases_df: pd.DataFrame) -> int:
            thereof_deceased = \
                cases_df.loc[cases_df.loc[:, "Art"] == "Verstorben auf ITS", "Veränderung zum Vortag"].values[0]
            if isinstance(thereof_deceased, str):
                thereof_deceased = thereof_deceased.replace(".", "").replace("+", "")
            return int(thereof_deceased)

        cases_dict = dict()
        pdf_bytesio = self._get_bytesio_of_pdf_from_url(url_pdf)
        cases_dict["reporting date"] = self._get_date_from_intensive_register_pdf(pdf_bytesio)
        pdf_bytesio.seek(0)
        cases_df = get_cases_df_from_pdf(pdf_bytesio)

        cases_dict['intensive care patients with positive COVID-19 test'] = \
            intensive_care_patients_with_positive_covid19_test(cases_df)
        cases_dict['invasively ventilated'] = invasively_ventilated(cases_df)
        cases_dict['newly admitted intensive care patients with a positive COVID-19 test'] = \
            new_admissions_to_intensive_care_last_day(cases_df)
        # cases_dict['with treatment completed'] = with_treatment_completed(pdf)
        cases_dict['thereof deceased (change from previous day)'] = thereof_deceased_last_day(cases_df)
        return cases_dict

    def get_capacities_from_intensive_register_report(self, url_pdf: str = None, url_csv: str = None) -> dict:

        def get_capacities_df_from_pdf(pdf_bytesio: BytesIO):
            pdf_table_area_capacities = (437, 34, 481, 561)
            pandas_options = {"names": ["Status", "Low-Care", "High-Care", "ECMO", "ITS-Betten gesamt",
                                        "ITS-Betten gesamt (nur Erwachsene)",
                                        "ITS-Betten Veränderung zum Vortag",
                                        "ITS-Betten (nur Erwachsene) Veränderung zum Vortag",
                                        "7-Tage-Notfallreserve", "7-Tage-Notfallreserve (nur Erwachsene)"],
                              'decimal': ",",
                              "thousands": "."}
            return self._get_df_from_pdf_bytesio(pdf_bytesio, pdf_table_area_capacities, pandas_options)\
                       .set_index("Status")

        def get_last_csv_from_intensive_register_and_date(url_csv: str = None):
            if url_csv is None:
                url_csv = self._url_csv
            csv = pd.read_csv(url_csv)
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
            # till 30.03.2021
            # return csv.iloc[0]["faelle_covid_aktuell_beatmet"]

            # since 31.03.2021
            return csv.iloc[0]["faelle_covid_aktuell_invasiv_beatmet"]

        def free_intensive_care_beds(csv):
            return csv.iloc[0]["betten_frei"]

        def occupied_intensive_care_beds(csv):
            return csv.iloc[0]["betten_belegt"]

        date_pdf = None
        date_csv = None
        while ((date_pdf != date_csv) |
               (date_pdf is None) | (date_csv is None)):
            pdf_bytesio = self._get_bytesio_of_pdf_from_url(url_pdf)
            date_pdf = self._get_date_from_intensive_register_pdf(pdf_bytesio)
            pdf_bytesio.seek(0)  # seek back to the beginning of the file
            capacities_df_from_csv, date_csv = get_last_csv_from_intensive_register_and_date(url_csv)

        capacities_df_from_pdf = get_capacities_df_from_pdf(pdf_bytesio)

        capacities_dict = dict()
        capacities_dict['reporting date'] = date_pdf
        capacities_dict['emergency reserve'] = emergency_reserve(capacities_df_from_pdf)
        capacities_dict['number of reporting areas'] = number_of_reporting_areas(capacities_df_from_csv)
        capacities_dict['COVID-19 cases'] = covid19_cases(capacities_df_from_csv)
        capacities_dict['invasively ventilated'] = invasively_ventilated(capacities_df_from_csv)
        capacities_dict['free intensive care beds'] = free_intensive_care_beds(capacities_df_from_csv)
        capacities_dict['occupied intensive care beds'] = occupied_intensive_care_beds(capacities_df_from_csv)
        return capacities_dict

    def _get_date_from_intensive_register_pdf(self, pdf_bytesio: BytesIO) -> datetime:
        # file = self._get_bytesio_of_pdf_from_url(url_pdf)
        pdf = PDF(pdf_bytesio)
        date_as_str_german = pdf[0].split("bundesweit am ")[1].split(" um ")[0].replace(" ", "")
        date = pd.to_datetime(date_as_str_german, dayfirst=True)
        return date

    def _get_bytesio_of_pdf_from_url(self, url: str = None) -> BytesIO:
        if url is None:
            url = self._url_pdf
        file = urllib.request.urlopen(url).read()
        return BytesIO(file)

    def _get_df_from_pdf_bytesio(self, pdf_bytesio: BytesIO,
                                 area_of_table_in_pdf: Tuple[int, int, int, int],
                                 pandas_options: dict) -> pd.DataFrame:
        pdf = read_pdf(pdf_bytesio,
                       encoding='utf-8',
                       guess=False,
                       stream=True,
                       multiple_tables=False,
                       pages=1,
                       area=area_of_table_in_pdf,
                       pandas_options=pandas_options
                       )

        return pdf[0]
