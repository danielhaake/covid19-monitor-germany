import time

import logging
import traceback

from data_pandas_subclasses.date_index_classes.CoronaCasesAndDeaths import CoronaCasesAndDeathsDataFrame
from data_pandas_subclasses.date_index_classes.NowcastRKI import NowcastRKIDataFrame
from data_pandas_subclasses.date_index_classes.IntensiveRegister import IntensiveRegisterDataFrame
from data_pandas_subclasses.week_index_classes.CasesPerOutbreak import CasesPerOutbreakDataFrame
from data_pandas_subclasses.week_index_classes.DeathsByWeekOfDeathAndAgeGroup import DeathsByWeekOfDeathAndAgeGroupDataFrame
from data_pandas_subclasses.week_index_classes.NumberPCRTests import NumberPCRTestsDataFrame
from data_pandas_subclasses.week_index_classes.ClinicalAspects import ClinicalAspectsDataFrame
from data_pandas_subclasses.AgeDistribution import AgeDistributionDataFrame

logging.basicConfig(level=logging.INFO)


def update_CoronaCasesAndDeathsDataFrame():
    try:
        CoronaCasesAndDeathsDataFrame.update_csv_with_data_from_rki_api()
    except Exception:
        traceback.print_exc()


def update_NowcastRKIDataFrame():
    try:
        NowcastRKIDataFrame.update_with_new_data_from_rki()
    except Exception:
        traceback.print_exc()


def update_IntensiveRegisterDataFrame():
    try:
        IntensiveRegisterDataFrame.update_csv_with_intensive_register_data()
    except Exception:
        traceback.print_exc()


def update_ClinicalAspectsDataFrame():
    try:
        ClinicalAspectsDataFrame.update_csv_with_new_data_from_rki()
    except Exception:
        traceback.print_exc()


def update_AgeDistributionDataFrame():
    try:
        AgeDistributionDataFrame.get_age_distribution_of_cases_and_deaths()
    except Exception:
        traceback.print_exc()


def update_NumberPCRTestsDataFrame():
    try:
        NumberPCRTestsDataFrame.update_csv_with_new_data_from_rki()
    except Exception:
        traceback.print_exc()


def update_CasesPerOutbreakDataFrame():
    try:
        CasesPerOutbreakDataFrame.update_csv_with_new_data_from_rki()
    except Exception:
        traceback.print_exc()


def update_DeathsByWeekOfDeathAndAgeGroupDataFrame():
    try:
        DeathsByWeekOfDeathAndAgeGroupDataFrame.update_csv_with_new_data_from_rki()
    except Exception:
        traceback.print_exc()


def update_dataframes():
    update_CoronaCasesAndDeathsDataFrame()
    update_NowcastRKIDataFrame()
    update_IntensiveRegisterDataFrame()
    update_ClinicalAspectsDataFrame()
    update_AgeDistributionDataFrame()
    update_NumberPCRTestsDataFrame()
    update_CasesPerOutbreakDataFrame()
    update_DeathsByWeekOfDeathAndAgeGroupDataFrame()


if __name__ == '__main__':

    logging.info("START COMPLETE UPDATE PROCESS")
    start_time = time.time()

    update_dataframes()

    end_time = time.time()
    logging.info(f"FINISHED COMPLETE UPDATE PROCESS IN {end_time - start_time} SECONDS")
