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


class Layout:
    class FiguresDict(TypedDict):
        fig_cases_mean_3: Figure
        fig_deaths_mean_3: Figure
        fig_r0: Figure
        fig_7d_incidences: Figure
        fig_pcr_tests: Figure
        fig_distribution_of_inhabitants_and_deaths: Figure
        fig_distribution_of_cases_and_deaths_per_n_inhabitants: Figure
        fig_intensive_new: Figure
        fig_intensive_daily_change: Figure
        fig_intensive_reporting_areas: Figure
        fig_intensive_care_ventilated: Figure
        fig_intensive_beds: Figure
        fig_intensive_beds_prop: Figure
        fig_proportions_cases_hospitalizations_deaths: Figure
        fig_new_deaths_per_refdate: Figure
        fig_new_cases_by_reporting_date: Figure
        fig_total_cases_by_refdate: Figure
        fig_total_deaths_by_refdate: Figure

    class DailyFiguresDict(TypedDict):
        cases_cumulative: int
        last_cases_reported_by_RKI: int
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

        # ----------------------------- CREATE PLOT OBJECTS ----------------------#

        plots = self._plot_objects(corona_cases_and_deaths,
                                   nowcast_rki,
                                   number_pcr_tests,
                                   intensive_register,
                                   clinical_aspects,
                                   age_distribution)

        # TAB STYLING
        # https://dash.plotly.com/dash-core-components/tabs

        return [dcc.Tab(label='Daily Overview',
                        value='daily-overview',
                        className='tab',
                        selected_className='tab-selected',
                        id='tab-daily-overview',
                        children=self._tab_daily_overview(plots, daily_figures)
                        ),

                dcc.Tab(label='Corona cases',
                        value='tab-corona-cases',
                        className='tab',
                        selected_className='tab-selected',
                        id='tab-corona-cases',
                        children=self._tab_corona_cases(plots)
                        ),

                dcc.Tab(label='Intensive care',
                        value='tab-intensive-care',
                        className='tab',
                        selected_className='tab-selected',
                        id='tab-intensive-care',
                        children=self._tab_corona_intensive_care(plots)
                        ),
                ]

    def _tab_daily_overview(self, plots: FiguresDict, daily_figures: DailyFiguresDict) -> List[html.Div]:
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
                                 figure=plots["fig_new_deaths_per_refdate"]),
                             dcc.Graph(
                                 id='graph-new-cases-by-reporting-date',
                                 figure=plots["fig_new_cases_by_reporting_date"])
                         ]
                         )
                ]

    def _tab_corona_cases(self, plots: FiguresDict) -> List[dcc.Graph]:
        return [
            dcc.Graph(
                id='graph-cases-mean-3',
                figure=plots["fig_cases_mean_3"]),
            dcc.Graph(
                id='graph-total-cases-by-refdate',
                figure=plots["fig_total_cases_by_refdate"]),
            dcc.Graph(
                id='graph-deaths-mean-3',
                figure=plots["fig_deaths_mean_3"]),
            dcc.Graph(
                id='graph-total-deaths-by-refdate',
                figure=plots["fig_total_deaths_by_refdate"]),
            dcc.Graph(
                id='graph-r0',
                figure=plots["fig_r0"]),
            dcc.Graph(
                id='graph-7d-incidence',
                figure=plots["fig_7d_incidences"]),
            dcc.Graph(
                id='graph-fig-tested',
                figure=plots["fig_pcr_tests"]),
            dcc.Graph(
                id='graph-fig-proportions-cases-hospitalizations-deaths',
                figure=plots["fig_proportions_cases_hospitalizations_deaths"]),
            dcc.Graph(
                id='graph-fig-distribution-of-inhabitants-and-deaths',
                figure=plots["fig_distribution_of_inhabitants_and_deaths"]),
            dcc.Graph(
                id='graph-fig-distribution-of-cases-and-deaths-per-n-inhabitants',
                figure=plots["fig_distribution_of_cases_and_deaths_per_n_inhabitants"])
        ]

    def _tab_corona_intensive_care(self, plots: FiguresDict) -> List[dcc.Graph]:
        return [
            dcc.Graph(
                id='graph-fig-intensive-reporting-areas',
                figure=plots["fig_intensive_reporting_areas"]),
            dcc.Graph(
                id='graph-fig-intensive-new',
                figure=plots["fig_intensive_new"]),
            dcc.Graph(
                id='graph-fig-intensive-daily-change',
                figure=plots["fig_intensive_daily_change"]),
            dcc.Graph(
                id='graph-fig-intensive-care-ventilated',
                figure=plots["fig_intensive_care_ventilated"]),
            dcc.Graph(
                id='graph-fig-intensive-beds',
                figure=plots["fig_intensive_beds"]),
            dcc.Graph(
                id='graph-fig-intensive-beds-prop',
                figure=plots["fig_intensive_beds_prop"])
        ]

    def _block_daily_overview_cases(self, daily_figures: DailyFiguresDict) -> List[THtml]:
        prefix_mean_cases_change = ""
        if daily_figures["last_mean_cases_change_since_day_before"] > 0:
            prefix_mean_cases_change = "+"

        if daily_figures["last_mean_cases_change_since_day_before"] == 0:
            prefix_mean_cases_change = "±"

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
        prefix_mean_deaths_change = ""
        if daily_figures["last_mean_deaths_change_since_day_before"] > 0:
            prefix_mean_deaths_change = "+"
        if daily_figures["last_mean_deaths_change_since_day_before"] == 0:
            prefix_mean_deaths_change = "±"

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
        prefix_r0_change = ""
        if daily_figures["last_r0_change_since_day_before"] > 0:
            prefix_r0_change = "+"
        if daily_figures["last_r0_change_since_day_before"] == 0:
            prefix_r0_change = "±"

        prefix_r0_rki_change = ""
        if daily_figures["last_r0_by_nowcast_rki_change_since_day_before"] > 0:
            prefix_r0_rki_change = "+"
        if daily_figures["last_r0_by_nowcast_rki_change_since_day_before"] == 0:
            prefix_r0_rki_change = "±"

        prefix_r0_intensive_care_change = ""
        if daily_figures["last_r0_by_new_admissions_to_intensive_care_change_since_day_before"] > 0:
            prefix_r0_intensive_care_change = "+"
        if daily_figures["last_r0_by_new_admissions_to_intensive_care_change_since_day_before"] == 0:
            prefix_r0_intensive_care_change = "±"

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
        prefix_cases_7_days_change = ""
        if daily_figures["cases_last_7_days_change_since_day_before"] > 0:
            prefix_cases_7_days_change = "+"
        if daily_figures["cases_last_7_days_change_since_day_before"] == 0:
            prefix_cases_7_days_change = "±"

        prefix_cases_7_days_by_reporting_date_change = ""
        if daily_figures["cases_last_7_days_by_reporting_date_change_since_day_before"] > 0:
            prefix_cases_7_days_by_reporting_date_change = "+"
        if daily_figures["cases_last_7_days_by_reporting_date_change_since_day_before"] == 0:
            prefix_cases_7_days_by_reporting_date_change = "±"

        prefix_deaths_7_days_change = ""
        if daily_figures["deaths_last_7_days_change_since_day_before"] > 0:
            prefix_deaths_7_days_change = "+"
        if daily_figures["deaths_last_7_days_change_since_day_before"] == 0:
            prefix_deaths_7_days_change = "±"

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

    def _get_daily_figures(self,
                           corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                           nowcast_rki: NowcastRKIDataFrame,
                           intensive_register: IntensiveRegisterDataFrame) -> DailyFiguresDict:

        cases_cumulative = int(corona_cases_and_deaths.get_last_cases_cumulative())
        last_rki_reported_cases = int(corona_cases_and_deaths.get_last_reported_cases())
        last_mean_cases = int(np.round(corona_cases_and_deaths.get_last_mean_cases()))
        last_mean_cases_change_day_before = \
            int(np.round(
                corona_cases_and_deaths
                    .get_change_from_second_last_to_last_date_for_mean_cases())
            )

        incidence_cases = int(np.round(corona_cases_and_deaths.get_last_7_day_incidence_per_100_000_inhabitants()))
        incidence_cases_change = \
            int(np.round(
                corona_cases_and_deaths
                    .get_change_from_second_last_to_last_date_for_7_day_incidence_per_100_000_inhabitants())
            )

        incidence_cases_by_reporting_date = \
            int(np.round(
                corona_cases_and_deaths
                    .get_last_7_day_incidence_per_100_000_inhabitants_by_reporting_date())
            )

        incidence_cases_change_by_reporting_date = \
            int(np.round(
                corona_cases_and_deaths
                    .get_change_from_second_last_to_last_date_for_7_day_incidence_per_100_000_inhabitants_by_reporting_date())
            )

        deaths_cumulative = int(corona_cases_and_deaths.get_last_deaths_cumulative())
        last_rki_reported_deaths = int(corona_cases_and_deaths.get_last_reported_deaths())
        last_mean_deaths = int(np.round(corona_cases_and_deaths.get_last_mean_deaths()))
        last_mean_deaths_change_day_before = \
            int(np.round(
                corona_cases_and_deaths
                    .get_change_from_second_last_to_last_date_for_mean_deaths())
            )

        incidence_deaths = \
            int(np.round(
                corona_cases_and_deaths
                    .get_last_7_day_deaths_by_mean_cases_per_1_000_000_inhabitants())
            )

        incidence_deaths_change = \
            int(np.round(
                corona_cases_and_deaths
                    .get_change_from_second_last_to_last_date_for_7_day_deaths_by_mean_cases_per_1_000_000_inhabitants())
            )

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

        render_mode = self.config["ALL_FIGS"]["render_mode"]
        x = self.config["FIG_CASES_MEAN_3"]["x"]
        y = json.loads(self.config["FIG_CASES_MEAN_3"]["y"])
        color_discrete_map = json.loads(self.config["FIG_CASES_MEAN_3"]["color_discrete_map"])
        labels = json.loads(self.config["FIG_CASES_MEAN_3"]["labels"])
        title = self.config["FIG_CASES_MEAN_3"]["title"]
        xaxis_title = self.config["FIG_CASES_MEAN_3"]["xaxis_title"]
        yaxis_title = self.config["FIG_CASES_MEAN_3"]["yaxis_title"]
        legend = json.loads(self.config["ALL_FIGS"]["legend"])
        font_family = self.config["ALL_FIGS"]["font_family"]
        font_color = self.config["ALL_FIGS"]["font_color"]
        plot_bgcolor = self.config["ALL_FIGS"]["plot_bgcolor"]
        paper_bgcolor = self.config["ALL_FIGS"]["paper_bgcolor"]

        corona_cases_and_deaths_with_nowcast = pd.concat([corona_cases_and_deaths, nowcast_rki], axis=1).reset_index()

        fig_cases_mean_3 = px.line(corona_cases_and_deaths_with_nowcast,
                                   x=x,
                                   y=y,
                                   color_discrete_map=color_discrete_map,
                                   labels=labels,
                                   render_mode=render_mode)

        fig_cases_mean_3.update_layout(title=title,
                                       xaxis_title=xaxis_title,
                                       yaxis_title=yaxis_title,
                                       legend=legend,
                                       font_family=font_family,
                                       font_color=font_color,
                                       plot_bgcolor=plot_bgcolor,
                                       paper_bgcolor=paper_bgcolor)
        return fig_cases_mean_3

    def _figure_deaths_mean_3(self,
                              corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                              nowcast_rki: NowcastRKIDataFrame) -> Figure:

        render_mode = self.config["ALL_FIGS"]["render_mode"]
        x = self.config["FIG_DEATHS_MEAN_3"]["x"]
        y = json.loads(self.config["FIG_DEATHS_MEAN_3"]["y"])
        color_discrete_map = json.loads(self.config["FIG_DEATHS_MEAN_3"]["color_discrete_map"])
        title = self.config["FIG_DEATHS_MEAN_3"]["title"]
        xaxis_title = self.config["FIG_DEATHS_MEAN_3"]["xaxis_title"]
        yaxis_title = self.config["FIG_DEATHS_MEAN_3"]["yaxis_title"]
        legend = json.loads(self.config["ALL_FIGS"]["legend"])
        font_family = self.config["ALL_FIGS"]["font_family"]
        font_color = self.config["ALL_FIGS"]["font_color"]
        plot_bgcolor = self.config["ALL_FIGS"]["plot_bgcolor"]
        paper_bgcolor = self.config["ALL_FIGS"]["paper_bgcolor"]

        corona_cases_and_deaths_with_nowcast = pd.concat([corona_cases_and_deaths, nowcast_rki], axis=1).reset_index()

        fig_deaths_mean_3 = px.line(corona_cases_and_deaths_with_nowcast,
                                    x=x,
                                    y=y,
                                    color_discrete_map=color_discrete_map,
                                    render_mode=render_mode)

        fig_deaths_mean_3.update_layout(title=title,
                                        xaxis_title=xaxis_title,
                                        yaxis_title=yaxis_title,
                                        legend=legend,
                                        font_family=font_family,
                                        font_color=font_color,
                                        plot_bgcolor=plot_bgcolor,
                                        paper_bgcolor=paper_bgcolor)

        return fig_deaths_mean_3

    def _figure_r0(self,
                   corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                   nowcast_rki: NowcastRKIDataFrame) -> Figure:
        render_mode = self.config["ALL_FIGS"]["render_mode"]
        x = self.config["FIG_R0"]["x"]
        y = json.loads(self.config["FIG_R0"]["y"])
        color_discrete_map = json.loads(self.config["FIG_R0"]["color_discrete_map"])
        title = self.config["FIG_R0"]["title"]
        xaxis_title = self.config["FIG_R0"]["xaxis_title"]
        yaxis_title = self.config["FIG_R0"]["yaxis_title"]
        yaxis = json.loads(self.config["FIG_R0"]["yaxis"])
        legend = json.loads(self.config["ALL_FIGS"]["legend"])
        font_family = self.config["ALL_FIGS"]["font_family"]
        font_color = self.config["ALL_FIGS"]["font_color"]
        plot_bgcolor = self.config["ALL_FIGS"]["plot_bgcolor"]
        paper_bgcolor = self.config["ALL_FIGS"]["paper_bgcolor"]

        corona_cases_and_deaths_with_nowcast = pd.concat([corona_cases_and_deaths, nowcast_rki], axis=1).reset_index()
        min_date = corona_cases_and_deaths_with_nowcast.date.min()
        max_date = corona_cases_and_deaths_with_nowcast.date.max()
        shapes = [{"type": 'line',
                   "y0": 1,
                   "y1": 1,
                   "x0": min_date,
                   "x1": max_date}]

        fig_r0 = px.line(corona_cases_and_deaths_with_nowcast,
                         x=x,
                         y=y,
                         color_discrete_map=color_discrete_map,
                         render_mode=render_mode)
        fig_r0.update_layout(title=title,
                             xaxis_title=xaxis_title,
                             yaxis_title=yaxis_title,
                             shapes=shapes,
                             yaxis=yaxis,
                             legend=legend,
                             font_family=font_family,
                             font_color=font_color,
                             plot_bgcolor=plot_bgcolor,
                             paper_bgcolor=paper_bgcolor)
        return fig_r0

    def _figure_7d_incidences(self,
                              corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                              nowcast_rki: NowcastRKIDataFrame) -> Figure:

        render_mode = self.config["ALL_FIGS"]["render_mode"]
        x = self.config["FIG_7D_INCIDENCES"]["x"]
        y = json.loads(self.config["FIG_7D_INCIDENCES"]["y"])
        color_discrete_map = json.loads(self.config["FIG_7D_INCIDENCES"]["color_discrete_map"])
        title = self.config["FIG_7D_INCIDENCES"]["title"]
        xaxis_title = self.config["FIG_7D_INCIDENCES"]["xaxis_title"]
        yaxis_title = self.config["FIG_7D_INCIDENCES"]["yaxis_title"]
        legend = json.loads(self.config["ALL_FIGS"]["legend"])
        font_family = self.config["ALL_FIGS"]["font_family"]
        font_color = self.config["ALL_FIGS"]["font_color"]
        plot_bgcolor = self.config["ALL_FIGS"]["plot_bgcolor"]
        paper_bgcolor = self.config["ALL_FIGS"]["paper_bgcolor"]

        corona_cases_and_deaths_with_nowcast = pd.concat([corona_cases_and_deaths, nowcast_rki], axis=1).reset_index()

        fig_7d_incidences = px.line(corona_cases_and_deaths_with_nowcast,
                                    x=x,
                                    y=y,
                                    color_discrete_map=color_discrete_map,
                                    render_mode=render_mode)
        fig_7d_incidences.update_layout(title=title,
                                        xaxis_title=xaxis_title,
                                        yaxis_title=yaxis_title,
                                        legend=legend,
                                        font_family=font_family,
                                        font_color=font_color,
                                        plot_bgcolor=plot_bgcolor,
                                        paper_bgcolor=paper_bgcolor)

        return fig_7d_incidences

    def _figure_pcr_tests(self, number_pcr_tests: NumberPCRTestsDataFrame) -> Figure:
        render_mode = self.config["ALL_FIGS"]["render_mode"]
        x = self.config["FIG_PCR_TESTS"]["x"]
        y = json.loads(self.config["FIG_PCR_TESTS"]["y"])
        color_discrete_map = json.loads(self.config["FIG_PCR_TESTS"]["color_discrete_map"])
        title = self.config["FIG_PCR_TESTS"]["title"]
        xaxis_title = self.config["FIG_PCR_TESTS"]["xaxis_title"]
        yaxis_title = self.config["FIG_PCR_TESTS"]["yaxis_title"]
        legend = json.loads(self.config["ALL_FIGS"]["legend"])
        font_family = self.config["ALL_FIGS"]["font_family"]
        font_color = self.config["ALL_FIGS"]["font_color"]
        plot_bgcolor = self.config["ALL_FIGS"]["plot_bgcolor"]
        paper_bgcolor = self.config["ALL_FIGS"]["paper_bgcolor"]

        number_pcr_tests = number_pcr_tests.reset_index()

        subfig = make_subplots(specs=[[{"secondary_y": True}]])
        fig_pcr_tests = px.bar(number_pcr_tests,
                               x=x,
                               y=y,
                               color_discrete_map=color_discrete_map)

        fig_pcr_tests_percentage = px.line(number_pcr_tests,
                                           x=x,
                                           y="positive rate (%)",
                                           color_discrete_map={"positive rate (%)": "rgb(255,0,0)"},
                                           render_mode=render_mode)
        fig_pcr_tests_percentage.update_traces(yaxis="y2")

        subfig.add_traces(fig_pcr_tests.data + fig_pcr_tests_percentage.data)
        subfig.update_yaxes(title_text="positive rate (%)", secondary_y=True)

        subfig.update_layout(title=title,
                             barmode='stack',
                             xaxis_title=xaxis_title,
                             yaxis_title=yaxis_title,
                             legend=legend,
                             font_family=font_family,
                             font_color=font_color,
                             plot_bgcolor=plot_bgcolor,
                             paper_bgcolor=paper_bgcolor)

        return subfig

    def _figure_distribution_of_inhabitants_and_deaths(self, age_distribution: AgeDistributionDataFrame) -> Figure:
        render_mode = self.config["ALL_FIGS"]["render_mode"]
        x = self.config["FIG_DISTRIBUTION_OF_INHABITANTS"]["x"]
        y = json.loads(self.config["FIG_DISTRIBUTION_OF_INHABITANTS"]["y"])
        color_discrete_map = json.loads(self.config["FIG_DISTRIBUTION_OF_INHABITANTS"]["color_discrete_map"])
        title = self.config["FIG_DISTRIBUTION_OF_INHABITANTS"]["title"]
        xaxis_title = self.config["FIG_DISTRIBUTION_OF_INHABITANTS"]["xaxis_title"]
        yaxis_title = self.config["FIG_DISTRIBUTION_OF_INHABITANTS"]["yaxis_title"]
        legend = json.loads(self.config["ALL_FIGS"]["legend"])
        font_family = self.config["ALL_FIGS"]["font_family"]
        font_color = self.config["ALL_FIGS"]["font_color"]
        plot_bgcolor = self.config["ALL_FIGS"]["plot_bgcolor"]
        paper_bgcolor = self.config["ALL_FIGS"]["paper_bgcolor"]
        y_subfig = json.loads(self.config["SUBFIG_DISTRIBUTION_OF_DEATHS"]["y"])
        color_discrete_map_subfig = json.loads(self.config["SUBFIG_DISTRIBUTION_OF_DEATHS"]["color_discrete_map"])
        yaxis_title_subfig = self.config["SUBFIG_DISTRIBUTION_OF_DEATHS"]["yaxis_title"]
        barmode = self.config["SUBFIG_DISTRIBUTION_OF_DEATHS"]["barmode"]

        age_distribution = age_distribution.reset_index()

        subfig = make_subplots(specs=[[{"secondary_y": True}]])
        fig_distribution_of_inhabitants = px.bar(age_distribution,
                                                 x=x,
                                                 y=y,
                                                 color_discrete_map=color_discrete_map)

        fig_distribution_of_deaths = px.bar(age_distribution,
                                            x=x,
                                            y=y_subfig,
                                            color_discrete_map=color_discrete_map_subfig)
        fig_distribution_of_deaths.update_traces(yaxis="y2")

        subfig.add_traces(
            fig_distribution_of_inhabitants.data + fig_distribution_of_deaths.data)
        subfig.update_yaxes(title_text=yaxis_title_subfig, secondary_y=True)

        subfig.update_layout(title=title,
                             barmode=barmode,
                             xaxis_title=xaxis_title,
                             yaxis_title=yaxis_title,
                             legend=legend,
                             font_family=font_family,
                             font_color=font_color,
                             plot_bgcolor=plot_bgcolor,
                             paper_bgcolor=paper_bgcolor)

        return subfig

    def _figure_distribution_of_cases_and_deaths_per_n_inhabitants(self,
                                                                   age_distribution: AgeDistributionDataFrame) -> Figure:
        render_mode = self.config["ALL_FIGS"]["render_mode"]
        x = self.config["FIG_DISTRIBUTION_OF_CASES_PER_N_INHABITANTS"]["x"]
        y = json.loads(self.config["FIG_DISTRIBUTION_OF_CASES_PER_N_INHABITANTS"]["y"])
        color_discrete_map = json.loads(
            self.config["FIG_DISTRIBUTION_OF_CASES_PER_N_INHABITANTS"]["color_discrete_map"])
        title = self.config["FIG_DISTRIBUTION_OF_CASES_PER_N_INHABITANTS"]["title"]
        xaxis_title = self.config["FIG_DISTRIBUTION_OF_CASES_PER_N_INHABITANTS"]["xaxis_title"]
        yaxis_title = self.config["FIG_DISTRIBUTION_OF_CASES_PER_N_INHABITANTS"]["yaxis_title"]
        legend = json.loads(self.config["ALL_FIGS"]["legend"])
        font_family = self.config["ALL_FIGS"]["font_family"]
        font_color = self.config["ALL_FIGS"]["font_color"]
        plot_bgcolor = self.config["ALL_FIGS"]["plot_bgcolor"]
        paper_bgcolor = self.config["ALL_FIGS"]["paper_bgcolor"]
        y_subfig = json.loads(self.config["SUBFIG_DISTRIBUTION_OF_DEATHS_PER_N_INHABITANTS"]["y"])
        color_discrete_map_subfig = json.loads(
            self.config["SUBFIG_DISTRIBUTION_OF_DEATHS_PER_N_INHABITANTS"]["color_discrete_map"])
        yaxis_title_subfig = self.config["SUBFIG_DISTRIBUTION_OF_DEATHS_PER_N_INHABITANTS"]["yaxis_title"]
        barmode = self.config["SUBFIG_DISTRIBUTION_OF_DEATHS_PER_N_INHABITANTS"]["barmode"]

        age_distribution = age_distribution.reset_index()

        subfig = make_subplots(specs=[[{"secondary_y": True}]])
        fig_distribution_of_cases_per_n_inhabitants = px.bar(age_distribution,
                                                             x=x,
                                                             y=y,
                                                             color_discrete_map=color_discrete_map)

        fig_distribution_of_deaths_per_n_inhabitants = px.bar(age_distribution,
                                                              x=x,
                                                              y=y_subfig,
                                                              color_discrete_map=color_discrete_map_subfig)
        fig_distribution_of_deaths_per_n_inhabitants.update_traces(yaxis="y2")

        subfig.add_traces(
            fig_distribution_of_cases_per_n_inhabitants.data + fig_distribution_of_deaths_per_n_inhabitants.data)
        subfig.update_yaxes(title_text=yaxis_title_subfig, secondary_y=True)

        subfig.update_layout(title=title,
                             barmode=barmode,
                             xaxis_title=xaxis_title,
                             yaxis_title=yaxis_title,
                             legend=legend,
                             font_family=font_family,
                             font_color=font_color,
                             plot_bgcolor=plot_bgcolor,
                             paper_bgcolor=paper_bgcolor)

        return subfig

    def _figure_intensive_new(self, intensive_register: IntensiveRegisterDataFrame) -> Figure:
        render_mode = self.config["ALL_FIGS"]["render_mode"]
        x = self.config["FIG_INTENSIVE_NEW"]["x"]
        y = json.loads(self.config["FIG_INTENSIVE_NEW"]["y"])
        color_discrete_map = json.loads(self.config["FIG_INTENSIVE_NEW"]["color_discrete_map"])
        title = self.config["FIG_INTENSIVE_NEW"]["title"]
        xaxis_title = self.config["FIG_INTENSIVE_NEW"]["xaxis_title"]
        yaxis_title = self.config["FIG_INTENSIVE_NEW"]["yaxis_title"]
        legend = json.loads(self.config["ALL_FIGS"]["legend"])
        font_family = self.config["ALL_FIGS"]["font_family"]
        font_color = self.config["ALL_FIGS"]["font_color"]
        plot_bgcolor = self.config["ALL_FIGS"]["plot_bgcolor"]
        paper_bgcolor = self.config["ALL_FIGS"]["paper_bgcolor"]

        intensive_register = intensive_register.reset_index()

        fig_intensive_new = px.line(intensive_register,
                                    x=x,
                                    y=y,
                                    color_discrete_map=color_discrete_map,
                                    render_mode=render_mode)
        fig_intensive_new.update_layout(title=title,
                                        xaxis_title=xaxis_title,
                                        yaxis_title=yaxis_title,
                                        legend=legend,
                                        font_family=font_family,
                                        font_color=font_color,
                                        plot_bgcolor=plot_bgcolor,
                                        paper_bgcolor=paper_bgcolor)

        return fig_intensive_new

    def _figure_intensive_daily_change(self, intensive_register: IntensiveRegisterDataFrame) -> Figure:
        render_mode = self.config["ALL_FIGS"]["render_mode"]
        x = self.config["FIG_INTENSIVE_DAILY_CHANGE"]["x"]
        y = json.loads(self.config["FIG_INTENSIVE_DAILY_CHANGE"]["y"])
        color_discrete_map = json.loads(self.config["FIG_INTENSIVE_DAILY_CHANGE"]["color_discrete_map"])
        title = self.config["FIG_INTENSIVE_DAILY_CHANGE"]["title"]
        xaxis_title = self.config["FIG_INTENSIVE_DAILY_CHANGE"]["xaxis_title"]
        yaxis_title = self.config["FIG_INTENSIVE_DAILY_CHANGE"]["yaxis_title"]
        legend = json.loads(self.config["ALL_FIGS"]["legend"])
        font_family = self.config["ALL_FIGS"]["font_family"]
        font_color = self.config["ALL_FIGS"]["font_color"]
        plot_bgcolor = self.config["ALL_FIGS"]["plot_bgcolor"]
        paper_bgcolor = self.config["ALL_FIGS"]["paper_bgcolor"]

        intensive_register = intensive_register.reset_index()

        fig_intensive_daily_change = px.line(intensive_register,
                                             x=x,
                                             y=y,
                                             color_discrete_map=color_discrete_map,
                                             render_mode=render_mode)
        fig_intensive_daily_change.update_layout(title=title,
                                                 xaxis_title=xaxis_title,
                                                 yaxis_title=yaxis_title,
                                                 legend=legend,
                                                 font_family=font_family,
                                                 font_color=font_color,
                                                 plot_bgcolor=plot_bgcolor,
                                                 paper_bgcolor=paper_bgcolor)

        return fig_intensive_daily_change

    def _figure_intensive_reporting_areas(self, intensive_register: IntensiveRegisterDataFrame) -> Figure:
        render_mode = self.config["ALL_FIGS"]["render_mode"]
        x = self.config["FIG_INTENSIVE_REPORTING_AREAS"]["x"]
        y = json.loads(self.config["FIG_INTENSIVE_REPORTING_AREAS"]["y"])
        color_discrete_map = json.loads(self.config["FIG_INTENSIVE_REPORTING_AREAS"]["color_discrete_map"])
        title = self.config["FIG_INTENSIVE_REPORTING_AREAS"]["title"]
        xaxis_title = self.config["FIG_INTENSIVE_REPORTING_AREAS"]["xaxis_title"]
        yaxis_title = self.config["FIG_INTENSIVE_REPORTING_AREAS"]["yaxis_title"]
        legend = json.loads(self.config["ALL_FIGS"]["legend"])
        font_family = self.config["ALL_FIGS"]["font_family"]
        font_color = self.config["ALL_FIGS"]["font_color"]
        plot_bgcolor = self.config["ALL_FIGS"]["plot_bgcolor"]
        paper_bgcolor = self.config["ALL_FIGS"]["paper_bgcolor"]

        intensive_register = intensive_register.reset_index()

        fig_intensive_reporting_areas = px.line(intensive_register,
                                                x=x,
                                                y=y,
                                                color_discrete_map=color_discrete_map,
                                                render_mode=render_mode)

        fig_intensive_reporting_areas.update_layout(title=title,
                                                    xaxis_title=xaxis_title,
                                                    yaxis_title=yaxis_title,
                                                    legend=legend,
                                                    font_family=font_family,
                                                    font_color=font_color,
                                                    plot_bgcolor=plot_bgcolor,
                                                    paper_bgcolor=paper_bgcolor)

        return fig_intensive_reporting_areas

    def _figure_intensive_care_ventilated(self, intensive_register: IntensiveRegisterDataFrame) -> Figure:
        render_mode = self.config["ALL_FIGS"]["render_mode"]
        x = self.config["FIG_INTENSIVE_CARE_VENTILATED"]["x"]
        y = json.loads(self.config["FIG_INTENSIVE_CARE_VENTILATED"]["y"])
        color_discrete_map = json.loads(self.config["FIG_INTENSIVE_CARE_VENTILATED"]["color_discrete_map"])
        title = self.config["FIG_INTENSIVE_CARE_VENTILATED"]["title"]
        xaxis_title = self.config["FIG_INTENSIVE_CARE_VENTILATED"]["xaxis_title"]
        yaxis_title = self.config["FIG_INTENSIVE_CARE_VENTILATED"]["yaxis_title"]
        legend = json.loads(self.config["ALL_FIGS"]["legend"])
        font_family = self.config["ALL_FIGS"]["font_family"]
        font_color = self.config["ALL_FIGS"]["font_color"]
        plot_bgcolor = self.config["ALL_FIGS"]["plot_bgcolor"]
        paper_bgcolor = self.config["ALL_FIGS"]["paper_bgcolor"]
        y_subfig = json.loads(self.config["SUBFIG_INTENSIVE_CARE_VENTILATED_PERCENTAGE"]["y"])
        color_discrete_map_subfig = json.loads(
            self.config["SUBFIG_INTENSIVE_CARE_VENTILATED_PERCENTAGE"]["color_discrete_map"])
        yaxis_title_subfig = self.config["SUBFIG_INTENSIVE_CARE_VENTILATED_PERCENTAGE"]["yaxis_title"]
        barmode = self.config["SUBFIG_INTENSIVE_CARE_VENTILATED_PERCENTAGE"]["barmode"]

        intensive_register = intensive_register.reset_index()

        subfig = make_subplots(specs=[[{"secondary_y": True}]])

        fig_intensive_care_ventilated = px.bar(intensive_register,
                                               x=x,
                                               y=y,
                                               color_discrete_map=color_discrete_map)

        fig_intensive_care_ventilated_percentage = px.line(intensive_register,
                                                           x=x,
                                                           y=y_subfig,
                                                           color_discrete_map=color_discrete_map_subfig,
                                                           render_mode=render_mode)

        fig_intensive_care_ventilated_percentage.update_traces(yaxis="y2")

        subfig.add_traces(fig_intensive_care_ventilated.data + fig_intensive_care_ventilated_percentage.data)
        subfig.update_yaxes(title_text=yaxis_title_subfig, secondary_y=True)

        subfig.update_layout(
            title=title,
            barmode=barmode,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            legend=legend,
            font_family=font_family,
            font_color=font_color,
            plot_bgcolor=plot_bgcolor,
            paper_bgcolor=paper_bgcolor)

        return subfig

    def _figure_intensive_beds(self, intensive_register: IntensiveRegisterDataFrame) -> Figure:
        render_mode = self.config["ALL_FIGS"]["render_mode"]
        x = self.config["FIG_INTENSIVE_BEDS"]["x"]
        y = json.loads(self.config["FIG_INTENSIVE_BEDS"]["y"])
        color_discrete_map = json.loads(self.config["FIG_INTENSIVE_BEDS"]["color_discrete_map"])
        title = self.config["FIG_INTENSIVE_BEDS"]["title"]
        xaxis_title = self.config["FIG_INTENSIVE_BEDS"]["xaxis_title"]
        yaxis_title = self.config["FIG_INTENSIVE_BEDS"]["yaxis_title"]
        legend = json.loads(self.config["ALL_FIGS"]["legend"])
        font_family = self.config["ALL_FIGS"]["font_family"]
        font_color = self.config["ALL_FIGS"]["font_color"]
        plot_bgcolor = self.config["ALL_FIGS"]["plot_bgcolor"]
        paper_bgcolor = self.config["ALL_FIGS"]["paper_bgcolor"]
        y_subfig = json.loads(self.config["FIG_INTENSIVE_BEDS_COUNT"]["y"])
        color_discrete_map_subfig = json.loads(self.config["FIG_INTENSIVE_BEDS_COUNT"]["color_discrete_map"])
        barmode = self.config["FIG_INTENSIVE_BEDS_COUNT"]["barmode"]

        intensive_register = intensive_register.reset_index()

        subfig = make_subplots(specs=[[{"secondary_y": True}]])

        fig_intensive_beds = px.bar(intensive_register,
                                    x=x,
                                    y=y,
                                    color_discrete_map=color_discrete_map)

        fig_intensive_beds_count = px.line(intensive_register,
                                           x=x,
                                           y=y_subfig,
                                           color_discrete_map=color_discrete_map_subfig,
                                           render_mode=render_mode)

        # fig_intensive_beds_count.update_traces(yaxis="y1")

        subfig.add_traces(fig_intensive_beds.data + fig_intensive_beds_count.data)
        subfig.update_yaxes(secondary_y=False)

        subfig.update_layout(title=title,
                             barmode=barmode,
                             xaxis_title=xaxis_title,
                             yaxis_title=yaxis_title,
                             legend=legend,
                             font_family=font_family,
                             font_color=font_color,
                             plot_bgcolor=plot_bgcolor,
                             paper_bgcolor=paper_bgcolor)

        return subfig

    def _figure_intensive_beds_prop(self, intensive_register: IntensiveRegisterDataFrame) -> Figure:
        render_mode = self.config["ALL_FIGS"]["render_mode"]
        x = self.config["FIG_INTENSIVE_BEDS_PROP"]["x"]
        y = json.loads(self.config["FIG_INTENSIVE_BEDS_PROP"]["y"])
        color_discrete_map = json.loads(self.config["FIG_INTENSIVE_BEDS_PROP"]["color_discrete_map"])
        title = self.config["FIG_INTENSIVE_BEDS_PROP"]["title"]
        xaxis_title = self.config["FIG_INTENSIVE_BEDS_PROP"]["xaxis_title"]
        yaxis_title = self.config["FIG_INTENSIVE_BEDS_PROP"]["yaxis_title"]
        yaxis = json.loads(self.config["FIG_INTENSIVE_BEDS_PROP"]["yaxis"])
        legend = json.loads(self.config["ALL_FIGS"]["legend"])
        font_family = self.config["ALL_FIGS"]["font_family"]
        font_color = self.config["ALL_FIGS"]["font_color"]
        plot_bgcolor = self.config["ALL_FIGS"]["plot_bgcolor"]
        paper_bgcolor = self.config["ALL_FIGS"]["paper_bgcolor"]

        intensive_register = intensive_register.reset_index()

        fig_intensive_beds_prop = px.line(intensive_register,
                                          x=x,
                                          y=y,
                                          color_discrete_map=color_discrete_map,
                                          render_mode=render_mode)

        fig_intensive_beds_prop.update_layout(title=title,
                                              xaxis_title=xaxis_title,
                                              yaxis_title=yaxis_title,
                                              yaxis=yaxis,
                                              legend=legend,
                                              font_family=font_family,
                                              font_color=font_color,
                                              plot_bgcolor=plot_bgcolor,
                                              paper_bgcolor=paper_bgcolor)

        return fig_intensive_beds_prop

    def _figure_proportions_cases_hospitalizations_deaths(self, clinical_aspects: ClinicalAspectsDataFrame) -> Figure:
        render_mode = self.config["ALL_FIGS"]["render_mode"]
        x = self.config["FIG_PROPORTIONS_CASES_HOSPITALIZATIONS_DEATHS"]["x"]
        y = json.loads(self.config["FIG_PROPORTIONS_CASES_HOSPITALIZATIONS_DEATHS"]["y"])
        color_discrete_map = json.loads(
            self.config["FIG_PROPORTIONS_CASES_HOSPITALIZATIONS_DEATHS"]["color_discrete_map"])
        title = self.config["FIG_PROPORTIONS_CASES_HOSPITALIZATIONS_DEATHS"]["title"]
        xaxis_title = self.config["FIG_PROPORTIONS_CASES_HOSPITALIZATIONS_DEATHS"]["xaxis_title"]
        yaxis_title = self.config["FIG_PROPORTIONS_CASES_HOSPITALIZATIONS_DEATHS"]["yaxis_title"]
        # yaxis = json.loads(self.config["FIG_PROPORTIONS_CASES_HOSPITALIZATIONS_DEATHS"]["yaxis"])
        legend = json.loads(self.config["ALL_FIGS"]["legend"])
        font_family = self.config["ALL_FIGS"]["font_family"]
        font_color = self.config["ALL_FIGS"]["font_color"]
        plot_bgcolor = self.config["ALL_FIGS"]["plot_bgcolor"]
        paper_bgcolor = self.config["ALL_FIGS"]["paper_bgcolor"]

        clinical_aspects = clinical_aspects.reset_index()

        proportions_cases_hospitalizations_deaths = px.line(clinical_aspects,
                                                            x=x,
                                                            y=y,
                                                            color_discrete_map=color_discrete_map,
                                                            render_mode=render_mode)

        proportions_cases_hospitalizations_deaths.update_layout(title=title,
                                                                xaxis_title=xaxis_title,
                                                                yaxis_title=yaxis_title,
                                                                # yaxis=yaxis,
                                                                legend=legend,
                                                                font_family=font_family,
                                                                font_color=font_color,
                                                                plot_bgcolor=plot_bgcolor,
                                                                paper_bgcolor=paper_bgcolor)

        return proportions_cases_hospitalizations_deaths

    def _figure_new_deaths_by_refdate(self,
                                      corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                                      nowcast_rki: NowcastRKIDataFrame) -> Figure:

        render_mode = self.config["ALL_FIGS"]["render_mode"]
        x = self.config["FIG_NEW_DEATHS_PER_REFDATE"]["x"]
        y = json.loads(self.config["FIG_NEW_DEATHS_PER_REFDATE"]["y"])
        color_discrete_map = json.loads(self.config["FIG_NEW_DEATHS_PER_REFDATE"]["color_discrete_map"])
        title = self.config["FIG_NEW_DEATHS_PER_REFDATE"]["title"]
        xaxis_title = self.config["FIG_NEW_DEATHS_PER_REFDATE"]["xaxis_title"]
        yaxis_title = self.config["FIG_NEW_DEATHS_PER_REFDATE"]["yaxis_title"]
        legend = json.loads(self.config["ALL_FIGS"]["legend"])
        font_family = self.config["ALL_FIGS"]["font_family"]
        font_color = self.config["ALL_FIGS"]["font_color"]
        plot_bgcolor = self.config["ALL_FIGS"]["plot_bgcolor"]
        paper_bgcolor = self.config["ALL_FIGS"]["paper_bgcolor"]

        corona_cases_and_deaths_with_nowcast = pd.concat([corona_cases_and_deaths, nowcast_rki], axis=1)
        df_filtered = corona_cases_and_deaths_with_nowcast.loc[:, y].dropna(how='all', axis=0)
        df_filtered = df_filtered.reset_index()

        fig_new_deaths_per_refdate = px.bar(df_filtered,
                                            x=x,
                                            y=y,
                                            color_discrete_map=color_discrete_map)

        fig_new_deaths_per_refdate.update_layout(title=title,
                                                 barmode='stack',
                                                 xaxis_title=xaxis_title,
                                                 yaxis_title=yaxis_title,
                                                 legend=legend,
                                                 font_family=font_family,
                                                 font_color=font_color,
                                                 plot_bgcolor=plot_bgcolor,
                                                 paper_bgcolor=paper_bgcolor)

        return fig_new_deaths_per_refdate

    def _figure_total_cases_by_refdate(self,
                                       corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                                       nowcast_rki: NowcastRKIDataFrame) -> Figure:

        render_mode = self.config["ALL_FIGS"]["render_mode"]
        x = self.config["FIG_TOTAL_CASES_PER_REFDATE"]["x"]
        y = json.loads(self.config["FIG_TOTAL_CASES_PER_REFDATE"]["y"])
        color_discrete_map = json.loads(self.config["FIG_TOTAL_CASES_PER_REFDATE"]["color_discrete_map"])
        title = self.config["FIG_TOTAL_CASES_PER_REFDATE"]["title"]
        xaxis_title = self.config["FIG_TOTAL_CASES_PER_REFDATE"]["xaxis_title"]
        yaxis_title = self.config["FIG_TOTAL_CASES_PER_REFDATE"]["yaxis_title"]
        legend = json.loads(self.config["ALL_FIGS"]["legend"])
        font_family = self.config["ALL_FIGS"]["font_family"]
        font_color = self.config["ALL_FIGS"]["font_color"]
        plot_bgcolor = self.config["ALL_FIGS"]["plot_bgcolor"]
        paper_bgcolor = self.config["ALL_FIGS"]["paper_bgcolor"]

        corona_cases_and_deaths_with_nowcast = pd.concat([corona_cases_and_deaths, nowcast_rki], axis=1).reset_index()

        fig_total_cases_per_refdate = px.bar(corona_cases_and_deaths_with_nowcast,
                                             x=x,
                                             y=y,
                                             color_discrete_map=color_discrete_map)

        fig_total_cases_per_refdate.update_layout(title=title,
                                                  barmode='stack',
                                                  xaxis_title=xaxis_title,
                                                  yaxis_title=yaxis_title,
                                                  legend=legend,
                                                  font_family=font_family,
                                                  font_color=font_color,
                                                  plot_bgcolor=plot_bgcolor,
                                                  paper_bgcolor=paper_bgcolor)

        return fig_total_cases_per_refdate

    def _figure_new_cases_by_reporting_date(self,
                                            corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                                            nowcast_rki: NowcastRKIDataFrame) -> Figure:

        render_mode = self.config["ALL_FIGS"]["render_mode"]
        x = self.config["FIG_NEW_CASES_BY_REPORTING_DATE"]["x"]
        y = json.loads(self.config["FIG_NEW_CASES_BY_REPORTING_DATE"]["y"])
        color_discrete_map = json.loads(self.config["FIG_NEW_CASES_BY_REPORTING_DATE"]["color_discrete_map"])
        title = self.config["FIG_NEW_CASES_BY_REPORTING_DATE"]["title"]
        xaxis_title = self.config["FIG_NEW_CASES_BY_REPORTING_DATE"]["xaxis_title"]
        yaxis_title = self.config["FIG_NEW_CASES_BY_REPORTING_DATE"]["yaxis_title"]
        legend = json.loads(self.config["ALL_FIGS"]["legend"])
        font_family = self.config["ALL_FIGS"]["font_family"]
        font_color = self.config["ALL_FIGS"]["font_color"]
        plot_bgcolor = self.config["ALL_FIGS"]["plot_bgcolor"]
        paper_bgcolor = self.config["ALL_FIGS"]["paper_bgcolor"]

        corona_cases_and_deaths_with_nowcast = pd.concat([corona_cases_and_deaths, nowcast_rki], axis=1)
        df_filtered = corona_cases_and_deaths_with_nowcast.loc[:, y].dropna(how='all', axis=0)
        df_filtered = df_filtered.reset_index()

        fig_new_deaths_per_refdate = px.bar(df_filtered,
                                            x=x,
                                            y=y,
                                            color_discrete_map=color_discrete_map)

        fig_new_deaths_per_refdate.update_layout(title=title,
                                                 barmode='stack',
                                                 xaxis_title=xaxis_title,
                                                 yaxis_title=yaxis_title,
                                                 legend=legend,
                                                 font_family=font_family,
                                                 font_color=font_color,
                                                 plot_bgcolor=plot_bgcolor,
                                                 paper_bgcolor=paper_bgcolor)

        return fig_new_deaths_per_refdate

    def _figure_total_deaths_by_refdate(self,
                                        corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                                        nowcast_rki: NowcastRKIDataFrame) -> Figure:

        x = self.config["FIG_TOTAL_DEATHS_PER_REFDATE"]["x"]
        y = json.loads(self.config["FIG_TOTAL_DEATHS_PER_REFDATE"]["y"])
        color_discrete_map = json.loads(self.config["FIG_TOTAL_DEATHS_PER_REFDATE"]["color_discrete_map"])
        title = self.config["FIG_TOTAL_DEATHS_PER_REFDATE"]["title"]
        xaxis_title = self.config["FIG_TOTAL_DEATHS_PER_REFDATE"]["xaxis_title"]
        yaxis_title = self.config["FIG_TOTAL_DEATHS_PER_REFDATE"]["yaxis_title"]
        legend = json.loads(self.config["ALL_FIGS"]["legend"])
        font_family = self.config["ALL_FIGS"]["font_family"]
        font_color = self.config["ALL_FIGS"]["font_color"]
        plot_bgcolor = self.config["ALL_FIGS"]["plot_bgcolor"]
        paper_bgcolor = self.config["ALL_FIGS"]["paper_bgcolor"]

        corona_cases_and_deaths_with_nowcast = pd.concat([corona_cases_and_deaths, nowcast_rki], axis=1).reset_index()

        fig_total_deaths_per_refdate = px.bar(corona_cases_and_deaths_with_nowcast,
                                              x=x,
                                              y=y,
                                              color_discrete_map=color_discrete_map)

        fig_total_deaths_per_refdate.update_layout(title=title,
                                                   barmode='stack',
                                                   xaxis_title=xaxis_title,
                                                   yaxis_title=yaxis_title,
                                                   legend=legend,
                                                   font_family=font_family,
                                                   font_color=font_color,
                                                   plot_bgcolor=plot_bgcolor,
                                                   paper_bgcolor=paper_bgcolor)

        return fig_total_deaths_per_refdate

    def _plot_objects(self,
                      corona_cases_and_deaths: CoronaCasesAndDeathsDataFrame,
                      nowcast_rki: NowcastRKIDataFrame,
                      number_pcr_tests: NumberPCRTestsDataFrame,
                      intensive_register: IntensiveRegisterDataFrame,
                      clinical_aspects: ClinicalAspectsDataFrame,
                      age_distribution: AgeDistributionDataFrame) -> FiguresDict:
        """
        Function that creates all relevant plot objects (visualizations).
        """

        # BRING ALL PLOTS INTO ONE DICTIONAIRY OBJECT
        figures: Layout.FiguresDict = \
            {"fig_cases_mean_3": self._figure_cases_mean_3(corona_cases_and_deaths, nowcast_rki),
             "fig_deaths_mean_3": self._figure_deaths_mean_3(corona_cases_and_deaths, nowcast_rki),
             "fig_r0": self._figure_r0(corona_cases_and_deaths, nowcast_rki),
             "fig_7d_incidences": self._figure_7d_incidences(corona_cases_and_deaths, nowcast_rki),
             "fig_pcr_tests": self._figure_pcr_tests(number_pcr_tests),
             "fig_distribution_of_inhabitants_and_deaths":
                 self._figure_distribution_of_inhabitants_and_deaths(age_distribution),
             "fig_distribution_of_cases_and_deaths_per_n_inhabitants":
                 self._figure_distribution_of_cases_and_deaths_per_n_inhabitants(age_distribution),
             "fig_intensive_new": self._figure_intensive_new(intensive_register),
             "fig_intensive_daily_change": self._figure_intensive_daily_change(intensive_register),
             "fig_intensive_reporting_areas": self._figure_intensive_reporting_areas(intensive_register),
             "fig_intensive_care_ventilated": self._figure_intensive_care_ventilated(intensive_register),
             "fig_intensive_beds": self._figure_intensive_beds(intensive_register),
             "fig_intensive_beds_prop": self._figure_intensive_beds_prop(intensive_register),
             "fig_proportions_cases_hospitalizations_deaths":
                 self._figure_proportions_cases_hospitalizations_deaths(clinical_aspects),
             "fig_new_deaths_per_refdate": self._figure_new_deaths_by_refdate(corona_cases_and_deaths, nowcast_rki),
             "fig_new_cases_by_reporting_date":
                 self._figure_new_cases_by_reporting_date(corona_cases_and_deaths, nowcast_rki),
             "fig_total_cases_by_refdate": self._figure_total_cases_by_refdate(corona_cases_and_deaths, nowcast_rki),
             "fig_total_deaths_by_refdate": self._figure_total_deaths_by_refdate(corona_cases_and_deaths, nowcast_rki)
             }

        return figures
