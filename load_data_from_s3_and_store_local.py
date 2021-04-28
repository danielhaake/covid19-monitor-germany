import time

from data_pandas_subclasses.date_index_classes.CoronaCasesAndDeaths import *
from data_pandas_subclasses.date_index_classes.NowcastRKI import *
from data_pandas_subclasses.date_index_classes.IntensiveRegister import *
from data_pandas_subclasses.week_index_classes.NumberPCRTests import *
from data_pandas_subclasses.week_index_classes.ClinicalAspects import *
from data_pandas_subclasses.week_index_classes.CasesPerOutbreak import *
from data_pandas_subclasses.AgeDistribution import *


def process_corona_cases_and_deaths():
    corona_cases_and_deaths = CoronaCasesAndDeathsDataFrame.from_csv()
    corona_cases_and_deaths.to_csv("data/corona_cases_and_deaths.csv")


def process_nowcast():
    nowcast = NowcastRKIDataFrame.from_csv()
    nowcast.to_csv("data/nowcast_rki.csv")


def process_intensive_register():
    intensive_register = IntensiveRegisterDataFrame.from_csv()
    intensive_register.to_csv("data/intensive_register_total.csv")


def process_number_pcr_tests():
    pcr_tests = NumberPCRTestsDataFrame.from_csv()
    pcr_tests.to_csv("data/number_of_tests_germany.csv")


def process_clinical_aspects():
    clinical_aspects = ClinicalAspectsDataFrame.from_csv()
    clinical_aspects.to_csv("data/clinical_aspects.csv")


def process_cases_per_outbreak():
    cases_per_outbreak = CasesPerOutbreakDataFrame.from_csv()
    cases_per_outbreak.to_csv("data/cases_attributed_to_an_outbreak.csv")


def process_age_distribution():
    age_distribution = AgeDistributionDataFrame.from_csv()
    age_distribution.to_csv("data/distribution_of_inhabitants_and_cases_and_deaths.csv")


def load_dataframes_from_s3_and_store_local():
    process_corona_cases_and_deaths()
    process_nowcast()
    process_intensive_register()
    process_number_pcr_tests()
    process_clinical_aspects()
    process_cases_per_outbreak()
    process_age_distribution()


if __name__ == '__main__':

    logging.info("START LOADING DATAFRAMES AND STORE LOCAL")
    start_time = time.time()
    load_dataframes_from_s3_and_store_local()
    end_time = time.time()
    logging.info(f"FINISHED LOADING DATAFRAMES AND STORE LOCAL IN {end_time - start_time} SECONDS")

