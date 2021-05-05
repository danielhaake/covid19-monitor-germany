# subclassing of Pandas
# see: https://pandas.pydata.org/pandas-docs/stable/development/extending.html#override-constructor-properties
import logging

from dotenv import load_dotenv

from api.RKIAPI import RKIAPI
from data_pandas_subclasses.week_index_classes.CoronaBaseWeekIndex import CoronaBaseWeekIndexDataFrame, CoronaBaseWeekIndexSeries

load_dotenv()
logging.basicConfig(level=logging.INFO)


class DeathsByWeekOfDeathAndAgeGroupSeries(CoronaBaseWeekIndexSeries):
    @property
    def _constructor(self):
        return DeathsByWeekOfDeathAndAgeGroupSeries

    @property
    def _constructor_expanddim(self):
        return DeathsByWeekOfDeathAndAgeGroupDataFrame


class DeathsByWeekOfDeathAndAgeGroupDataFrame(CoronaBaseWeekIndexDataFrame):

    _filename = "deaths_by_week_of_death_and_age_group.csv"
    api = RKIAPI()

    @property
    def _constructor(self):
        return DeathsByWeekOfDeathAndAgeGroupDataFrame

    @property
    def _constructor_sliced(self):
        return DeathsByWeekOfDeathAndAgeGroupSeries

    @staticmethod
    def from_csv(filename: str=None,
                 s3_bucket: str=None,
                 folder_path: str=None,
                 class_name: str=None) -> 'DeathsByWeekOfDeathAndAgeGroupDataFrame':

        if filename is None:
            filename = DeathsByWeekOfDeathAndAgeGroupDataFrame._filename
        if class_name is None:
            class_name = DeathsByWeekOfDeathAndAgeGroupDataFrame.__name__
        df = CoronaBaseWeekIndexDataFrame.from_csv(filename, s3_bucket, folder_path, class_name)

        return DeathsByWeekOfDeathAndAgeGroupDataFrame(df)

    @staticmethod
    def update_csv_with_new_data_from_rki(to_csv: bool = True,
                                          s3_bucket: str = None,
                                          folder_path: str = None):

        logging.info("START UPDATE PROCESS FOR DEATHS BY WEEK OF DEATH AND AGE GROUP")
        logging.info("start downloading file from RKI")

        cases_attributed_to_an_outbreak = DeathsByWeekOfDeathAndAgeGroupDataFrame(
            DeathsByWeekOfDeathAndAgeGroupDataFrame.api.deaths_by_week_of_death_and_age_group())
        if to_csv:
            cases_attributed_to_an_outbreak.save_as_csv(s3_bucket=s3_bucket, folder_path=folder_path)

        logging.info("FINISHED UPDATE PROCESS FOR DEATHS BY WEEK OF DEATH AND AGE GROUP")
        return cases_attributed_to_an_outbreak
