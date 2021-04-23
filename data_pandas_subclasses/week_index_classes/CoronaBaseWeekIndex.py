from data_pandas_subclasses.CoronaBase import CoronaBaseSeries, CoronaBaseDataFrame


class CoronaBaseWeekIndexSeries(CoronaBaseSeries):
    @property
    def _constructor(self):
        return CoronaBaseWeekIndexSeries

    @property
    def _constructor_expanddim(self):
        return CoronaBaseWeekIndexDataFrame


class CoronaBaseWeekIndexDataFrame(CoronaBaseDataFrame):

    @property
    def _constructor(self):
        return CoronaBaseWeekIndexDataFrame

    @property
    def _constructor_sliced(self):
        return CoronaBaseWeekIndexSeries

    @staticmethod
    def from_csv(filename: str,
                 s3_bucket: str=None,
                 folder_path: str=None,
                 class_name: str=None) -> 'CoronaBaseWeekIndexDataFrame':
        if class_name is None:
            class_name = 'CoronaBaseWeekIndexDataFrame'
        df = CoronaBaseDataFrame.from_csv(filename, s3_bucket, folder_path, class_name)

        return CoronaBaseWeekIndexDataFrame(df.set_index("calendar week"))
