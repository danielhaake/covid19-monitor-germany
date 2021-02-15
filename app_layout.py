# ------------------------------ CREATE PLOTS ----------------------------------------#
from typing import List, TypeVar, TypedDict

import dash_core_components as dcc
import dash_html_components as html

import configparser
import json

import plotly.express as px
from plotly.subplots import make_subplots
from plotly.graph_objects import Figure

import pandas as pd
import numpy as np

from data_pandas_subclasses.CoronaCasesAndDeaths import CoronaCasesAndDeathsDataFrame
from data_pandas_subclasses.NowcastRKI import NowcastRKIDataFrame
from data_pandas_subclasses.AgeDistribution import AgeDistributionDataFrame
from data_pandas_subclasses.ClinicalAspects import ClinicalAspectsDataFrame
from data_pandas_subclasses.IntensiveRegister import IntensiveRegisterDataFrame
from data_pandas_subclasses.NumberPCRTests import NumberPCRTestsDataFrame

THtml = TypeVar('THtml', html.H1, html.H2, html.H3, html.H4, html.H5, html.H6, html.Br, html.A, html.Hr, str)
TNum = TypeVar('TNum', int, float)


class Layout:

    class DailyFiguresDict(TypedDict):
        cases_cumulative: int
        last_cases_reported_by_rki: int
        last_mean_cases: int
        last_mean_cases_change_since_day_before: int
        cases_last_7_days: int
        cases_last_7_days_change_since_day_before: int
        cases_last_7_days_by_reporting_date: int
        cases_last_7_days_by_reporting_date_change_since_day_before: int
        deaths_cumulative: int
        last_deaths_reported_by_rki: int
        last_mean_deaths: int
        last_mean_deaths_change_since_day_before: int
        deaths_last_7_days: int
        deaths_last_7_days_change_since_day_before: int
        last_r0: float
        last_r0_change_since_day_before: float
        last_r0_by_nowcast_rki: float
        last_r0_by_nowcast_rki_change_since_day_before: float
        last_r0_by_new_admissions_to_intensive_care: float
        last_r0_by_new_admissions_to_intensive_care_change_since_day_before: float

    def __init__(self):
        self.config = configparser.ConfigParser(interpolation=None)
        self.config.read('graph_definitions.ini')

    def layout(self) -> html.Div:
        return html.Div(
            children=[
                html.Div(
                    id='headline',
                    children=self._headline()
                ),

                html.Div(
                    id='tabs-with-graphs-and-figures',
                    children=[
                        dcc.Interval('graph-update',
                                     interval=600000,
                                     n_intervals=0),
                        dcc.Tabs(id='tabs-global-overview',
                                 value='daily-overview',
                                 parent_className='tabs',
                                 children=self.tabs_with_graphs())
                    ]
                )
            ]
        )

    def _headline(self) -> List[THtml]:
        return [
            html.A(
                html.Img(id='logo', src='assets/logo_um.png'),
                href='https://www.unbelievable-machine.com/',
                target='_blank'),
            html.H3(id='app-title',
                    children='COVID-19 MONITOR GERMANY'),
            html.Hr()
        ]

    def tabs_with_graphs(self) -> List[dcc.Tab]:
        # ----------------------------- LOAD DATA AS DATAFRAMES ----------------------#

        corona_cases_and_deaths = CoronaCasesAndDeathsDataFrame.from_csv()
        nowcast_rki = NowcastRKIDataFrame.from_csv()
        number_pcr_tests = NumberPCRTestsDataFrame.from_csv()
        intensive_register = IntensiveRegisterDataFrame.from_csv()
        clinical_aspects = ClinicalAspectsDataFrame.from_csv()
        age_distribution = AgeDistributionDataFrame.from_csv()

        # ----------------------------- LOAD DATA FOR DAILY OVERVIEW ----------------------#

        daily_figures = self._get_daily_figures(corona_cases_and_deaths, nowcast_rki, intensive_register)

        # TAB STYLING
        # https://dash.plotly.com/dash-core-components/tabs

        return [dcc.Tab(label='Daily Overview',
                        value='daily-overview',
                        className='tab',
                        selected_className='tab-selected',
                        id='tab-daily-overview',
                        children=self._tab_daily_overview(daily_figures,
                                                          corona_cases_and_deaths,
                                                          nowcast_rki)
                        ),

                dcc.Tab(label='Corona cases',
                        value='tab-corona-cases',
                        className='tab',
                        selected_className='tab-selected',
                        id='tab-corona-cases',
                        children=self._tab_corona_cases(corona_cases_and_deaths,
                                                        nowcast_rki,
                                                        number_pcr_tests,
                                                        clinical_aspects,
                                                        age_distribution)
                        ),

                dcc.Tab(label='Intensive care',
                        value='tab-intensive-care',
                        className='tab',
                        selected_className='tab-selected',
                        id='tab-intensive-care',
                        children=self._tab_corona_intensive_care(intensive_register)
                        ),

                dcc.Tab(label='Data sources description',
                        value='tab-data-sources-description',
                        className='tab',
                        selected_className='tab-selected',
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
                                 id='daily-overview-r0',
                                 children=self._block_daily_overview_r0(daily_figures)
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
                          age_distribution: AgeDistributionDataFrame) -> List[dcc.Graph]:
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
                id='graph-r0',
                figure=self._figure_r0(corona_cases_and_deaths, nowcast_rki)),
            dcc.Graph(
                id='graph-7d-incidence',
                figure=self._figure_7d_incidences(corona_cases_and_deaths, nowcast_rki)),
            dcc.Graph(
                id='graph-fig-tested',
                figure=self._figure_pcr_tests(number_pcr_tests)),
            dcc.Graph(
                id='graph-fig-clinical-aspects',
                figure=self._figure_clinical_aspects(clinical_aspects)),
            dcc.Graph(
                id='graph-fig-distribution-of-inhabitants-and-deaths',
                figure=self._figure_distribution_of_inhabitants_and_deaths(age_distribution)),
            dcc.Graph(
                id='graph-fig-distribution-of-cases-and-deaths-per-n-inhabitants',
                figure=self._figure_distribution_of_cases_and_deaths_per_n_inhabitants(age_distribution))
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
        with open('./data_sources_description.md', 'r', encoding='utf-8') as input_file:
            text = input_file.read()
        return dcc.Markdown(text,
                            id='data-sources-description-content',
                            dangerously_allow_html=True)

    def _block_daily_overview_cases(self, daily_figures: DailyFiguresDict) -> List[THtml]:
        prefix_mean_cases_change = self._get_prefix(daily_figures["last_mean_cases_change_since_day_before"])

        return [html.H2(children=["cases"]),
                html.Br(),
                html.H3(children=[f'{daily_figures["last_mean_cases"]:,}']),
                'calculated mean cases',
                html.Br(),
                html.Br(),
                f'{prefix_mean_cases_change}{daily_figures["last_mean_cases_change_since_day_before"]:,}',
                html.Br(),
                'mean cases since day before',
                html.Br(),
                html.Br(),
                f'{daily_figures["cases_cumulative"]:,}',
                html.Br(),
                'total number of cases',
                html.Br(),
                html.Br(),
                f'{daily_figures["last_cases_reported_by_rki"]:,}',
                html.Br(),
                'new reported cases by RKI'
                ]

    def _block_daily_overview_deaths(self, daily_figures: DailyFiguresDict) -> List[THtml]:
        prefix_mean_deaths_change = self._get_prefix(daily_figures["last_mean_deaths_change_since_day_before"])

        return [html.H2(children=["deaths"]),
                html.Br(),
                html.H3(children=[f'{daily_figures["last_mean_deaths"]:,}']),
                'calculated mean deaths',
                html.Br(),
                html.Br(),
                f'{prefix_mean_deaths_change}{daily_figures["last_mean_deaths_change_since_day_before"]:,}',
                html.Br(),
                'mean deaths since day before',
                html.Br(),
                html.Br(),
                f'{daily_figures["deaths_cumulative"]:,}',
                html.Br(),
                'total number of deaths',
                html.Br(),
                html.Br(),
                f'{daily_figures["last_deaths_reported_by_rki"]:,}',
                html.Br(),
                'new reported deaths by RKI'
                ]

    def _block_daily_overview_r0(self, daily_figures: DailyFiguresDict) -> List[THtml]:
        prefix_r0_change = self._get_prefix(daily_figures["last_r0_change_since_day_before"])
        prefix_r0_rki_change = self._get_prefix(daily_figures["last_r0_by_nowcast_rki_change_since_day_before"])
        prefix_r0_intensive_care_change = \
            self._get_prefix(daily_figures["last_r0_by_new_admissions_to_intensive_care_change_since_day_before"])

        return [html.H2(children=["R0"]),
                html.Br(),
                html.H3(children=[f'{daily_figures["last_r0"]:,}']),
                'R0 calculated by mean cases',
                html.Br(),
                html.Br(),
                f'{prefix_r0_change}{daily_figures["last_r0_change_since_day_before"]:,}',
                html.Br(),
                'change since day before',
                html.Br(),
                html.Br(),
                f'{daily_figures["last_r0_by_nowcast_rki"]:,} '
                f'({prefix_r0_rki_change}{daily_figures["last_r0_by_nowcast_rki_change_since_day_before"]:,})',
                html.Br(),
                '7 day R0 reported by RKI',
                html.Br(),
                html.Br(),
                f'{daily_figures["last_r0_by_new_admissions_to_intensive_care"]:,} '
                f'({prefix_r0_intensive_care_change}'
                f'{daily_figures["last_r0_by_new_admissions_to_intensive_care_change_since_day_before"]:,})',
                html.Br(),
                'R0 by new admissions to intensive care'
                ]

    def _block_daily_overview_last_7_days(self, daily_figures: DailyFiguresDict) -> List[THtml]:
        prefix_cases_7_days_change = self._get_prefix(daily_figures["cases_last_7_days_change_since_day_before"])
        prefix_cases_7_days_by_reporting_date_change = \
            self._get_prefix(daily_figures["cases_last_7_days_by_reporting_date_change_since_day_before"])
        prefix_deaths_7_days_change = self._get_prefix(daily_figures["deaths_last_7_days_change_since_day_before"])

        return [html.H2(children=["last 7 days"]),
                html.Br(),
                html.H3(children=[f'{daily_figures["cases_last_7_days"]:,}']),
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

        cases_cumulative = int(corona_cases_and_deaths.get_last_cases_cumulative())
        last_rki_reported_cases = int(corona_cases_and_deaths.get_last_reported_cases())
        last_mean_cases = int(np.round(corona_cases_and_deaths.get_last_mean_cases()))

        last_mean_cases_change_day_before = \
            corona_cases_and_deaths.get_change_from_second_last_to_last_date_for_mean_cases()
        last_mean_cases_change_day_before = int(np.round(last_mean_cases_change_day_before))

        incidence_cases = int(np.round(corona_cases_and_deaths.get_last_7_day_incidence_per_100_000_inhabitants()))

        incidence_cases_change = \
            corona_cases_and_deaths.get_change_from_second_last_to_last_date_for_7_day_incidence_per_100_000_inhabitants()
        incidence_cases_change = int(np.round(incidence_cases_change))

        incidence_cases_by_reporting_date = \
            corona_cases_and_deaths.get_last_7_day_incidence_per_100_000_inhabitants_by_reporting_date()
        incidence_cases_by_reporting_date = int(np.round(incidence_cases_by_reporting_date))

        incidence_cases_change_by_reporting_date = \
            corona_cases_and_deaths. \
                get_change_from_second_last_to_last_date_for_7_day_incidence_per_100_000_inhabitants_by_reporting_date()
        incidence_cases_change_by_reporting_date = int(np.round(incidence_cases_change_by_reporting_date))

        deaths_cumulative = int(corona_cases_and_deaths.get_last_deaths_cumulative())
        last_rki_reported_deaths = int(corona_cases_and_deaths.get_last_reported_deaths())
        last_mean_deaths = int(np.round(corona_cases_and_deaths.get_last_mean_deaths()))

        last_mean_deaths_change_day_before = \
            corona_cases_and_deaths.get_change_from_second_last_to_last_date_for_mean_deaths()
        last_mean_deaths_change_day_before = int(np.round(last_mean_deaths_change_day_before))

        incidence_deaths = corona_cases_and_deaths.get_last_7_day_deaths_by_mean_cases_per_1_000_000_inhabitants()
        incidence_deaths = int(np.round(incidence_deaths))

        incidence_deaths_change = \
            corona_cases_and_deaths. \
                get_change_from_second_last_to_last_date_for_7_day_deaths_by_mean_cases_per_1_000_000_inhabitants()
        incidence_deaths_change = int(np.round(incidence_deaths_change))

        last_r0 = np.round(corona_cases_and_deaths.get_last_r0_by_mean_cases(), 2)
        r0_change = np.round(corona_cases_and_deaths.get_change_from_second_last_to_last_date_for_r0_by_mean_cases(), 2)
        last_r0_nowcast = np.round(nowcast_rki.get_last_r0(), 2)
        r0_nowcast_change = np.round(nowcast_rki.get_change_from_second_last_to_last_date_for_r0(), 2)
        last_r0_intensive_register = np.round(intensive_register.get_last_r0_by_mean_cases(), 2)
        r0_intensive_register_change = np.round(
            intensive_register.get_change_from_second_last_to_last_date_for_r0_by_mean_cases(), 2)

        daily_figures: Layout.DailyFiguresDict = \
            {"cases_cumulative": cases_cumulative,
             "last_cases_reported_by_rki": last_rki_reported_cases,
             "last_mean_cases": last_mean_cases,
             "last_mean_cases_change_since_day_before": last_mean_cases_change_day_before,
             "cases_last_7_days": incidence_cases,
             "cases_last_7_days_change_since_day_before": incidence_cases_change,
             "cases_last_7_days_by_reporting_date": incidence_cases_by_reporting_date,
             "cases_last_7_days_by_reporting_date_change_since_day_before": incidence_cases_change_by_reporting_date,
             "deaths_cumulative": deaths_cumulative,
             "last_deaths_reported_by_rki": last_rki_reported_deaths,
             "last_mean_deaths": last_mean_deaths,
             "last_mean_deaths_change_since_day_before": last_mean_deaths_change_day_before,
             "deaths_last_7_days": incidence_deaths,
             "deaths_last_7_days_change_since_day_before": incidence_deaths_change,
             "last_r0": last_r0,
             "last_r0_change_since_day_before": r0_change,
             "last_r0_by_nowcast_rki": last_r0_nowcast,
             "last_r0_by_nowcast_rki_change_since_day_before": r0_nowcast_change,
             "last_r0_by_new_admissions_to_intensive_care": last_r0_intensive_register,
             "last_r0_by_new_admissions_to_intensive_care_change_since_day_before": r0_intensive_register_change
             }

        return daily_figures

    def _figure_cases_mean_3(self,
                             corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                             nowcast_rki: NowcastRKIDataFrame) -> Figure:

        corona_cases_and_deaths_with_nowcast = pd.concat([corona_cases_and_deaths, nowcast_rki], axis=1).reset_index()

        corona_cases_and_deaths_with_nowcast.loc[:, self.config["FIG_CASES_MEAN_3"]["hover_data"]] = \
            corona_cases_and_deaths_with_nowcast.loc[:, self.config["FIG_CASES_MEAN_3"]["hover_data"]] \
                .dt.strftime('%b %d, %Y')

        fig = make_subplots(specs=[[{"secondary_y": False}]])

        mainfig = px.line(corona_cases_and_deaths_with_nowcast,
                          x=self.config["FIG_CASES_MEAN_3"]["x"],
                          y=json.loads(self.config["FIG_CASES_MEAN_3"]["y"]),
                          color_discrete_map=json.loads(self.config["FIG_CASES_MEAN_3"]["color_discrete_map"]),
                          render_mode=self.config["ALL_FIGS"]["render_mode"],
                          hover_data=[self.config["FIG_CASES_MEAN_3"]["hover_data"]])

        subfig = px.line(corona_cases_and_deaths_with_nowcast,
                         x=self.config["FIG_CASES_MEAN_3"]["x"],
                         y=json.loads(self.config["FIG_CASES_MEAN_3_SUBFIG"]["y"]),
                         color_discrete_map=json.loads(self.config["FIG_CASES_MEAN_3_SUBFIG"]["color_discrete_map"]),
                         render_mode=self.config["ALL_FIGS"]["render_mode"])

        fig.add_traces(mainfig.data + subfig.data)

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
        corona_cases_and_deaths_with_nowcast.loc[:, self.config["FIG_DEATHS_MEAN_3"]["hover_data"]] = \
            corona_cases_and_deaths_with_nowcast.loc[:, self.config["FIG_DEATHS_MEAN_3"]["hover_data"]] \
                .dt.strftime('%b %d, %Y')

        fig = make_subplots(specs=[[{"secondary_y": False}]])

        mainfig = px.line(corona_cases_and_deaths_with_nowcast,
                          x=self.config["FIG_DEATHS_MEAN_3"]["x"],
                          y=json.loads(self.config["FIG_DEATHS_MEAN_3"]["y"]),
                          color_discrete_map=json.loads(self.config["FIG_DEATHS_MEAN_3"]["color_discrete_map"]),
                          render_mode=self.config["ALL_FIGS"]["render_mode"],
                          hover_data=[self.config["FIG_DEATHS_MEAN_3"]["hover_data"]])

        subfig = px.line(corona_cases_and_deaths_with_nowcast,
                         x=self.config["FIG_DEATHS_MEAN_3"]["x"],
                         y=json.loads(self.config["FIG_DEATHS_MEAN_3_SUBFIG"]["y"]),
                         color_discrete_map=json.loads(self.config["FIG_DEATHS_MEAN_3_SUBFIG"]["color_discrete_map"]),
                         render_mode=self.config["ALL_FIGS"]["render_mode"])

        fig.add_traces(mainfig.data + subfig.data)

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

    def _figure_r0(self,
                   corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                   nowcast_rki: NowcastRKIDataFrame) -> Figure:

        corona_cases_and_deaths_with_nowcast = pd.concat([corona_cases_and_deaths, nowcast_rki], axis=1).reset_index()

        fig = px.line(corona_cases_and_deaths_with_nowcast,
                      x=self.config["FIG_R0"]["x"],
                      y=json.loads(self.config["FIG_R0"]["y"]),
                      color_discrete_map=json.loads(self.config["FIG_R0"]["color_discrete_map"]),
                      render_mode=self.config["ALL_FIGS"]["render_mode"])

        min_date = corona_cases_and_deaths_with_nowcast.date.min()
        max_date = corona_cases_and_deaths_with_nowcast.date.max()
        shapes = [{"type": 'line',
                   "y0": 1,
                   "y1": 1,
                   "x0": min_date,
                   "x1": max_date}]

        fig.update_layout(title=self.config["FIG_R0"]["title"],
                          xaxis_title=self.config["FIG_R0"]["xaxis_title"],
                          yaxis_title=self.config["FIG_R0"]["yaxis_title"],
                          shapes=shapes,
                          yaxis=json.loads(self.config["FIG_R0"]["yaxis"]),
                          legend=json.loads(self.config["ALL_FIGS"]["legend"]),
                          font_family=self.config["ALL_FIGS"]["font_family"],
                          font_color=self.config["ALL_FIGS"]["font_color"],
                          plot_bgcolor=self.config["ALL_FIGS"]["plot_bgcolor"],
                          paper_bgcolor=self.config["ALL_FIGS"]["paper_bgcolor"],
                          yaxis_tickformat=self.config["FIG_R0"]["yaxis_tickformat"])
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

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        mainfig = \
            px.bar(number_pcr_tests,
                   x=self.config["FIG_PCR_TESTS"]["x"],
                   y=json.loads(self.config["FIG_PCR_TESTS"]["y"]),
                   color_discrete_map=json.loads(self.config["FIG_PCR_TESTS"]["color_discrete_map"]))

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

        clinical_aspects = clinical_aspects.reset_index()

        fig = px.line(clinical_aspects,
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

    def _figure_new_deaths_by_refdate(self,
                                      corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                                      nowcast_rki: NowcastRKIDataFrame) -> Figure:

        y = json.loads(self.config["FIG_NEW_DEATHS_PER_REFDATE"]["y"])
        corona_cases_and_deaths_with_nowcast = pd.concat([corona_cases_and_deaths, nowcast_rki], axis=1)
        corona_cases_and_deaths_with_nowcast = corona_cases_and_deaths_with_nowcast.loc[:, y].dropna(how='all', axis=0)
        corona_cases_and_deaths_with_nowcast = corona_cases_and_deaths_with_nowcast.reset_index()

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

        corona_cases_and_deaths_with_nowcast = pd.concat([corona_cases_and_deaths, nowcast_rki], axis=1)
        corona_cases_and_deaths_with_nowcast = corona_cases_and_deaths_with_nowcast.loc[:, y].dropna(how='all', axis=0)
        corona_cases_and_deaths_with_nowcast = corona_cases_and_deaths_with_nowcast.reset_index()

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