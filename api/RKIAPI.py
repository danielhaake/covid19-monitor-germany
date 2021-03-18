from datetime import datetime
from io import BytesIO
from typing import Tuple, List

import pandas as pd
import requests


class RKIAPI():

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
                                                      'attributes.date': 'data status'})
        cases_by_date.loc[:, 'reference date'] = pd.to_datetime(cases_by_date.loc[:, 'reference date'], unit='ms')
        cases_by_date = cases_by_date.set_index("reference date")
        cases_by_date = cases_by_date.sort_index()
        return cases_by_date

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
            response = requests.get(url)
            file_object = BytesIO(response.content)
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
            response = requests.get(url)
            file_object = BytesIO(response.content)

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
                            "Obere Grenze des 95%-Prädiktionsintervalls des 7-Tage-R Wertes"]
                 ]
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


