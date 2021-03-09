# subclassing of Pandas
# see: https://pandas.pydata.org/pandas-docs/stable/development/extending.html#override-constructor-properties
import boto3
import logging
import os

from dotenv import load_dotenv
from io import StringIO

import pandas as pd

load_dotenv()
logging.basicConfig(level=logging.INFO)


class CoronaBaseSeries(pd.Series):
    @property
    def _constructor(self):
        return CoronaBaseSeries

    @property
    def _constructor_expanddim(self):
        return CoronaBaseDataFrame


class CoronaBaseDataFrame(pd.DataFrame):

    _folder_path = "data/"

    @property
    def _constructor(self):
        return CoronaBaseDataFrame

    @property
    def _constructor_sliced(self):
        return CoronaBaseSeries

    def _set_path(self, path: str):
        self._path = path

    def _set_folder_path(self, folder_path: str):
        self._folder_path = folder_path

    @staticmethod
    def from_csv(filename: str,
                 s3_bucket: str=None,
                 folder_path: str=None,
                 class_name: str=None) -> 'CoronaBaseDataFrame':

        if (s3_bucket is not None) & (folder_path is not None):
            logging.info("Both arguments for s3_bucket and for path are set. In this case s3_bucket is used.")

        if class_name is None:
            class_name = CoronaBaseDataFrame.__name__

        if (os.environ.get('S3_BUCKET') is not None) | (s3_bucket is not None):
            df = CoronaBaseDataFrame.load_csv_from_s3(filename=filename, s3_bucket=s3_bucket, class_name=class_name)
        else:
            df = CoronaBaseDataFrame.load_csv_from_path(filename=filename, folder_path=folder_path, class_name=class_name)

        if folder_path is not None:
            df._set_path(folder_path)

        return df

    @staticmethod
    def load_csv_from_s3(filename: str, s3_bucket: str, class_name: str=None) -> 'CoronaBaseDataFrame':
        if s3_bucket is None:
            s3_bucket = os.environ.get('S3_BUCKET')

        s3 = boto3.client('s3')
        logging.info(f"...start loading {class_name} with filename {filename} from S3 Bucket {s3_bucket}")
        read_file = s3.get_object(Bucket=s3_bucket, Key=filename)
        df = CoronaBaseDataFrame(pd.read_csv(read_file['Body']))
        logging.info(f"...{class_name} with filename {filename} successfully loaded from S3 Bucket {s3_bucket}")

        return df

    @staticmethod
    def load_csv_from_path(filename: str, folder_path: str, class_name: str=None) -> 'CoronaBaseDataFrame':
        if folder_path is None:
            if os.environ.get('FOLDER_PATH') is not None:
                folder_path = os.environ.get('FOLDER_PATH')
            else:
                folder_path = CoronaBaseDataFrame._folder_path
        path = folder_path + filename

        logging.info(f"start loading {class_name} from {path}")
        df = CoronaBaseDataFrame(pd.read_csv(path))
        logging.info(f"{class_name} successfully loaded from {path}")

        if os.environ.get('FOLDER_PATH') is not None:
            df._set_folder_path(os.environ.get('FOLDER_PATH'))

        return df

    def save_as_csv(self, filename: str=None, s3_bucket: str=None, folder_path: str=None):
        if (s3_bucket is not None) & (folder_path is not None):
            logging.info("Both arguments for s3_bucket and for path in method save_as_csv() are set. "
                         "In this case s3_bucket is used.")

        if (os.environ.get('S3_BUCKET') is not None) | (s3_bucket is not None):
            self._save_as_csv_to_s3(filename, s3_bucket)

        elif (os.environ.get('FOLDER_PATH') is not None) | (folder_path is not None):
            self._save_as_csv_to_path(filename, folder_path)

        else:
            raise ValueError("Neither argument s3_bucket nor argument folder_path has been set. "
                             "However, either argument s3_bucket or argument folder_path must be set.")

    def _save_as_csv_to_s3(self, filename: str=None, s3_bucket: str=None):
        if filename is None:
            filename = self._filename

        if s3_bucket is None:
            s3_bucket = os.environ.get('S3_BUCKET')

        csv_buffer = StringIO()
        self.to_csv(csv_buffer)  # pandas to_save()-method
        s3 = boto3.client('s3')

        logging.info(f"try writing {self.__class__.__name__} with filename {self._filename} "
                     f"to S3 Bucket {s3_bucket}")
        s3.put_object(Bucket=s3_bucket, Key=filename, Body=csv_buffer.getvalue())
        logging.info(f"{self.__class__.__name__} with filename {self._filename} has been "
                     f"written to S3 Bucket {s3_bucket}")

    def _save_as_csv_to_path(self, filename: str=None, folder_path: str=None):
        if filename is None:
            filename = self._filename

        if folder_path is None:
            if os.environ.get('FOLDER_PATH') is not None:
                folder_path = os.environ.get('FOLDER_PATH')
            else:
                folder_path = self._folder_path

        path = folder_path + filename
        self._set_folder_path(folder_path)
        self._set_path(path)

        logging.info(f"try writing {self.__class__.__name__} to {path}")
        self.to_csv(path)  # pandas to_csv()-method
        logging.info(f"{self.__class__.__name__} has been written to {path}")
