from typing import TypedDict


class DailyFiguresDict(TypedDict):
    cases_cumulative: int
    cases_last_365_days: int
    last_cases_reported_by_rki: int
    last_mean_cases: int
    last_mean_cases_change_since_day_before: int
    cases_last_7_days: int
    cases_last_7_days_change_since_day_before: int
    cases_last_7_days_by_reporting_date: int
    cases_last_7_days_by_reporting_date_change_since_day_before: int
    deaths_cumulative: int
    deaths_last_365_days: int
    last_deaths_reported_by_rki: int
    last_mean_deaths: int
    last_mean_deaths_change_since_day_before: int
    deaths_last_7_days: int
    deaths_last_7_days_change_since_day_before: int
    last_r_value: float
    last_r_value_change_since_day_before: float
    last_r_value_by_nowcast_rki: float
    last_r_value_by_nowcast_rki_change_since_day_before: float
    last_r_value_by_new_admissions_to_intensive_care: float
    last_r_value_by_new_admissions_to_intensive_care_change_since_day_before: float