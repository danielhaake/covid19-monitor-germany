import time

import logging
import traceback

from data_pandas_subclasses.date_index_classes.CoronaCasesAndDeaths import CoronaCasesAndDeathsDataFrame
from data_pandas_subclasses.date_index_classes.NowcastRKI import NowcastRKIDataFrame
from data_pandas_subclasses.date_index_classes.IntensiveRegister import IntensiveRegisterDataFrame
from data_pandas_subclasses.week_index_classes.NumberPCRTests import NumberPCRTestsDataFrame
from data_pandas_subclasses.week_index_classes.ClinicalAspects import ClinicalAspectsDataFrame
from data_pandas_subclasses.AgeDistribution import AgeDistributionDataFrame

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':

    logging.info("START COMPLETE UPDATE PROCESS")
    start_time = time.time()
    try:
        CoronaCasesAndDeathsDataFrame.update_csv_with_data_from_rki_api()
    except Exception:
        traceback.print_exc()
    try:
        NowcastRKIDataFrame.update_with_new_data_from_rki()
    except Exception:
        traceback.print_exc()
    try:
        IntensiveRegisterDataFrame.update_csv_with_intensive_register_data()
    except Exception:
        traceback.print_exc()
    try:
        ClinicalAspectsDataFrame.update_csv_with_new_data_from_rki()
    except Exception:
        traceback.print_exc()
    try:
        AgeDistributionDataFrame.get_age_distribution_of_cases_and_deaths()
    except Exception:
        traceback.print_exc()
    try:
        NumberPCRTestsDataFrame.update_csv_with_new_data_from_rki()
    except Exception:
        traceback.print_exc()
    end_time = time.time()
    logging.info(f"FINISHED COMPLETE UPDATE PROCESS IN {end_time - start_time} SECONDS")
