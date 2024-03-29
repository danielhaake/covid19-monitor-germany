# ------------------------------ CREATE PLOTS ----------------------------------------#
import time

import logging
from typing import List, TypeVar

import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html

import configparser
import json

import plotly.express as px
from plotly.subplots import make_subplots
from plotly.graph_objects import Figure

import pandas as pd
import numpy as np

from data_pandas_subclasses.date_index_classes.CoronaCasesAndDeaths import CoronaCasesAndDeathsDataFrame, \
    CoronaCasesAndDeathsSeries
from data_pandas_subclasses.date_index_classes.NowcastRKI import NowcastRKIDataFrame
from data_pandas_subclasses.AgeDistribution import AgeDistributionDataFrame
from data_pandas_subclasses.week_index_classes.ClinicalAspects import ClinicalAspectsDataFrame
from data_pandas_subclasses.week_index_classes.CasesPerOutbreak import CasesPerOutbreakDataFrame
from data_pandas_subclasses.week_index_classes.DeathsByWeekOfDeathAndAgeGroup import \
    DeathsByWeekOfDeathAndAgeGroupDataFrame
from data_pandas_subclasses.date_index_classes.IntensiveRegister import IntensiveRegisterDataFrame
from data_pandas_subclasses.week_index_classes.NumberPCRTests import NumberPCRTestsDataFrame
from data_pandas_subclasses.week_index_classes.MedianAndMeanAges import MedianAndMeanAgesDataFrame
from layout.DailyFiguresDict import DailyFiguresDict

logging.basicConfig(level=logging.INFO)
THtml = TypeVar('THtml', html.H1, html.H2, html.H3, html.H4, html.H5, html.H6, html.Br, html.A, html.Hr, str)
TNum = TypeVar('TNum', int, float)


class Layout:

    def __init__(self):
        self.config = configparser.ConfigParser(interpolation=None)
        self.config.read('layout/graph_definitions.ini')

    def layout(self) -> html.Div:
        return html.Div(
            id='layout',
            children=[
                html.Header(
                    id='headline',
                    children=self._headline()
                ),
                html.Div(
                    id='tabs-with-graphs-and-figures',
                    children=[
                        dcc.Interval('graph-update',
                                     interval=600000,
                                     n_intervals=0),
                        dbc.Tabs(id='tabs-global-overview',
                                 className='nav-justified',  # bootstrap class name for justified navigation tabs
                                 children=self.tabs_with_graphs())
                    ]
                ),
                html.Div(
                    id='warning-message',
                    children=self._warning_message()
                ),
                html.Footer(
                    id='footer',
                    children=self._footer()
                )
            ]
        )

    def _headline(self) -> List[THtml]:
        return [
            html.H3(id='app-title',
                    children='COVID-19 MONITOR GERMANY'),
            html.Hr()
        ]

    def _footer(self) -> List[THtml]:
        return [
            html.Hr(),
            "developed by ",
            html.A(
                "Daniel Haake",
                href='https://www.linkedin.com/in/daniel-haake/',
                target='_blank'),
            " with support from ",
            html.A(
                "Christian Kirifidis",
                href='https://www.linkedin.com/in/christian-kirifidis/',
                target='_blank'),
            html.Br(),
#            html.A(
#                "Impressum",
#                href='https://www.unbelievable-machine.com/impressum/')
        ]

    def _warning_message(self) -> List[THtml]:
        return [
            html.Br(),
            "This website is only viewable in landscape mode.",
            html.Br(),
            html.Br(),
            "Please rotate your screen."
        ]

    def tabs_with_graphs(self) -> List[dcc.Tab]:
        # ----------------------------- LOAD DATA AS DATAFRAMES ----------------------#
        logging.info("START LOADING OF DATAFRAMES")
        start_time = time.time()
        corona_cases_and_deaths = CoronaCasesAndDeathsDataFrame.from_csv()
        nowcast_rki = NowcastRKIDataFrame.from_csv()
        number_pcr_tests = NumberPCRTestsDataFrame.from_csv()
        intensive_register = IntensiveRegisterDataFrame.from_csv()
        clinical_aspects = ClinicalAspectsDataFrame.from_csv()
        median_and_mean_ages = MedianAndMeanAgesDataFrame.from_csv()
        age_distribution = AgeDistributionDataFrame.from_csv()
        cases_per_outbreak = CasesPerOutbreakDataFrame.from_csv()
        deaths_by_week_of_death_and_age_group = DeathsByWeekOfDeathAndAgeGroupDataFrame.from_csv()
        end_time = time.time()
        logging.info(f"FINISHED LOADING OF DATAFRAMES IN {end_time - start_time} SECONDS")

        # ----------------------------- LOAD DATA FOR DAILY OVERVIEW ----------------------#

        daily_figures = self._get_daily_figures(corona_cases_and_deaths, nowcast_rki, intensive_register)

        # TAB STYLING
        # https://dash.plotly.com/dash-core-components/tabs

        return [dbc.Tab(label='Daily Overview',
                        labelClassName='tab',
                        activeLabelClassName='tab-selected',
                        id='tab-daily-overview',
                        children=self._tab_daily_overview(daily_figures,
                                                          corona_cases_and_deaths,
                                                          nowcast_rki)
                        ),

                dbc.Tab(label='Corona cases',
                        labelClassName='tab',
                        activeLabelClassName='tab-selected',
                        id='tab-corona-cases',
                        children=self._tab_corona_cases(corona_cases_and_deaths,
                                                        nowcast_rki,
                                                        number_pcr_tests,
                                                        clinical_aspects,
                                                        median_and_mean_ages,
                                                        age_distribution,
                                                        cases_per_outbreak,
                                                        deaths_by_week_of_death_and_age_group)
                        ),

                dbc.Tab(label='Intensive care',
                        labelClassName='tab',
                        activeLabelClassName='tab-selected',
                        id='tab-intensive-care',
                        children=self._tab_corona_intensive_care(intensive_register)
                        ),

                dbc.Tab(label='Data sources description',
                        labelClassName='tab',
                        activeLabelClassName='tab-selected',
                        id='tab-data-sources-description',
                        children=self._tab_data_sources_description()
                        )
                ]

    def _tab_daily_overview(self,
                            daily_figures: DailyFiguresDict,
                            corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                            nowcast_rki: NowcastRKIDataFrame) -> List[html.Div]:

        return [html.Div(className="daily-overview-figures",
                         children=[
                             html.Div(
                                 className='daily-overview-single-figure',
                                 id='daily-overview-cases',
                                 children=self._block_daily_overview_cases(daily_figures)
                             ),
                             html.Div(
                                 className='daily-overview-single-figure',
                                 id='daily-overview-deaths',
                                 children=self._block_daily_overview_deaths(daily_figures)
                             ),
                             html.Div(
                                 className='daily-overview-single-figure',
                                 id='daily-overview-r-value',
                                 children=self._block_daily_overview_r_value(daily_figures)
                             ),
                             html.Div(
                                 className='daily-overview-single-figure',
                                 id='daily-overview-last-7-days',
                                 children=self._block_daily_overview_last_7_days(daily_figures)
                             )
                         ]
                         ),
                html.Div(className='daily-overview-plots',
                         children=[
                             dcc.Graph(
                                 id='graph-new-deaths-by-refdate',
                                 figure=self._figure_new_deaths_by_refdate(corona_cases_and_deaths, nowcast_rki)),
                             dcc.Graph(
                                 id='graph-new-cases-by-reporting-date',
                                 figure=self._figure_new_cases_by_reporting_date(corona_cases_and_deaths, nowcast_rki))
                         ]
                         )
                ]

    def _tab_corona_cases(self,
                          corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                          nowcast_rki: NowcastRKIDataFrame,
                          number_pcr_tests: NumberPCRTestsDataFrame,
                          clinical_aspects: ClinicalAspectsDataFrame,
                          median_and_mean_ages: MedianAndMeanAgesDataFrame,
                          age_distribution: AgeDistributionDataFrame,
                          cases_per_outbreak: CasesPerOutbreakDataFrame,
                          deaths_by_week_of_death_and_age_group: DeathsByWeekOfDeathAndAgeGroupDataFrame) \
            -> List[dcc.Graph]:
        return [
            dcc.Graph(
                id='graph-cases-mean-3',
                figure=self._figure_cases_mean_3(corona_cases_and_deaths, nowcast_rki)),
            dcc.Graph(
                id='graph-total-cases-by-refdate',
                figure=self._figure_total_cases_by_refdate(corona_cases_and_deaths, nowcast_rki)),
            dcc.Graph(
                id='graph-deaths-mean-3',
                figure=self._figure_deaths_mean_3(corona_cases_and_deaths, nowcast_rki)),
            dcc.Graph(
                id='graph-total-deaths-by-refdate',
                figure=self._figure_total_deaths_by_refdate(corona_cases_and_deaths, nowcast_rki)),
            dcc.Graph(
                id='graph-r-value',
                figure=self._figure_r_value(corona_cases_and_deaths, nowcast_rki)),
            dcc.Graph(
                id='graph-7d-incidence',
                figure=self._figure_7d_incidences(corona_cases_and_deaths, nowcast_rki)),
            dcc.Graph(
                id='graph-fig-tested',
                figure=self._figure_pcr_tests(number_pcr_tests)),
            dcc.Graph(
                id='graph-fig-clinical-aspects',
                figure=self._figure_clinical_aspects(clinical_aspects)),
            self._dropdown_for_median_and_mean_ages(),
            dcc.Graph(
                id='graph-fig-median_ages',
                figure=self._figure_median_or_mean_ages(median_and_mean_ages)),
            dcc.Graph(
                id='graph-fig-mean_ages',
                figure=self._figure_median_or_mean_ages(median_and_mean_ages, median=False)),
            self._dropdown_for_hospitalizations_per_age_group(),
            dcc.Graph(
                id='graph-fig-hospitalizations-per-age-group-bar-plot',
                figure=self._figure_hospitalizations_per_age_group(clinical_aspects, type='bar')),
            dcc.Graph(
                id='graph-fig-hospitalizations-per-age-group-line-plot',
                figure=self._figure_hospitalizations_per_age_group(clinical_aspects, type='line')),
            self._dropdown_for_deaths_by_week_of_death_and_age_group(),
            dcc.Graph(
                id='graph-fig-deaths-by-week-and-age-group-bar-plot',
                figure=self._figure_deaths_by_week_of_death_and_age_group(deaths_by_week_of_death_and_age_group,
                                                                          type='bar')),
            dcc.Graph(
                id='graph-fig-deaths-by-week-and-age-group-line-plot',
                figure=self._figure_deaths_by_week_of_death_and_age_group(deaths_by_week_of_death_and_age_group,
                                                                          type='line')),
            dcc.Graph(
                id='graph-fig-deaths-in-percent-by-week-and-age-group-bar-plot',
                figure=self._figure_deaths_by_week_of_death_and_age_group_in_percent(deaths_by_week_of_death_and_age_group,
                                                                                     type='bar')),
            dcc.Graph(
                id='graph-fig-deaths-in-percent-by-week-and-age-group-line-plot',
                figure=self._figure_deaths_by_week_of_death_and_age_group_in_percent(deaths_by_week_of_death_and_age_group,
                                                                                     type='line')),
            dcc.Graph(
                id='graph-fig-distribution-of-inhabitants-and-deaths',
                figure=self._figure_distribution_of_inhabitants_and_deaths(age_distribution)),
            dcc.Graph(
                id='graph-fig-distribution-of-cases-and-deaths-per-n-inhabitants',
                figure=self._figure_distribution_of_cases_and_deaths_per_n_inhabitants(age_distribution)),
            self._dropdown_for_cases_per_outbreak(),
            dcc.Graph(
                id='graph-fig-cases-per-outbreak-bar-plot',
                figure=self._figure_cases_per_outbreak(cases_per_outbreak, type='bar')),
            dcc.Graph(
                id='graph-fig-cases-per-outbreak-in-percent-bar-plot',
                figure=self._figure_cases_per_outbreak_in_percent(cases_per_outbreak, type='bar')),
            dcc.Graph(
                id='graph-fig-cases-per-outbreak-line-plot',
                figure=self._figure_cases_per_outbreak(cases_per_outbreak, type='line')),
            dcc.Graph(
                id='graph-fig-cases-per-outbreak-in-percent-line-plot',
                figure=self._figure_cases_per_outbreak_in_percent(cases_per_outbreak, type='line'))
        ]

    def _tab_corona_intensive_care(self, intensive_register: IntensiveRegisterDataFrame) -> List[dcc.Graph]:
        return [
            dcc.Graph(
                id='graph-fig-intensive-reporting-areas',
                figure=self._figure_intensive_reporting_areas(intensive_register)),
            dcc.Graph(
                id='graph-fig-intensive-new',
                figure=self._figure_intensive_new(intensive_register)),
            dcc.Graph(
                id='graph-fig-intensive-r-value',
                figure=self._figure_intensive_r_value(intensive_register)),
            dcc.Graph(
                id='graph-fig-intensive-daily-change',
                figure=self._figure_intensive_daily_change(intensive_register)),
            dcc.Graph(
                id='graph-fig-intensive-care-ventilated',
                figure=self._figure_intensive_care_ventilated(intensive_register)),
            dcc.Graph(
                id='graph-fig-intensive-beds',
                figure=self._figure_intensive_beds(intensive_register)),
            dcc.Graph(
                id='graph-fig-intensive-beds-prop',
                figure=self._figure_intensive_beds_prop(intensive_register))
        ]

    def _tab_data_sources_description(self) -> dcc.Markdown:
        with open('data_sources_description.md', 'r', encoding='utf-8') as input_file:
            text = input_file.read()
        return dcc.Markdown(text,
                            id='data-sources-description-content',
                            dangerously_allow_html=True)

    def _block_daily_overview_cases(self, daily_figures: DailyFiguresDict) -> List[THtml]:
        prefix_mean_cases_change = self._get_prefix(daily_figures["last_mean_cases_change_since_day_before"])

        return [html.H2("cases"),
                html.Br(),
                html.H3(f'{daily_figures["last_mean_cases"]:,}'),
                'calculated mean cases',
                html.Br(),
                html.Br(),
                f'{prefix_mean_cases_change}{daily_figures["last_mean_cases_change_since_day_before"]:,}',
                html.Br(),
                'mean cases since day before',
                html.Br(),
                html.Br(),
                f'{daily_figures["cases_last_365_days"]:,}',
                html.Br(),
                'cases last 365 days',
                html.Br(),
                html.Br(),
                f'{daily_figures["last_cases_reported_by_rki"]:,}',
                html.Br(),
                'new reported cases by RKI'
                ]

    def _block_daily_overview_deaths(self, daily_figures: DailyFiguresDict) -> List[THtml]:
        prefix_mean_deaths_change = self._get_prefix(daily_figures["last_mean_deaths_change_since_day_before"])

        return [html.H2("deaths"),
                html.Br(),
                html.H3(f'{daily_figures["last_mean_deaths"]:,}'),
                'calculated mean deaths',
                html.Br(),
                html.Br(),
                f'{prefix_mean_deaths_change}{daily_figures["last_mean_deaths_change_since_day_before"]:,}',
                html.Br(),
                'mean deaths since day before',
                html.Br(),
                html.Br(),
                f'{daily_figures["deaths_last_365_days"]:,}',
                html.Br(),
                'deaths last 365 days',
                html.Br(),
                html.Br(),
                f'{daily_figures["last_deaths_reported_by_rki"]:,}',
                html.Br(),
                'new reported deaths by RKI'
                ]

    def _block_daily_overview_r_value(self, daily_figures: DailyFiguresDict) -> List[THtml]:
        prefix_r_value_change = self._get_prefix(daily_figures["last_r_value_change_since_day_before"])
        prefix_r_value_rki_change = self._get_prefix(
            daily_figures["last_r_value_by_nowcast_rki_change_since_day_before"])
        prefix_r_value_intensive_care_change = \
            self._get_prefix(daily_figures["last_r_value_by_new_admissions_to_intensive_care_change_since_day_before"])

        return [html.H2("R value"),
                html.Br(),
                html.H3(f'{daily_figures["last_r_value"]:,}'),
                'R value calculated by mean cases',
                html.Br(),
                html.Br(),
                f'{prefix_r_value_change}{daily_figures["last_r_value_change_since_day_before"]:,}',
                html.Br(),
                'change since day before',
                html.Br(),
                html.Br(),
                f'{daily_figures["last_r_value_by_nowcast_rki"]:,} '
                f'({prefix_r_value_rki_change}{daily_figures["last_r_value_by_nowcast_rki_change_since_day_before"]:,})',
                html.Br(),
                '7 day R value reported by RKI',
                html.Br(),
                html.Br(),
                f'{daily_figures["last_r_value_by_new_admissions_to_intensive_care"]:,} '
                f'({prefix_r_value_intensive_care_change}'
                f'{daily_figures["last_r_value_by_new_admissions_to_intensive_care_change_since_day_before"]:,})',
                html.Br(),
                'R value by new admissions to intensive care'
                ]

    def _block_daily_overview_last_7_days(self, daily_figures: DailyFiguresDict) -> List[THtml]:
        prefix_cases_7_days_change = self._get_prefix(daily_figures["cases_last_7_days_change_since_day_before"])
        prefix_cases_7_days_by_reporting_date_change = \
            self._get_prefix(daily_figures["cases_last_7_days_by_reporting_date_change_since_day_before"])
        prefix_deaths_7_days_change = self._get_prefix(daily_figures["deaths_last_7_days_change_since_day_before"])

        return [html.H2("last 7 days"),
                html.Br(),
                html.H3(f'{daily_figures["cases_last_7_days"]:,}'),
                'cases per 100,000 inhabitants',
                html.Br(),
                html.Br(),
                f'{prefix_cases_7_days_change}{daily_figures["cases_last_7_days_change_since_day_before"]:,}',
                html.Br(),
                'change since day before',
                html.Br(),
                html.Br(),
                f'{daily_figures["cases_last_7_days_by_reporting_date"]:,} '
                f'({prefix_cases_7_days_by_reporting_date_change}'
                f'{daily_figures["cases_last_7_days_by_reporting_date_change_since_day_before"]:,})',
                html.Br(),
                'cases by reporting date (RKI version)',
                html.Br(),
                html.Br(),
                f'{daily_figures["deaths_last_7_days"]:,} '
                f'({prefix_deaths_7_days_change}{daily_figures["deaths_last_7_days_change_since_day_before"]:,})',
                html.Br(),
                'deaths per 1,000,000 inhabitants'
                ]

    def _get_prefix(self, number: TNum) -> str:
        prefix = ""

        if number > 0:
            prefix = "+"
        elif number == 0:
            prefix = "±"

        return prefix

    def _get_daily_figures(self,
                           corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                           nowcast_rki: NowcastRKIDataFrame,
                           intensive_register: IntensiveRegisterDataFrame) -> DailyFiguresDict:

        cases_cumulative = int(corona_cases_and_deaths.last_cases_cumulative())
        cases_last_365_days = int(corona_cases_and_deaths.cases_last_365_days())
        last_rki_reported_cases = int(corona_cases_and_deaths.last_reported_cases())
        last_mean_cases = int(np.round(corona_cases_and_deaths.last_mean_cases()))

        last_mean_cases_change_day_before = \
            corona_cases_and_deaths.change_from_second_last_to_last_date_for_mean_cases()
        last_mean_cases_change_day_before = int(np.round(last_mean_cases_change_day_before))

        incidence_cases = np.round(corona_cases_and_deaths.last_7_day_incidence_per_100_000_inhabitants(), 2)

        incidence_cases_change = \
            corona_cases_and_deaths.change_from_second_last_to_last_date_for_7_day_incidence_per_100_000_inhabitants()
        incidence_cases_change = np.round(incidence_cases_change, 2)

        incidence_cases_by_reporting_date = \
            corona_cases_and_deaths.last_7_day_incidence_per_100_000_inhabitants_by_reporting_date()
        incidence_cases_by_reporting_date = np.round(incidence_cases_by_reporting_date, 2)

        incidence_cases_change_by_reporting_date = \
            corona_cases_and_deaths. \
                change_from_second_last_to_last_date_for_7_day_incidence_per_100_000_inhabitants_by_reporting_date()
        incidence_cases_change_by_reporting_date = np.round(incidence_cases_change_by_reporting_date, 2)

        deaths_cumulative = int(corona_cases_and_deaths.last_deaths_cumulative())
        deaths_last_365_days = int(corona_cases_and_deaths.deaths_last_365_days())
        last_rki_reported_deaths = int(corona_cases_and_deaths.last_reported_deaths())
        last_mean_deaths = int(np.round(corona_cases_and_deaths.last_mean_deaths()))

        last_mean_deaths_change_day_before = \
            corona_cases_and_deaths.change_from_second_last_to_last_date_for_mean_deaths()
        last_mean_deaths_change_day_before = int(np.round(last_mean_deaths_change_day_before))

        incidence_deaths = corona_cases_and_deaths.last_7_day_deaths_by_mean_cases_per_1_000_000_inhabitants()
        incidence_deaths = np.round(incidence_deaths, 2)

        incidence_deaths_change = \
            corona_cases_and_deaths. \
                change_from_second_last_to_last_date_for_7_day_deaths_by_mean_cases_per_1_000_000_inhabitants()
        incidence_deaths_change = np.round(incidence_deaths_change, 2)

        last_r_value = np.round(corona_cases_and_deaths.last_r_value_by_mean_cases(), 2)
        r_value_change = np.round(
            corona_cases_and_deaths.change_from_second_last_to_last_date_for_r_value_by_mean_cases(), 2)
        last_r_value_nowcast = np.round(nowcast_rki.last_r_value(), 2)
        r_value_nowcast_change = np.round(nowcast_rki.change_from_second_last_to_last_date_for_r_value(), 2)
        last_r_value_intensive_register = np.round(intensive_register.last_r_value_by_mean_cases(), 2)
        r_value_intensive_register_change = np.round(
            intensive_register.change_from_second_last_to_last_date_for_r_value_by_mean_cases(), 2)

        daily_figures: DailyFiguresDict = \
            {"cases_cumulative": cases_cumulative,
             "cases_last_365_days": cases_last_365_days,
             "last_cases_reported_by_rki": last_rki_reported_cases,
             "last_mean_cases": last_mean_cases,
             "last_mean_cases_change_since_day_before": last_mean_cases_change_day_before,
             "cases_last_7_days": incidence_cases,
             "cases_last_7_days_change_since_day_before": incidence_cases_change,
             "cases_last_7_days_by_reporting_date": incidence_cases_by_reporting_date,
             "cases_last_7_days_by_reporting_date_change_since_day_before": incidence_cases_change_by_reporting_date,
             "deaths_cumulative": deaths_cumulative,
             "deaths_last_365_days": deaths_last_365_days,
             "last_deaths_reported_by_rki": last_rki_reported_deaths,
             "last_mean_deaths": last_mean_deaths,
             "last_mean_deaths_change_since_day_before": last_mean_deaths_change_day_before,
             "deaths_last_7_days": incidence_deaths,
             "deaths_last_7_days_change_since_day_before": incidence_deaths_change,
             "last_r_value": last_r_value,
             "last_r_value_change_since_day_before": r_value_change,
             "last_r_value_by_nowcast_rki": last_r_value_nowcast,
             "last_r_value_by_nowcast_rki_change_since_day_before": r_value_nowcast_change,
             "last_r_value_by_new_admissions_to_intensive_care": last_r_value_intensive_register,
             "last_r_value_by_new_admissions_to_intensive_care_change_since_day_before": r_value_intensive_register_change
             }

        return daily_figures

    def _figure_cases_mean_3(self,
                             corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                             nowcast_rki: NowcastRKIDataFrame) -> Figure:

        corona_cases_and_deaths_with_nowcast = pd.concat([corona_cases_and_deaths, nowcast_rki], axis=1).reset_index()
        corona_cases_and_deaths_with_nowcast.loc[:, self.config["FIG_CASES_MEAN_3"]["hover_data_strftime"]] = \
            self._format_column_strftime(corona_cases_and_deaths_with_nowcast, "FIG_CASES_MEAN_3")
        corona_cases_and_deaths_with_nowcast.loc[:, self.config["FIG_CASES_MEAN_3"]["hover_data_format_column"]] = \
            self._format_hover_data_column(corona_cases_and_deaths_with_nowcast, "FIG_CASES_MEAN_3")

        fig = make_subplots(specs=[[{"secondary_y": False}]])

        mainfig = px.line(corona_cases_and_deaths_with_nowcast,
                          x=self.config["FIG_CASES_MEAN_3"]["x"],
                          y=json.loads(self.config["FIG_CASES_MEAN_3"]["y"]),
                          color_discrete_map=json.loads(self.config["FIG_CASES_MEAN_3"]["color_discrete_map"]),
                          render_mode=self.config["ALL_FIGS"]["render_mode"],
                          hover_data=json.loads(self.config["FIG_CASES_MEAN_3"]["hover_data"]))

        subfig = px.line(corona_cases_and_deaths_with_nowcast,
                         x=self.config["FIG_CASES_MEAN_3"]["x"],
                         y=json.loads(self.config["FIG_CASES_MEAN_3_SUBFIG"]["y"]),
                         color_discrete_map=json.loads(self.config["FIG_CASES_MEAN_3_SUBFIG"]["color_discrete_map"]),
                         render_mode=self.config["ALL_FIGS"]["render_mode"],
                         hover_data=json.loads(self.config["FIG_CASES_MEAN_3_SUBFIG"]["hover_data"]))

        subfig_2 = px.line(corona_cases_and_deaths_with_nowcast,
                           x=self.config["FIG_CASES_MEAN_3"]["x"],
                           y=json.loads(self.config["FIG_CASES_MEAN_3_SUBFIG_2"]["y"]),
                           color_discrete_map=json.loads(
                               self.config["FIG_CASES_MEAN_3_SUBFIG_2"]["color_discrete_map"]),
                           render_mode=self.config["ALL_FIGS"]["render_mode"])

        fig.add_traces(mainfig.data + subfig.data + subfig_2.data)

        fig.update_layout(title=self.config["FIG_CASES_MEAN_3"]["title"],
                          xaxis_title=self.config["FIG_CASES_MEAN_3"]["xaxis_title"],
                          yaxis_title=self.config["FIG_CASES_MEAN_3"]["yaxis_title"],
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_CASES_MEAN_3"]["yaxis_tickformat"])
        return fig

    def _figure_deaths_mean_3(self,
                              corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                              nowcast_rki: NowcastRKIDataFrame) -> Figure:

        corona_cases_and_deaths_with_nowcast = pd.concat([corona_cases_and_deaths, nowcast_rki], axis=1).reset_index()
        corona_cases_and_deaths_with_nowcast.loc[:, self.config["FIG_DEATHS_MEAN_3"]["hover_data_strftime"]] = \
            self._format_column_strftime(corona_cases_and_deaths_with_nowcast, "FIG_DEATHS_MEAN_3")
        corona_cases_and_deaths_with_nowcast.loc[:, self.config["FIG_DEATHS_MEAN_3"]["hover_data_format_column"]] = \
            self._format_hover_data_column(corona_cases_and_deaths_with_nowcast, "FIG_DEATHS_MEAN_3")

        fig = make_subplots(specs=[[{"secondary_y": False}]])

        mainfig = px.line(corona_cases_and_deaths_with_nowcast,
                          x=self.config["FIG_DEATHS_MEAN_3"]["x"],
                          y=json.loads(self.config["FIG_DEATHS_MEAN_3"]["y"]),
                          color_discrete_map=json.loads(self.config["FIG_DEATHS_MEAN_3"]["color_discrete_map"]),
                          render_mode=self.config["ALL_FIGS"]["render_mode"],
                          hover_data=json.loads(self.config["FIG_DEATHS_MEAN_3"]["hover_data"]))

        subfig = px.line(corona_cases_and_deaths_with_nowcast,
                         x=self.config["FIG_DEATHS_MEAN_3"]["x"],
                         y=json.loads(self.config["FIG_DEATHS_MEAN_3_SUBFIG"]["y"]),
                         color_discrete_map=json.loads(self.config["FIG_DEATHS_MEAN_3_SUBFIG"]["color_discrete_map"]),
                         render_mode=self.config["ALL_FIGS"]["render_mode"],
                         hover_data=json.loads(self.config["FIG_DEATHS_MEAN_3_SUBFIG"]["hover_data"]))

        subfig_2 = px.line(corona_cases_and_deaths_with_nowcast,
                           x=self.config["FIG_DEATHS_MEAN_3"]["x"],
                           y=json.loads(self.config["FIG_DEATHS_MEAN_3_SUBFIG_2"]["y"]),
                           color_discrete_map=json.loads(
                               self.config["FIG_DEATHS_MEAN_3_SUBFIG_2"]["color_discrete_map"]),
                           render_mode=self.config["ALL_FIGS"]["render_mode"])

        fig.add_traces(mainfig.data + subfig.data + subfig_2.data)

        fig.update_layout(title=self.config["FIG_DEATHS_MEAN_3"]["title"],
                          xaxis_title=self.config["FIG_DEATHS_MEAN_3"]["xaxis_title"],
                          yaxis_title=self.config["FIG_DEATHS_MEAN_3"]["yaxis_title"],
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_DEATHS_MEAN_3"]["yaxis_tickformat"])

        return fig

    def _format_hover_data_column(self,
                                  df: pd.DataFrame,
                                  config_section: str) -> pd.Series:
        str_format = "{:" + self.config[config_section]["hover_data_format"] + "}"
        return df.loc[:, self.config[config_section]["hover_data_format_column"]] \
            .map(str_format.format)

    def _format_column_strftime(self,
                                corona_cases_and_deaths_with_nowcast: CoronaCasesAndDeathsDataFrame,
                                config_section: str) -> CoronaCasesAndDeathsSeries:
        return corona_cases_and_deaths_with_nowcast.loc[:, self.config[config_section]["hover_data_strftime"]] \
            .dt.strftime('%b %d, %Y')

    def _figure_r_value(self,
                        corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                        nowcast_rki: NowcastRKIDataFrame) -> Figure:

        corona_cases_and_deaths_with_nowcast = pd.concat([corona_cases_and_deaths, nowcast_rki], axis=1).reset_index()

        fig = px.line(corona_cases_and_deaths_with_nowcast,
                      x=self.config["FIG_R_VALUE"]["x"],
                      y=json.loads(self.config["FIG_R_VALUE"]["y"]),
                      color_discrete_map=json.loads(self.config["FIG_R_VALUE"]["color_discrete_map"]),
                      render_mode=self.config["ALL_FIGS"]["render_mode"])

        min_date = corona_cases_and_deaths_with_nowcast.date.min()
        max_date = corona_cases_and_deaths_with_nowcast.date.max()
        shapes = [{"type": 'line',
                   "y0": 1,
                   "y1": 1,
                   "x0": min_date,
                   "x1": max_date}]

        fig.update_layout(title=self.config["FIG_R_VALUE"]["title"],
                          xaxis_title=self.config["FIG_R_VALUE"]["xaxis_title"],
                          yaxis_title=self.config["FIG_R_VALUE"]["yaxis_title"],
                          shapes=shapes,
                          yaxis=json.loads(self.config["FIG_R_VALUE"]["yaxis"]),
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_R_VALUE"]["yaxis_tickformat"])
        return fig

    def _figure_7d_incidences(self,
                              corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                              nowcast_rki: NowcastRKIDataFrame) -> Figure:

        corona_cases_and_deaths_with_nowcast = pd.concat([corona_cases_and_deaths, nowcast_rki], axis=1).reset_index()

        fig = px.line(corona_cases_and_deaths_with_nowcast,
                      x=self.config["FIG_7D_INCIDENCES"]["x"],
                      y=json.loads(self.config["FIG_7D_INCIDENCES"]["y"]),
                      color_discrete_map=json.loads(self.config["FIG_7D_INCIDENCES"]["color_discrete_map"]),
                      render_mode=self.config["ALL_FIGS"]["render_mode"])

        fig.update_layout(title=self.config["FIG_7D_INCIDENCES"]["title"],
                          xaxis_title=self.config["FIG_7D_INCIDENCES"]["xaxis_title"],
                          yaxis_title=self.config["FIG_7D_INCIDENCES"]["yaxis_title"],
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_7D_INCIDENCES"]["yaxis_tickformat"])

        return fig

    def _figure_pcr_tests(self, number_pcr_tests: NumberPCRTestsDataFrame) -> Figure:

        number_pcr_tests = number_pcr_tests.reset_index()
        number_pcr_tests.loc[:, self.config["FIG_PCR_TESTS"]["hover_data_format_column"]] = \
            self._format_hover_data_column(number_pcr_tests, "FIG_PCR_TESTS")

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        mainfig = \
            px.bar(number_pcr_tests,
                   x=self.config["FIG_PCR_TESTS"]["x"],
                   y=json.loads(self.config["FIG_PCR_TESTS"]["y"]),
                   color_discrete_map=json.loads(self.config["FIG_PCR_TESTS"]["color_discrete_map"]),
                   hover_data=json.loads(self.config["FIG_PCR_TESTS"]["hover_data"]))

        subfig = \
            px.line(number_pcr_tests,
                    x=self.config["FIG_PCR_TESTS"]["x"],
                    y=json.loads(self.config["SUBFIG_PCR_TESTS_POSITIVE_RATE"]["y"]),
                    color_discrete_map=json.loads(self.config["SUBFIG_PCR_TESTS_POSITIVE_RATE"]["color_discrete_map"]),
                    render_mode=self.config["ALL_FIGS"]["render_mode"])

        subfig.update_traces(yaxis="y2")

        fig.add_traces(mainfig.data + subfig.data)
        fig.update_yaxes(title_text=self.config["SUBFIG_PCR_TESTS_POSITIVE_RATE"]["yaxis_title"],
                         secondary_y=True)

        fig.update_layout(title=self.config["FIG_PCR_TESTS"]["title"],
                          barmode=self.config["FIG_PCR_TESTS"]["barmode"],
                          xaxis_title=self.config["FIG_PCR_TESTS"]["xaxis_title"],
                          yaxis_title=self.config["FIG_PCR_TESTS"]["yaxis_title"],
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis1=dict(tickformat=self.config["FIG_PCR_TESTS"]["yaxis_tickformat"]),
                          yaxis2=dict(tickformat=self.config["SUBFIG_PCR_TESTS_POSITIVE_RATE"]["yaxis_tickformat"]))

        return fig

    def _figure_distribution_of_inhabitants_and_deaths(self, age_distribution: AgeDistributionDataFrame) -> Figure:

        age_distribution = age_distribution.reset_index()

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        mainfig = \
            px.bar(age_distribution,
                   x=self.config["FIG_DISTRIBUTION_OF_INHABITANTS"]["x"],
                   y=json.loads(self.config["FIG_DISTRIBUTION_OF_INHABITANTS"]["y"]),
                   color_discrete_map=json.loads(self.config["FIG_DISTRIBUTION_OF_INHABITANTS"]["color_discrete_map"]))

        subfig = \
            px.bar(age_distribution,
                   x=self.config["FIG_DISTRIBUTION_OF_INHABITANTS"]["x"],
                   y=json.loads(self.config["SUBFIG_DISTRIBUTION_OF_DEATHS"]["y"]),
                   color_discrete_map=json.loads(self.config["SUBFIG_DISTRIBUTION_OF_DEATHS"]["color_discrete_map"]))
        subfig.update_traces(yaxis="y2")

        fig.add_traces(mainfig.data + subfig.data)
        fig.update_yaxes(title_text=self.config["SUBFIG_DISTRIBUTION_OF_DEATHS"]["yaxis_title"],
                         secondary_y=True)

        fig.update_layout(title=self.config["FIG_DISTRIBUTION_OF_INHABITANTS"]["title"],
                          barmode=self.config["SUBFIG_DISTRIBUTION_OF_DEATHS"]["barmode"],
                          xaxis_title=self.config["FIG_DISTRIBUTION_OF_INHABITANTS"]["xaxis_title"],
                          yaxis_title=self.config["FIG_DISTRIBUTION_OF_INHABITANTS"]["yaxis_title"],
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis1=dict(tickformat=self.config["FIG_DISTRIBUTION_OF_INHABITANTS"]["yaxis_tickformat"]),
                          yaxis2=dict(tickformat=self.config["SUBFIG_DISTRIBUTION_OF_DEATHS"]["yaxis_tickformat"]))

        return fig

    def _figure_distribution_of_cases_and_deaths_per_n_inhabitants(self,
                                                                   age_distribution: AgeDistributionDataFrame) -> Figure:

        age_distribution = age_distribution.reset_index()

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        mainfig = \
            px.bar(age_distribution,
                   x=self.config["FIG_DISTRIBUTION_OF_CASES_PER_N_INHABITANTS"]["x"],
                   y=json.loads(self.config["FIG_DISTRIBUTION_OF_CASES_PER_N_INHABITANTS"]["y"]),
                   color_discrete_map=json.loads(
                       self.config["FIG_DISTRIBUTION_OF_CASES_PER_N_INHABITANTS"]["color_discrete_map"]))

        subfig = \
            px.bar(age_distribution,
                   x=self.config["FIG_DISTRIBUTION_OF_CASES_PER_N_INHABITANTS"]["x"],
                   y=json.loads(self.config["SUBFIG_DISTRIBUTION_OF_DEATHS_PER_N_INHABITANTS"]["y"]),
                   color_discrete_map=json.loads(
                       self.config["SUBFIG_DISTRIBUTION_OF_DEATHS_PER_N_INHABITANTS"]["color_discrete_map"]))

        subfig.update_traces(yaxis="y2")

        fig.add_traces(
            mainfig.data + subfig.data)
        fig.update_yaxes(title_text=self.config["SUBFIG_DISTRIBUTION_OF_DEATHS_PER_N_INHABITANTS"]["yaxis_title"],
                         secondary_y=True)

        fig.update_layout(title=self.config["FIG_DISTRIBUTION_OF_CASES_PER_N_INHABITANTS"]["title"],
                          barmode=self.config["SUBFIG_DISTRIBUTION_OF_DEATHS_PER_N_INHABITANTS"]["barmode"],
                          xaxis_title=self.config["FIG_DISTRIBUTION_OF_CASES_PER_N_INHABITANTS"]["xaxis_title"],
                          yaxis_title=self.config["FIG_DISTRIBUTION_OF_CASES_PER_N_INHABITANTS"]["yaxis_title"],
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis1=dict(tickformat=
                                      self.config["FIG_DISTRIBUTION_OF_CASES_PER_N_INHABITANTS"]["yaxis_tickformat"]),
                          yaxis2=dict(tickformat=
                                      self.config["SUBFIG_DISTRIBUTION_OF_DEATHS_PER_N_INHABITANTS"][
                                          "yaxis_tickformat"]))

        return fig

    def _figure_intensive_new(self, intensive_register: IntensiveRegisterDataFrame) -> Figure:

        intensive_register = intensive_register.reset_index()

        fig = px.line(intensive_register,
                      x=self.config["FIG_INTENSIVE_NEW"]["x"],
                      y=json.loads(self.config["FIG_INTENSIVE_NEW"]["y"]),
                      color_discrete_map=json.loads(self.config["FIG_INTENSIVE_NEW"]["color_discrete_map"]),
                      render_mode=self.config["ALL_FIGS"]["render_mode"])

        fig.update_layout(title=self.config["FIG_INTENSIVE_NEW"]["title"],
                          xaxis_title=self.config["FIG_INTENSIVE_NEW"]["xaxis_title"],
                          yaxis_title=self.config["FIG_INTENSIVE_NEW"]["yaxis_title"],
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_INTENSIVE_NEW"]["yaxis_tickformat"])

        return fig

    def _figure_intensive_r_value(self, intensive_register: IntensiveRegisterDataFrame) -> Figure:

        intensive_register = intensive_register.reset_index()

        fig = px.line(intensive_register,
                      x=self.config["FIG_INTENSIVE_R_VALUE"]["x"],
                      y=json.loads(self.config["FIG_INTENSIVE_R_VALUE"]["y"]),
                      color_discrete_map=json.loads(self.config["FIG_INTENSIVE_R_VALUE"]["color_discrete_map"]),
                      render_mode=self.config["ALL_FIGS"]["render_mode"])

        min_date = intensive_register.date.min()
        max_date = intensive_register.date.max()
        shapes = [{"type": 'line',
                   "y0": 1,
                   "y1": 1,
                   "x0": min_date,
                   "x1": max_date}]

        fig.update_layout(title=self.config["FIG_INTENSIVE_R_VALUE"]["title"],
                          xaxis_title=self.config["FIG_INTENSIVE_R_VALUE"]["xaxis_title"],
                          yaxis_title=self.config["FIG_INTENSIVE_R_VALUE"]["yaxis_title"],
                          shapes=shapes,
                          yaxis=json.loads(self.config["FIG_INTENSIVE_R_VALUE"]["yaxis"]),
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_INTENSIVE_R_VALUE"]["yaxis_tickformat"])
        return fig


    def _figure_intensive_daily_change(self, intensive_register: IntensiveRegisterDataFrame) -> Figure:

        intensive_register = intensive_register.reset_index()

        fig = \
            px.line(intensive_register,
                    x=self.config["FIG_INTENSIVE_DAILY_CHANGE"]["x"],
                    y=json.loads(self.config["FIG_INTENSIVE_DAILY_CHANGE"]["y"]),
                    color_discrete_map=json.loads(self.config["FIG_INTENSIVE_DAILY_CHANGE"]["color_discrete_map"]),
                    render_mode=self.config["ALL_FIGS"]["render_mode"])

        fig.update_layout(title=self.config["FIG_INTENSIVE_DAILY_CHANGE"]["title"],
                          xaxis_title=self.config["FIG_INTENSIVE_DAILY_CHANGE"]["xaxis_title"],
                          yaxis_title=self.config["FIG_INTENSIVE_DAILY_CHANGE"]["yaxis_title"],
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_INTENSIVE_DAILY_CHANGE"]["yaxis_tickformat"])

        return fig

    def _figure_intensive_reporting_areas(self, intensive_register: IntensiveRegisterDataFrame) -> Figure:

        intensive_register = intensive_register.reset_index()

        fig = \
            px.line(intensive_register,
                    x=self.config["FIG_INTENSIVE_REPORTING_AREAS"]["x"],
                    y=json.loads(self.config["FIG_INTENSIVE_REPORTING_AREAS"]["y"]),
                    color_discrete_map=json.loads(self.config["FIG_INTENSIVE_REPORTING_AREAS"]["color_discrete_map"]),
                    render_mode=self.config["ALL_FIGS"]["render_mode"])

        fig.update_layout(title=self.config["FIG_INTENSIVE_REPORTING_AREAS"]["title"],
                          xaxis_title=self.config["FIG_INTENSIVE_REPORTING_AREAS"]["xaxis_title"],
                          yaxis_title=self.config["FIG_INTENSIVE_REPORTING_AREAS"]["yaxis_title"],
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_INTENSIVE_REPORTING_AREAS"]["yaxis_tickformat"])

        return fig

    def _figure_intensive_care_ventilated(self, intensive_register: IntensiveRegisterDataFrame) -> Figure:

        intensive_register = intensive_register.reset_index()

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        mainfig = \
            px.bar(intensive_register,
                   x=self.config["FIG_INTENSIVE_CARE_VENTILATED"]["x"],
                   y=json.loads(self.config["FIG_INTENSIVE_CARE_VENTILATED"]["y"]),
                   color_discrete_map=json.loads(self.config["FIG_INTENSIVE_CARE_VENTILATED"]["color_discrete_map"]))

        subfig = \
            px.line(intensive_register,
                    x=self.config["FIG_INTENSIVE_CARE_VENTILATED"]["x"],
                    y=json.loads(self.config["SUBFIG_INTENSIVE_CARE_VENTILATED_PERCENTAGE"]["y"]),
                    color_discrete_map=
                    json.loads(self.config["SUBFIG_INTENSIVE_CARE_VENTILATED_PERCENTAGE"]["color_discrete_map"]),
                    render_mode=self.config["ALL_FIGS"]["render_mode"])

        subfig.update_traces(yaxis="y2")

        fig.add_traces(mainfig.data + subfig.data)
        fig.update_yaxes(title_text=self.config["SUBFIG_INTENSIVE_CARE_VENTILATED_PERCENTAGE"]["yaxis_title"],
                         secondary_y=True)

        fig.update_layout(title=self.config["FIG_INTENSIVE_CARE_VENTILATED"]["title"],
                          barmode=self.config["SUBFIG_INTENSIVE_CARE_VENTILATED_PERCENTAGE"]["barmode"],
                          xaxis_title=self.config["FIG_INTENSIVE_CARE_VENTILATED"]["xaxis_title"],
                          yaxis_title=self.config["FIG_INTENSIVE_CARE_VENTILATED"]["yaxis_title"],
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis1=dict(tickformat=self.config["FIG_INTENSIVE_CARE_VENTILATED"]["yaxis_tickformat"]),
                          yaxis2=dict(tickformat=
                                      self.config["SUBFIG_INTENSIVE_CARE_VENTILATED_PERCENTAGE"]["yaxis_tickformat"]))

        return fig

    def _figure_intensive_beds(self, intensive_register: IntensiveRegisterDataFrame) -> Figure:

        intensive_register = intensive_register.reset_index()

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        mainfig = px.bar(intensive_register,
                         x=self.config["FIG_INTENSIVE_BEDS"]["x"],
                         y=json.loads(self.config["FIG_INTENSIVE_BEDS"]["y"]),
                         color_discrete_map=json.loads(self.config["FIG_INTENSIVE_BEDS"]["color_discrete_map"]))

        subfig = px.line(intensive_register,
                         x=self.config["FIG_INTENSIVE_BEDS"]["x"],
                         y=json.loads(self.config["FIG_INTENSIVE_BEDS_COUNT"]["y"]),
                         color_discrete_map=json.loads(self.config["FIG_INTENSIVE_BEDS_COUNT"]["color_discrete_map"]),
                         render_mode=self.config["ALL_FIGS"]["render_mode"])

        # fig_intensive_beds_count.update_traces(yaxis="y1")

        fig.add_traces(mainfig.data + subfig.data)
        fig.update_yaxes(secondary_y=False)

        fig.update_layout(title=self.config["FIG_INTENSIVE_BEDS"]["title"],
                          barmode=self.config["FIG_INTENSIVE_BEDS_COUNT"]["barmode"],
                          xaxis_title=self.config["FIG_INTENSIVE_BEDS"]["xaxis_title"],
                          yaxis_title=self.config["FIG_INTENSIVE_BEDS"]["yaxis_title"],
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_INTENSIVE_BEDS"]["yaxis_tickformat"],
                          yaxis1=dict(tickformat=self.config["FIG_INTENSIVE_BEDS"]["yaxis_tickformat"]),
                          yaxis2=dict(tickformat=self.config["FIG_INTENSIVE_BEDS_COUNT"]["yaxis_tickformat"]))

        return fig

    def _figure_intensive_beds_prop(self, intensive_register: IntensiveRegisterDataFrame) -> Figure:

        intensive_register = intensive_register.reset_index()

        fig = px.line(intensive_register,
                      x=self.config["FIG_INTENSIVE_BEDS_PROP"]["x"],
                      y=json.loads(self.config["FIG_INTENSIVE_BEDS_PROP"]["y"]),
                      color_discrete_map=json.loads(self.config["FIG_INTENSIVE_BEDS_PROP"]["color_discrete_map"]),
                      render_mode=self.config["ALL_FIGS"]["render_mode"])

        fig.update_layout(title=self.config["FIG_INTENSIVE_BEDS_PROP"]["title"],
                          xaxis_title=self.config["FIG_INTENSIVE_BEDS_PROP"]["xaxis_title"],
                          yaxis_title=self.config["FIG_INTENSIVE_BEDS_PROP"]["yaxis_title"],
                          yaxis=json.loads(self.config["FIG_INTENSIVE_BEDS_PROP"]["yaxis"]),
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis1=dict(tickformat=self.config["FIG_INTENSIVE_BEDS"]["yaxis_tickformat"]),
                          yaxis2=dict(tickformat=self.config["FIG_INTENSIVE_BEDS_COUNT"]["yaxis_tickformat"]))

        return fig

    def _figure_clinical_aspects(self, clinical_aspects: ClinicalAspectsDataFrame) -> Figure:

        df = clinical_aspects.reset_index()

        fig = px.line(df,
                      x=self.config["FIG_CLINICAL_ASPECTS"]["x"],
                      y=json.loads(self.config["FIG_CLINICAL_ASPECTS"]["y"]),
                      color_discrete_map=json.loads(self.config["FIG_CLINICAL_ASPECTS"]["color_discrete_map"]),
                      render_mode=self.config["ALL_FIGS"]["render_mode"])

        fig.update_layout(title=self.config["FIG_CLINICAL_ASPECTS"]["title"],
                          xaxis_title=self.config["FIG_CLINICAL_ASPECTS"]["xaxis_title"],
                          yaxis_title=self.config["FIG_CLINICAL_ASPECTS"]["yaxis_title"],
                          # yaxis=yaxis,
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_CLINICAL_ASPECTS"]["yaxis_tickformat"])

        return fig

    def _dropdown_for_cases_per_outbreak(self) -> dcc.Dropdown:
        return dcc.Dropdown(
            id='radio-items-for-cases-per-outbreak',
            className='radio-items',
            options=[
                {'label': 'Cases per Outbreak Category and Week as Bar Plot',
                 'value': 'cases-per-outbreak-stacked-bar'},
                {'label': 'Cases in Percent per Outbreak Category and Week as Bar Plot',
                 'value': 'cases-in-percent-per-outbreak-stacked-bar'},
                {'label': 'Cases per Outbreak Category and Week as Line Plot',
                 'value': 'cases-per-outbreak-line-plot'},
                {'label': 'Cases in Percent per Outbreak Category and Week as Line Plot',
                 'value': 'cases-in-percent-per-outbreak-line-plot'},
            ],
            value='cases-per-outbreak-stacked-bar')

    def _figure_cases_per_outbreak(self, cases_per_outbreak: CasesPerOutbreakDataFrame, type: str) -> Figure:

        cases_per_outbreak = cases_per_outbreak.reset_index()

        fig = px.line(cases_per_outbreak,
                      x=self.config["FIG_CASES_PER_OUTBREAK"]["x"],
                      y=json.loads(self.config["FIG_CASES_PER_OUTBREAK"]["y"]),
                      color_discrete_map=json.loads(self.config["FIG_CASES_PER_OUTBREAK"]["color_discrete_map"]))

        if type == 'bar':
            fig = px.bar(cases_per_outbreak,
                         x=self.config["FIG_CASES_PER_OUTBREAK"]["x"],
                         y=json.loads(self.config["FIG_CASES_PER_OUTBREAK"]["y"]),
                         color_discrete_map=json.loads(self.config["FIG_CASES_PER_OUTBREAK"]["color_discrete_map"]))

        fig.update_layout(title=self.config["FIG_CASES_PER_OUTBREAK"]["title"],
                          xaxis_title=self.config["FIG_CASES_PER_OUTBREAK"]["xaxis_title"],
                          yaxis_title=self.config["FIG_CASES_PER_OUTBREAK"]["yaxis_title"],
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_CASES_PER_OUTBREAK"]["yaxis_tickformat"])

        if type == 'bar':
            fig.update_layout(barmode=self.config["FIG_CASES_PER_OUTBREAK"]["barmode"])

        return fig

    def _figure_cases_per_outbreak_in_percent(self, cases_per_outbreak: CasesPerOutbreakDataFrame, type: str) \
            -> Figure:

        cases_per_outbreak = cases_per_outbreak.reset_index()

        fig = px.line(cases_per_outbreak,
                      x=self.config["FIG_CASES_PER_OUTBREAK_IN_PERCENT"]["x"],
                      y=json.loads(self.config["FIG_CASES_PER_OUTBREAK_IN_PERCENT"]["y"]),
                      color_discrete_map=json.loads(
                          self.config["FIG_CASES_PER_OUTBREAK_IN_PERCENT"]["color_discrete_map"]))

        if type == 'bar':
            fig = px.bar(cases_per_outbreak,
                         x=self.config["FIG_CASES_PER_OUTBREAK_IN_PERCENT"]["x"],
                         y=json.loads(self.config["FIG_CASES_PER_OUTBREAK_IN_PERCENT"]["y"]),
                         color_discrete_map=json.loads(
                             self.config["FIG_CASES_PER_OUTBREAK_IN_PERCENT"]["color_discrete_map"]))

        fig.update_layout(title=self.config["FIG_CASES_PER_OUTBREAK_IN_PERCENT"]["title"],
                          xaxis_title=self.config["FIG_CASES_PER_OUTBREAK_IN_PERCENT"]["xaxis_title"],
                          yaxis_title=self.config["FIG_CASES_PER_OUTBREAK_IN_PERCENT"]["yaxis_title"],
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_CASES_PER_OUTBREAK_IN_PERCENT"]["yaxis_tickformat"])

        if type == 'bar':
            fig.update_layout(barmode=self.config["FIG_CASES_PER_OUTBREAK_IN_PERCENT"]["barmode"])

        return fig

    def _dropdown_for_median_and_mean_ages(self) -> dcc.Dropdown:
        return dcc.Dropdown(
            id='radio-items-for-median-and-mean-ages',
            className='radio-items',
            options=[
                {'label': 'Median Ages',
                 'value': 'median-ages'},
                {'label': 'Mean Ages',
                 'value': 'mean-ages'}
            ],
            value='median-ages')

    def _figure_median_or_mean_ages(self, median_and_mean_ages: MedianAndMeanAgesDataFrame, median:bool = True) -> Figure:

        if median:
            config_part = "FIG_MEDIAN_AGES"
        else:
            config_part = "FIG_MEAN_AGES"

        df = median_and_mean_ages.reset_index()

        fig = px.line(df,
                      x=self.config[config_part]["x"],
                      y=json.loads(self.config[config_part]["y"]),
                      color_discrete_map=json.loads(self.config[config_part]["color_discrete_map"]),
                      render_mode=self.config["ALL_FIGS"]["render_mode"])

        fig.update_layout(title=self.config[config_part]["title"],
                          xaxis_title=self.config[config_part]["xaxis_title"],
                          yaxis_title=self.config[config_part]["yaxis_title"],
                          # yaxis=yaxis,
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config[config_part]["yaxis_tickformat"])

        return fig

    def _dropdown_for_hospitalizations_per_age_group(self) -> dcc.Dropdown:
        return dcc.Dropdown(
            id='radio-items-for-hospitalizations-per-age-group',
            className='radio-items',
            options=[
                {'label': 'Hospitalizations per Age Group as Bar Plot',
                 'value': 'hospitalizations-per-age-group-stacked-bar'},
                {'label': 'Hospitalizations per Age Group as Line Plot',
                 'value': 'hospitalizations-per-age-group-line-plot'}
            ],
            value='hospitalizations-per-age-group-stacked-bar')

    def _figure_hospitalizations_per_age_group(self, clinical_aspects: ClinicalAspectsDataFrame, type: str) -> Figure:

        clinical_aspects = clinical_aspects.reset_index()

        fig = px.line(clinical_aspects,
                      x=self.config["FIG_HOSPITALIZATIONS"]["x"],
                      y=json.loads(self.config["FIG_HOSPITALIZATIONS"]["y"]),
                      color_discrete_map=json.loads(self.config["FIG_HOSPITALIZATIONS"]["color_discrete_map"]))

        if type == 'bar':
            fig = px.bar(clinical_aspects,
                         x=self.config["FIG_HOSPITALIZATIONS"]["x"],
                         y=json.loads(self.config["FIG_HOSPITALIZATIONS"]["y"]),
                         color_discrete_map=json.loads(self.config["FIG_HOSPITALIZATIONS"]["color_discrete_map"]))

        fig.update_layout(title=self.config["FIG_HOSPITALIZATIONS"]["title"],
                          xaxis_title=self.config["FIG_HOSPITALIZATIONS"]["xaxis_title"],
                          yaxis_title=self.config["FIG_HOSPITALIZATIONS"]["yaxis_title"],
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_HOSPITALIZATIONS"]["yaxis_tickformat"])

        if type == 'bar':
            fig.update_layout(barmode=self.config["FIG_HOSPITALIZATIONS"]["barmode"])

        return fig

    def _dropdown_for_deaths_by_week_of_death_and_age_group(self) -> dcc.Dropdown:
        return dcc.Dropdown(
            id='radio-items-for-deaths-by-week-of-death-and-age-group',
            className='radio-items',
            options=[
                {'label': 'Deaths By Week of Death and Age Group as Bar Plot',
                 'value': 'deaths-by-week-of-death-and-age-group-stacked-bar'},
                {'label': 'Deaths By Week of Death and Age Group as Line Plot',
                 'value': 'deaths-by-week-of-death-and-age-group-line-plot'},
                {'label': 'Deaths in Percent By Week of Death and Age Group as Bar Plot',
                 'value': 'deaths-in-percent-by-week-of-death-and-age-group-stacked-bar'},
                {'label': 'Deaths in Percent By Week of Death and Age Group as Line Plot',
                 'value': 'deaths-in-percent-by-week-of-death-and-age-group-line-plot'}
            ],
            value='deaths-by-week-of-death-and-age-group-stacked-bar')

    def _figure_deaths_by_week_of_death_and_age_group(self,
                                                      deaths_by_week_of_death_and_age_group:
                                                      DeathsByWeekOfDeathAndAgeGroupDataFrame,
                                                      type: str) -> Figure:

        deaths_by_week_of_death_and_age_group = deaths_by_week_of_death_and_age_group.reset_index()

        fig = px.line(deaths_by_week_of_death_and_age_group,
                      x=self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP"]["x"],
                      y=json.loads(self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP"]["y"]),
                      color_discrete_map=json.loads(
                          self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP"]["color_discrete_map"]))

        if type == 'bar':
            fig = px.bar(deaths_by_week_of_death_and_age_group,
                         x=self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP"]["x"],
                         y=json.loads(self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP"]["y"]),
                         color_discrete_map=json.loads(
                             self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP"]["color_discrete_map"]))

        fig.update_layout(title=self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP"]["title"],
                          xaxis_title=self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP"]["xaxis_title"],
                          yaxis_title=self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP"]["yaxis_title"],
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP"]["yaxis_tickformat"])

        if type == 'bar':
            fig.update_layout(barmode=self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP"]["barmode"])

        return fig

    def _figure_deaths_by_week_of_death_and_age_group_in_percent(self,
                                                                 deaths_by_week_of_death_and_age_group:
                                                                 DeathsByWeekOfDeathAndAgeGroupDataFrame,
                                                                 type: str) -> Figure:

        deaths_by_week_of_death_and_age_group = deaths_by_week_of_death_and_age_group.reset_index()

        fig = px.line(deaths_by_week_of_death_and_age_group,
                      x=self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP_IN_PERCENT"]["x"],
                      y=json.loads(self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP_IN_PERCENT"]["y"]),
                      color_discrete_map=json.loads(
                          self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP_IN_PERCENT"]["color_discrete_map"]))

        if type == 'bar':
            fig = px.bar(deaths_by_week_of_death_and_age_group,
                         x=self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP_IN_PERCENT"]["x"],
                         y=json.loads(self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP_IN_PERCENT"]["y"]),
                         color_discrete_map=json.loads(
                             self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP_IN_PERCENT"]["color_discrete_map"]))

        fig.update_layout(title=self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP_IN_PERCENT"]["title"],
                          xaxis_title=self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP_IN_PERCENT"]["xaxis_title"],
                          yaxis_title=self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP_IN_PERCENT"]["yaxis_title"],
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP_IN_PERCENT"]["yaxis_tickformat"])

        if type == 'bar':
            fig.update_layout(barmode=self.config["FIG_DEATHS_BY_WEEK_OF_DEATH_AND_AGE_GROUP_IN_PERCENT"]["barmode"])

        return fig

    def _figure_new_deaths_by_refdate(self,
                                      corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                                      nowcast_rki: NowcastRKIDataFrame) -> Figure:

        y = json.loads(self.config["FIG_NEW_DEATHS_PER_REFDATE"]["y"])
        corona_cases_and_deaths_with_nowcast = self._concat_corona_cases_and_deaths_with_nowcast_only_rows_with_data(
            corona_cases_and_deaths, nowcast_rki, y)

        fig = px.bar(corona_cases_and_deaths_with_nowcast,
                     x=self.config["FIG_NEW_DEATHS_PER_REFDATE"]["x"],
                     y=y,
                     color_discrete_map=json.loads(self.config["FIG_NEW_DEATHS_PER_REFDATE"]["color_discrete_map"]))

        fig.update_layout(title=self.config["FIG_NEW_DEATHS_PER_REFDATE"]["title"],
                          barmode=self.config["FIG_NEW_DEATHS_PER_REFDATE"]["barmode"],
                          xaxis_title=self.config["FIG_NEW_DEATHS_PER_REFDATE"]["xaxis_title"],
                          yaxis_title=self.config["FIG_NEW_DEATHS_PER_REFDATE"]["yaxis_title"],
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_NEW_DEATHS_PER_REFDATE"]["yaxis_tickformat"])

        return fig

    def _concat_corona_cases_and_deaths_with_nowcast_only_rows_with_data(self, corona_cases_and_deaths, nowcast_rki, y):
        corona_cases_and_deaths_with_nowcast = pd.concat([corona_cases_and_deaths, nowcast_rki], axis=1)

        if len(self._delete_rows_without_data_of(corona_cases_and_deaths_with_nowcast, y)) > 0:
            corona_cases_and_deaths_with_nowcast = self._delete_rows_without_data_of(
                corona_cases_and_deaths_with_nowcast, y)
        return corona_cases_and_deaths_with_nowcast.reset_index()

    def _delete_rows_without_data_of(self, df: pd.DataFrame, column_name: str) -> pd.DataFrame:
        if len(df.loc[:, column_name].dropna(how='all', axis=0)) > 0:
            return df.loc[:, column_name].dropna(how='all', axis=0)
        return df

    def _figure_total_cases_by_refdate(self,
                                       corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                                       nowcast_rki: NowcastRKIDataFrame) -> Figure:

        corona_cases_and_deaths_with_nowcast = pd.concat([corona_cases_and_deaths, nowcast_rki], axis=1).reset_index()

        fig = px.bar(corona_cases_and_deaths_with_nowcast,
                     x=self.config["FIG_TOTAL_CASES_PER_REFDATE"]["x"],
                     y=json.loads(self.config["FIG_TOTAL_CASES_PER_REFDATE"]["y"]),
                     color_discrete_map=json.loads(self.config["FIG_TOTAL_CASES_PER_REFDATE"]["color_discrete_map"]))

        fig.update_layout(title=self.config["FIG_TOTAL_CASES_PER_REFDATE"]["title"],
                          barmode=self.config["FIG_TOTAL_CASES_PER_REFDATE"]["barmode"],
                          xaxis_title=self.config["FIG_TOTAL_CASES_PER_REFDATE"]["xaxis_title"],
                          yaxis_title=self.config["FIG_TOTAL_CASES_PER_REFDATE"]["yaxis_title"],
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_TOTAL_CASES_PER_REFDATE"]["yaxis_tickformat"])

        return fig

    def _figure_new_cases_by_reporting_date(self,
                                            corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                                            nowcast_rki: NowcastRKIDataFrame) -> Figure:

        y = json.loads(self.config["FIG_NEW_CASES_BY_REPORTING_DATE"]["y"])

        corona_cases_and_deaths_with_nowcast = self._concat_corona_cases_and_deaths_with_nowcast_only_rows_with_data(
            corona_cases_and_deaths, nowcast_rki, y)

        fig = px.bar(corona_cases_and_deaths_with_nowcast,
                     x=self.config["FIG_NEW_CASES_BY_REPORTING_DATE"]["x"],
                     y=y,
                     color_discrete_map=json.loads(self.config["FIG_NEW_CASES_BY_REPORTING_DATE"]["color_discrete_map"])
                     )

        fig.update_layout(title=self.config["FIG_NEW_CASES_BY_REPORTING_DATE"]["title"],
                          barmode=self.config["FIG_NEW_CASES_BY_REPORTING_DATE"]["barmode"],
                          xaxis_title=self.config["FIG_NEW_CASES_BY_REPORTING_DATE"]["xaxis_title"],
                          yaxis_title=self.config["FIG_NEW_CASES_BY_REPORTING_DATE"]["yaxis_title"],
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_NEW_CASES_BY_REPORTING_DATE"]["yaxis_tickformat"])

        return fig

    def _figure_total_deaths_by_refdate(self,
                                        corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                                        nowcast_rki: NowcastRKIDataFrame) -> Figure:

        corona_cases_and_deaths_with_nowcast = pd.concat([corona_cases_and_deaths, nowcast_rki], axis=1).reset_index()

        fig = px.bar(corona_cases_and_deaths_with_nowcast,
                     x=self.config["FIG_TOTAL_DEATHS_PER_REFDATE"]["x"],
                     y=json.loads(self.config["FIG_TOTAL_DEATHS_PER_REFDATE"]["y"]),
                     color_discrete_map=json.loads(self.config["FIG_TOTAL_DEATHS_PER_REFDATE"]["color_discrete_map"]))

        fig.update_layout(title=self.config["FIG_TOTAL_DEATHS_PER_REFDATE"]["title"],
                          barmode=self.config["FIG_TOTAL_DEATHS_PER_REFDATE"]["barmode"],
                          xaxis_title=self.config["FIG_TOTAL_DEATHS_PER_REFDATE"]["xaxis_title"],
                          yaxis_title=self.config["FIG_TOTAL_DEATHS_PER_REFDATE"]["yaxis_title"],
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_TOTAL_DEATHS_PER_REFDATE"]["yaxis_tickformat"])

        return fig
