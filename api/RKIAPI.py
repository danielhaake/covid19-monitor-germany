from datetime import datetime
from io import BytesIO
from typing import Tuple, List

import pandas as pd
import requests


class RKIAPI:

    def new_reported_cases(self) -> Tuple[int, datetime]:
        return self._get_figure_from_rki_api(where='NeuerFall%20IN(1,-1)',
                                             out_fields='AnzahlFall,Datenstand',
                                             sum_statistic_field='AnzahlFall')

    def total_number_of_reported_cases(self) -> Tuple[int, datetime]:
        return self._get_figure_from_rki_api(where='NeuerFall%20IN(1,0)',
                                             out_fields='AnzahlFall,Datenstand',
                                             sum_statistic_field='AnzahlFall')

    def new_reported_deaths(self) -> Tuple[int, datetime]:
        return self._get_figure_from_rki_api(where='NeuerTodesfall%20IN(1,-1)',
                                             out_fields='AnzahlTodesfall,Datenstand',
                                             sum_statistic_field='AnzahlTodesfall')

    def total_number_of_reported_deaths(self) -> Tuple[int, datetime]:
        return self._get_figure_from_rki_api(where='NeuerTodesfall%20IN(1,0)',
                                             out_fields='AnzahlTodesfall,Datenstand',
                                             sum_statistic_field='AnzahlTodesfall')

    def total_number_of_cases_by_reference_date(self) -> Tuple[pd.Series, datetime]:
        return self._get_series_from_rki_api(where='NeuerFall%20IN(1,0)',
                                             out_fields='AnzahlFall,Refdatum',
                                             sum_statistic_field='AnzahlFall',
                                             group_by_field='Refdatum',
                                             column_name='cases by reference date '
                                                         '(start of illness, alternatively reporting date)')

    def total_number_of_cases_by_reference_date_with_known_start_of_illness(self) -> Tuple[pd.Series, datetime]:
        return self._get_series_from_rki_api(where='NeuerFall%20IN(1,0)%20AND%20'
                                                   'IstErkrankungsbeginn=1',
                                             out_fields='AnzahlFall,Refdatum',
                                             sum_statistic_field='AnzahlFall',
                                             group_by_field='Refdatum',
                                             column_name='cases with reported start of illness')

    def total_number_of_cases_by_reference_date_with_unknown_start_of_illness(self) -> Tuple[pd.Series, datetime]:
        return self._get_series_from_rki_api(where='NeuerFall%20IN(1,0)%20AND%20'
                                                   'IstErkrankungsbeginn=0',
                                             out_fields='AnzahlFall,Refdatum',
                                             sum_statistic_field='AnzahlFall',
                                             group_by_field='Refdatum',
                                             column_name='cases with unknown start of illness (reporting date)')

    def total_number_of_cases_by_reporting_date(self) -> Tuple[pd.Series, datetime]:
        return self._get_series_from_rki_api(where='NeuerFall%20IN(1,0)',
                                             out_fields='AnzahlFall,Meldedatum',
                                             sum_statistic_field='AnzahlFall',
                                             group_by_field='Meldedatum',
                                             column_name='cases by reporting date')

    def total_number_of_deaths_by_reference_date(self) -> Tuple[pd.Series, datetime]:
        return self._get_series_from_rki_api(where='NeuerTodesfall%20IN(1,0)',
                                             out_fields='AnzahlTodesfall,Refdatum',
                                             sum_statistic_field='AnzahlTodesfall',
                                             group_by_field='Refdatum',
                                             column_name='deaths by reference date '
                                                         '(start of illness, alternatively reporting date)')

    def total_number_of_deaths_by_reference_date_with_known_start_of_illness(self) -> Tuple[pd.Series, datetime]:
        return self._get_series_from_rki_api(where='NeuerTodesfall%20IN(1,0)%20AND%20'
                                                   'IstErkrankungsbeginn=1',
                                             out_fields='AnzahlTodesfall,Refdatum',
                                             sum_statistic_field='AnzahlTodesfall',
                                             group_by_field='Refdatum',
                                             column_name='deaths with reported start of illness')

    def total_number_of_deaths_by_reference_date_with_unknown_start_of_illness(self) -> Tuple[pd.Series, datetime]:
        return self._get_series_from_rki_api(where='NeuerTodesfall%20IN(1,0)%20AND%20'
                                                   'IstErkrankungsbeginn=0',
                                             out_fields='AnzahlTodesfall,Refdatum',
                                             sum_statistic_field='AnzahlTodesfall',
                                             group_by_field='Refdatum',
                                             column_name='deaths with unknown start of illness (reporting date)')

    def total_number_of_deaths_by_reporting_date(self) -> Tuple[pd.Series, datetime]:
        return self._get_series_from_rki_api(where='NeuerTodesfall%20IN(1,0)',
                                             out_fields='AnzahlTodesfall,Meldedatum',
                                             sum_statistic_field='AnzahlTodesfall',
                                             group_by_field='Meldedatum',
                                             column_name='deaths by reporting date')

    def new_reported_cases_by_reference_date(self) -> Tuple[pd.Series, datetime]:
        return self._get_series_from_rki_api(where='NeuerFall%20IN(1,-1)',
                                             out_fields='AnzahlFall,Refdatum',
                                             sum_statistic_field='AnzahlFall',
                                             group_by_field='Refdatum',
                                             column_name='new reported cases by reference date '
                                                         '(start of illness, alternatively reporting date)')

    def new_reported_cases_by_reference_date_with_known_start_of_illness(self) -> Tuple[pd.Series, datetime]:
        return self._get_series_from_rki_api(where='NeuerFall%20IN(1,-1)%20AND%20'
                                                   'IstErkrankungsbeginn=1',
                                             out_fields='AnzahlFall,Refdatum',
                                             sum_statistic_field='AnzahlFall',
                                             group_by_field='Refdatum',
                                             column_name='new reported cases with known start of illness')

    def new_reported_cases_by_reference_date_with_unknown_start_of_illness(self) -> Tuple[pd.Series, datetime]:
        return self._get_series_from_rki_api(where='NeuerFall%20IN(1,-1)%20AND%20'
                                                   'IstErkrankungsbeginn=0',
                                             out_fields='AnzahlFall,Refdatum',
                                             sum_statistic_field='AnzahlFall',
                                             group_by_field='Refdatum',
                                             column_name='new reported cases with unknown start of illness '
                                                         '(reporting date)')

    def new_reported_cases_by_reporting_date(self) -> Tuple[pd.Series, datetime]:
        return self._get_series_from_rki_api(where='NeuerFall%20IN(1,-1)',
                                             out_fields='AnzahlFall,Meldedatum',
                                             sum_statistic_field='AnzahlFall',
                                             group_by_field='Meldedatum',
                                             column_name='new reported cases by reporting date')

    def new_reported_deaths_by_reference_date(self) -> Tuple[pd.Series, datetime]:
        return self._get_series_from_rki_api(where='NeuerTodesfall%20IN(1,-1)',
                                             out_fields='AnzahlTodesfall,Refdatum',
                                             sum_statistic_field='AnzahlTodesfall',
                                             group_by_field='Refdatum',
                                             column_name='new reported deaths by reference date '
                                                         '(start of illness, alternatively reporting date)')

    def new_reported_deaths_by_reference_date_with_known_start_of_illness(self) -> Tuple[pd.Series, datetime]:
        return self._get_series_from_rki_api(where='NeuerTodesfall%20IN(1,-1)%20AND%20'
                                                   'IstErkrankungsbeginn=1',
                                             out_fields='AnzahlTodesfall,Refdatum',
                                             sum_statistic_field='AnzahlTodesfall',
                                             group_by_field='Refdatum',
                                             column_name='new reported deaths with known start of illness')

    def new_reported_deaths_by_reference_date_with_unknown_start_of_illness(self) -> Tuple[pd.Series, datetime]:
        return self._get_series_from_rki_api(where='NeuerTodesfall%20IN(1,-1)%20AND%20'
                                                   'IstErkrankungsbeginn=0',
                                             out_fields='AnzahlTodesfall,Refdatum',
                                             sum_statistic_field='AnzahlTodesfall',
                                             group_by_field='Refdatum',
                                             column_name='new reported deaths with unknown start of illness '
                                                         '(reporting date)')

    def new_reported_deaths_by_reporting_date(self) -> Tuple[pd.Series, datetime]:
        return self._get_series_from_rki_api(where='NeuerTodesfall%20IN(1,-1)',
                                             out_fields='AnzahlTodesfall,Meldedatum',
                                             sum_statistic_field='AnzahlTodesfall',
                                             group_by_field='Meldedatum',
                                             column_name='new reported deaths by reporting date')

    def new_reported_cases_by_age_group(self) -> Tuple[pd.Series, datetime]:
        return self._get_cases_by_age_group_from_rki_api(where='NeuerFall%20IN(-1,1)',
                                                         out_fields='AnzahlFall,Altersgruppe',
                                                         sum_statistic_field='AnzahlFall',
                                                         group_by_field='Altersgruppe',
                                                         column_name='new reported cases')

    def total_number_of_reported_cases_by_age_group(self) -> Tuple[pd.Series, datetime]:
        return self._get_cases_by_age_group_from_rki_api(where='NeuerFall%20IN(1,0)',
                                                         out_fields='AnzahlFall,Altersgruppe',
                                                         sum_statistic_field='AnzahlFall',
                                                         group_by_field='Altersgruppe',
                                                         column_name='total reported cases')

    def new_reported_deaths_by_age_group(self) -> Tuple[pd.Series, datetime]:
        return self._get_cases_by_age_group_from_rki_api(where='NeuerTodesfall%20IN(1,-1)',
                                                         out_fields='AnzahlTodesfall,Altersgruppe',
                                                         sum_statistic_field='AnzahlTodesfall',
                                                         group_by_field='Altersgruppe',
                                                         column_name='new reported deaths')

    def total_number_of_reported_deaths_by_age_group(self) -> Tuple[pd.Series, datetime]:
        return self._get_cases_by_age_group_from_rki_api(where='NeuerTodesfall%20IN(1,0)',
                                                         out_fields='AnzahlTodesfall,Altersgruppe',
                                                         sum_statistic_field='AnzahlTodesfall',
                                                         group_by_field='Altersgruppe',
                                                         column_name='total reported deaths')

    def _get_figure_from_rki_api(self,
                                 where: str,
                                 out_fields: str,
                                 sum_statistic_field: str) -> Tuple[int, datetime]:

        data = self._get_json_response_from_rki_api(where=where,
                                                    out_fields=out_fields,
                                                    sum_statistic_field=sum_statistic_field)

        cases = int(data["features"][0]["attributes"]["cases"])
        datetime_str_german = data["features"][0]["attributes"]["date"]
        date = pd.to_datetime(datetime_str_german.split(",")[0], dayfirst=True)

        return cases, date

    def _get_series_from_rki_api(self,
                                 where: str,
                                 out_fields: str,
                                 sum_statistic_field: str,
                                 group_by_field: str,
                                 column_name: str) -> Tuple[pd.Series, datetime]:

        data = self._get_json_response_from_rki_api(where=where,
                                                    out_fields=out_fields,
                                                    sum_statistic_field=sum_statistic_field,
                                                    group_by_field=group_by_field)

        cases_by_date = self._get_cases_by_date_from_json(data, column_name)

        datetime_of_data_status_str_german = cases_by_date.iloc[0, :]["data status"]
        datetime_of_data_status = pd.to_datetime(datetime_of_data_status_str_german.split(",")[0], dayfirst=True)

        return cases_by_date.loc[:, column_name], datetime_of_data_status

    def _get_cases_by_date_from_json(self, data: dict, column_name: str) -> pd.DataFrame:
        cases_by_date = pd.json_normalize(data["features"])
        cases_by_date = cases_by_date.rename(columns={'attributes.cases': column_name,
                                                      'attributes.Refdatum': 'reference date',
                                                      'attributes.Meldedatum': 'reporting date',
                                                      'attributes.date': 'data status'})
        date_column = 'reference date'
        if 'reporting date' in cases_by_date.columns:
            date_column = 'reporting date'
        cases_by_date.loc[:, date_column] = pd.to_datetime(cases_by_date.loc[:, date_column], unit='ms')
        cases_by_date = cases_by_date.set_index(date_column)
        cases_by_date = cases_by_date.sort_index()
        return cases_by_date

    def _get_cases_by_age_group_from_rki_api(self,
                                 where: str,
                                 out_fields: str,
                                 sum_statistic_field: str,
                                 group_by_field: str,
                                 column_name: str) -> Tuple[pd.Series, datetime]:
        data = self._get_json_response_from_rki_api(where=where,
                                                    out_fields=out_fields,
                                                    sum_statistic_field=sum_statistic_field,
                                                    group_by_field=group_by_field)

        cases_by_age_group = self._get_cases_by_age_group_from_json(data, column_name)

        datetime_of_data_status_str_german = cases_by_age_group.iloc[0, :]["data status"]
        datetime_of_data_status = pd.to_datetime(datetime_of_data_status_str_german.split(",")[0], dayfirst=True)

        return cases_by_age_group.loc[:, column_name], datetime_of_data_status

    def _get_cases_by_age_group_from_json(self, data: dict, column_name: str) -> pd.DataFrame:
        cases_by_age_group = pd.json_normalize(data["features"])
        cases_by_age_group = cases_by_age_group.rename(columns={'attributes.cases': column_name,
                                                                'attributes.Altersgruppe': 'age group',
                                                                'attributes.date': 'data status'})
        cases_by_age_group = cases_by_age_group.set_index("age group")

        if "unbekannt" in cases_by_age_group.index:
            cases_by_age_group = \
                cases_by_age_group.rename(index={"unbekannt": "unknown"})
        return cases_by_age_group.sort_index()

    def _get_json_response_from_rki_api(self,
                                        where: str,
                                        out_fields: str,
                                        sum_statistic_field: str,
                                        group_by_field: str = '') -> dict:
        url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_COVID19/FeatureServer/0/' \
              f'query?where={where}' \
              '&objectIds=' \
              '&time=' \
              '&resultType=standard' \
              f'&outFields={out_fields}' \
              '&returnIdsOnly=false' \
              '&returnUniqueIdsOnly=false' \
              '&returnCountOnly=false' \
              '&returnDistinctValues=false' \
              '&cacheHint=false' \
              f'&groupByFieldsForStatistics={group_by_field}' \
              '&outStatistics=[' \
                '{%22statisticType%22:%22sum%22,' \
                f'%22onStatisticField%22:%22{sum_statistic_field}%22,' \
                 '%22outStatisticFieldName%22:%22cases%22},' \
                '{%22statisticType%22:%22max%22,' \
                 '%22onStatisticField%22:%22Datenstand%22,' \
                 '%22outStatisticFieldName%22:%22date%22}' \
              ']' \
              '&having=' \
              '&resultOffset=' \
              '&resultRecordCount=' \
              '&sqlFormat=none' \
              '&f=pjson' \
              '&token='
        response = requests.get(url)
        return response.json()

    def initial_loading_of_cases_and_deaths(self) -> pd.DataFrame:
        """
        Normally we don't need this method, because we have our data stored in a csv file and we only have to update
        this file with new data of the day. But if we don't have data stored, we can get old data with this method. But
        with the normal API we get the data earlier in the day. This method also delivers no new data at the weekend. It
        is also possible, that the column name change over time, which can result into problems. Sometimes there are
        misspellings in the data of the Excel file, which is also problematic. The normal API is stable for those
        problems, so that the API should be preferred.
        """
        def load_cases_and_deaths_from_excel() -> pd.DataFrame:
            url = 'https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Daten/' \
                  'Fallzahlen_Kum_Tab.xlsx?__blob=publicationFile'
            file_object = self._get_bytesio_from_request(url)
            return pd.read_excel(file_object, sheet_name="Fälle-Todesfälle-gesamt", header=2) \
                     .dropna(how="all", axis='columns') \
                     .dropna(how="all", axis='index')

        def set_values_to_datetime(df: pd.DataFrame, column: str) -> List[datetime]:
            return [df.loc[index, column]
                    if isinstance(df.loc[index, column], datetime)
                    else pd.to_datetime(df.loc[index, column], dayfirst=True)
                    for index in df.index]

        def rename_columns_from_german_to_english(df: pd.DataFrame) -> pd.DataFrame:
            return df.rename(columns={'Berichtsdatum': 'RKI reporting date',
                                      'Differenz Vortag Fälle': 'cases',
                                      'Differenz Vortag Todesfälle': 'deaths',
                                      'Anzahl COVID-19-Fälle': 'cases cumulative',
                                      'Todesfälle': 'deaths cumulative',
                                      'Fall-Verstorbenen-Anteil': 'case fatility rate (CFR)',
                                      'Fälle ohne Todesfälle': 'non-deceased reported cases'})

        def calculate_date_and_set_as_index(df: pd.DataFrame) -> pd.DataFrame:
            """
            'RKI reporting date' is from beginning of the day (00:00),
            so the cases and deaths are reported one day earlier to the RKI
            """
            df.loc[:, 'date'] = df.loc[:, 'RKI reporting date'] - pd.DateOffset(1)
            df = df.sort_values("date")
            return df.set_index("date")

        rki_cases_and_deaths = load_cases_and_deaths_from_excel()
        rki_cases_and_deaths = rename_columns_from_german_to_english(rki_cases_and_deaths)
        rki_cases_and_deaths.loc[:, 'RKI reporting date'] = set_values_to_datetime(rki_cases_and_deaths,
                                                                                   "RKI reporting date")
        rki_cases_and_deaths = calculate_date_and_set_as_index(rki_cases_and_deaths)

        return rki_cases_and_deaths

    def nowcast(self) -> pd.DataFrame:
        def load_nowcast_from_excel() -> pd.DataFrame:
            url = 'https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Projekte_RKI/' \
                  'Nowcasting_Zahlen.xlsx?__blob=publicationFile'
            file_object = self._get_bytesio_from_request(url)

            dateparse = lambda x: datetime.strptime(x, '%d.%m.%Y')
            return pd.read_excel(file_object,
                                 sheet_name=1,
                                 header=0,
                                 thousands=".",
                                 parse_dates=['Datum des Erkrankungsbeginns'],
                                 date_parser=dateparse)\
                     .replace(",", ".", regex=True)

        def subset_of_df_with_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
            df = df.loc[:, ["Datum des Erkrankungsbeginns",
                            "Punktschätzer der Anzahl Neuerkrankungen",
                            "Untere Grenze des 95%-Prädiktionsintervalls der Anzahl Neuerkrankungen",
                            "Obere Grenze des 95%-Prädiktionsintervalls der Anzahl Neuerkrankungen",
                            "Punktschätzer des 7-Tage-R Wertes",
                            "Untere Grenze des 95%-Prädiktionsintervalls des 7-Tage-R Wertes",
                            "Obere Grenze des 95%-Prädiktionsintervalls des 7-Tage-R Wertes"]]
            df.loc[:, "Datum des Erkrankungsbeginns"] = pd.to_datetime(df.loc[:, "Datum des Erkrankungsbeginns"])
            return df

        def rename_columns_from_german_to_english_and_set_index(df: pd.DataFrame) -> pd.DataFrame:
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

        nowcast_rki = load_nowcast_from_excel()
        nowcast_rki = subset_of_df_with_datetime_columns(nowcast_rki)
        nowcast_rki = rename_columns_from_german_to_english_and_set_index(nowcast_rki)
        return nowcast_rki

    def clinical_aspects(self) -> pd.DataFrame:

        def load_clinical_aspects_from_excel() -> pd.DataFrame:
            url = "https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Daten/" \
                  "Klinische_Aspekte.xlsx?__blob=publicationFile"
            file_object = self._get_bytesio_from_request(url)

            try:
                clinical_aspects = pd.read_excel(file_object, sheet_name="Daten", header=1)\
                                     .dropna(how="all", axis=1)
            except:
                clinical_aspects = pd.read_excel(file_object, sheet_name=0, header=1)\
                                     .dropna(how="all", axis=1)

            return clinical_aspects

        def rename_columns_from_german_to_english(df: pd.DataFrame) -> pd.DataFrame:
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

        def create_calendar_week_and_set_as_index(df: pd.DataFrame) -> pd.DataFrame:
            calendar_week = df.loc[:, 'reporting year'].astype(str) + ' - ' + df.loc[:, 'reporting week'].astype(str)
            df.loc[:, 'calendar week'] = calendar_week
            df = df.set_index('calendar week')
            return df

        def append_proportional_columns_in_percent(df: pd.DataFrame):
            df.loc[:, 'no symptoms or no symptoms significant for COVID-19 in %'] = \
                convert_to_percent_for(df.loc[:, "proportion of no symptoms or no symptoms significant for COVID-19"])
            df.loc[:, 'hospitalized in %'] = convert_to_percent_for(df.loc[:, "proportion hospitalized"])
            df.loc[:, 'deceased in %'] = convert_to_percent_for(df.loc[:, "proportion deceased"])
            return df

        def convert_to_percent_for(series: pd.Series) -> pd.Series:
            if series.dtype == "float64":
                return series * 100
            return series.str.replace(" %", "")

        df = load_clinical_aspects_from_excel()
        df = rename_columns_from_german_to_english(df)
        df = create_calendar_week_and_set_as_index(df)
        df = append_proportional_columns_in_percent(df)
        return df

    def number_pcr_tests(self) -> pd.DataFrame:
        def load_number_pcr_tests_from_excel() -> pd.DataFrame:
            url = 'https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Daten/' \
                  'Testzahlen-gesamt.xlsx?__blob=publicationFile'
            file_object = self._get_bytesio_from_request(url)
            return pd.read_excel(file_object, sheet_name="1_Testzahlerfassung")

        def rename_columns_german_to_english(df: pd.DataFrame) -> pd.DataFrame:
            return df.rename(columns={'Anzahl Testungen': 'number of tests',
                                      'Positiv getestet': 'positive tested',
                                      'Kalenderwoche': 'calendar week',
                                      'Positivenquote (%)': 'positive rate (%)',
                                      'Positivenanteil (%)': 'positive rate (%)',
                                      'Anzahl übermittelnder Labore': 'number of transmitting laboratories'
                                      })

        def cleaning_because_of_calendar_week_column_and_set_as_index(df: pd.DataFrame) -> pd.DataFrame:
            df.loc[df.loc[:, "calendar week"] == "Bis einschließlich KW10, 2020", :"calendar week"] = "10/2020"

            first_not_included_row = df.loc[df.loc[:, "calendar week"] == "Summe"].index[0]
            df.loc[:, "calendar week"] = df.loc[:, "calendar week"].astype("str")
            df.loc[:, "calendar week"] = df.loc[:, "calendar week"].str.replace("*", "", regex=True)

            calendar_week_splitted = df.loc[:, "calendar week"].str.split("/")
            df.loc[:, "week of year"] = calendar_week_splitted.str[0]
            df.loc[:, "year"] = calendar_week_splitted.str[1]
            df.loc[:, "calendar week"] = df.loc[:, "year"] + " - " + df.loc[:, "week of year"]
            df.loc[df.loc[:, "calendar week"] == "2020 - 10", :"calendar week"] = "≤ 2020 - 10"
            df = df.iloc[:first_not_included_row, :]
            return df.set_index("calendar week")

        number_pcr_tests = load_number_pcr_tests_from_excel()
        number_pcr_tests = rename_columns_german_to_english(number_pcr_tests)
        number_pcr_tests = cleaning_because_of_calendar_week_column_and_set_as_index(number_pcr_tests)
        return number_pcr_tests

    def _get_bytesio_from_request(self, excel_file_url: str) -> BytesIO:
        response = requests.get(excel_file_url)
        return BytesIO(response.content)