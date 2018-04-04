import csv
import tempfile
import codecs

import boto3

from django.core.files.storage import default_storage
from django.core.files.base import File
from django.utils.translation import ugettext as _
from django.conf import settings
from model_utils.choices import Choices

from .utils import ExporterHelper


class FileHandler:
    VALID_HANDLERS = Choices(
        ("default_storage", _("default_storage")),
        ("s3", _("s3"))
    )

    def __init__(self, exporter, path_name, target_storage='default_storage'):
        self.path_name = path_name
        self.exporter = exporter
        self.target = self._get_file_storage(target_storage)

    def proccess(self):
        if self.target == self.VALID_HANDLERS.default_storage:
            return self._proccess_default_storage()

    def _get_file_storage(self, storage):
        if storage not in self.VALID_HANDLERS:
            raise KeyError(_("Invalid or unsupported storage"))

        return storage


class BaseHandler:
    def __init__(self, exporter, path_name):
        self.exporter = exporter
        self.path_name = path_name

    def proccess(self):
        raise NotImplementedError(_("Not implemented"))


class DefaultFileHandler(BaseHandler):
    def proccess(self):
        """ Join the file_list (chunked files) into one then saves and return the saved path """
        header = ExporterHelper.get_header(self.exporter.attrs)

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=True, encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=str(';'))
            writer.writerow(header)
            f.flush()

            for chunk in self.exporter.chunks.all():
                with default_storage.open(chunk.file.name) as temp_file:
                    reader = csv.reader(codecs.iterdecode(temp_file, 'utf-8'))
                    for row in reader:
                        writer.writerow(row[0].split(';'))
                        f.flush()

            self.exporter.file.save(self.path_name, File(f))

        return self.exporter


class S3FileHandler(BaseHandler):
    parts = []
    multipart_upload = None
    parts_mapping = []

    def __init__(self, exporter, path_name):
        super().__init__(exporter, path_name)

        self.resource = boto3.resource('s3', region_name=getattr(settings, 'AWS_S3_REGION_NAME'),
                                       endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL'),
                                       aws_access_key_id=getattr(settings, 'AWS_S3_ACCESS_KEY_ID'),
                                       aws_secret_access_key=getattr(settings, 'AWS_S3_SECRET_ACCESS_KEY'),
                                       )

        self.bucket_name = getattr(settings, 'AWS_S3_BUCKET_NAME')

    def collect_parts(self):
        self.parts.append(self._create_header_file())

        for chunk in self.exporter.chunks.all():
            self.parts.append(str(chunk.file))

    def _create_header_file(self):
        header = ExporterHelper.get_header(self.exporter.attrs)
        file_name = f"reports/{self.exporter.uuid}/header.csv"

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=True, encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=str(';'))
            writer.writerow(header)
            f.flush()

            self.exporter.file.save(file_name, File(f))

        return file_name

    def create_bucket(self):
        self.multipart_upload = self.resource.create_multipart_upload(Bucket=self.bucket_name, Key=self.path_name)

    def upload_part(self):
        for i, part in enumerate(self.parts):
            response = self.resource.upload_part_copy(Bucket=self.bucket_name, Key=self.path_name, PartNumber=i,
                                                      UploadId=self.multipart_upload['UploadId'], CopySource=part)

            self.parts_mapping.append({"ETag": response['CopyPartResult']['ETag'][1:-1], "PartNumber": i})

    def complete(self):
        self.resource.complete_multipart_upload(Bucket=self.bucket_name, Key=self.path_name,
                                                UploadId=self.multipart_upload['UploadId'],
                                                MultipartUpload={'Parts': self.parts_mapping})
