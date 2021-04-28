# subclassing of Pandas
# see: https://pandas.pydata.org/pandas-docs/stable/development/extending.html#override-constructor-properties
import logging

from dotenv import load_dotenv

from api.RKIAPI import RKIAPI
from data_pandas_subclasses.week_index_classes.CoronaBaseWeekIndex import CoronaBaseWeekIndexDataFrame, CoronaBaseWeekIndexSeries

load_dotenv()
logging.basicConfig(level=logging.INFO)


class CasesPerOutbreakSeries(CoronaBaseWeekIndexSeries):
    @property
    def _constructor(self):
        return CasesPerOutbreakSeries

    @property
    def _constructor_expanddim(self):
        return CasesPerOutbreakDataFrame


class CasesPerOutbreakDataFrame(CoronaBaseWeekIndexDataFrame):

    _filename = "cases_attributed_to_an_outbreak.csv"
    api = RKIAPI()

    @property
    def _constructor(self):
        return CasesPerOutbreakDataFrame

    @property
    def _constructor_sliced(self):
        return CasesPerOutbreakSeries

    @staticmethod
    def from_csv(filename: str=None,
                 s3_bucket: str=None,
                 folder_path: str=None,
                 class_name: str=None) -> 'CasesPerOutbreakDataFrame':

        if filename is None:
            filename = CasesPerOutbreakDataFrame._filename
        if class_name is None:
            class_name = CasesPerOutbreakDataFrame.__name__
        df = CoronaBaseWeekIndexDataFrame.from_csv(filename, s3_bucket, folder_path, class_name)

        return CasesPerOutbreakDataFrame(df)

    @staticmethod
    def update_csv_with_new_data_from_rki(to_csv: bool = True,
                                          s3_bucket: str = None,
                                          folder_path: str = None):

        logging.info("START UPDATE PROCESS FOR CASES PER OUTBREAK")
        logging.info("start downloading file from RKI")

        cases_attributed_to_an_outbreak = CasesPerOutbreakDataFrame(CasesPerOutbreakDataFrame.api.
                                                     cases_attributed_to_an_outbreak_per_week())
        if to_csv:
            cases_attributed_to_an_outbreak.save_as_csv(s3_bucket=s3_bucket, folder_path=folder_path)

        logging.info("FINISHED UPDATE PROCESS FOR CASES PER OUTBREAK")
        return cases_attributed_to_an_outbreak
