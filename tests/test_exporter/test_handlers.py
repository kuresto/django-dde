import os
import glob
import shutil
import pytest

from autofixture import AutoFixture
from tests.generators import CustomDocumentGenerator

from django.core import mail
from django.core.files.storage import default_storage

from tests.fixtures.fake_app.models import FakeModel

from exporter.handlers import S3FileHandler

pytestmark = pytest.mark.django_db


def test_s3_connect(exporter):
    path_name = f'reports/{exporter.uuid}/{exporter.uuid}.csv'

    handler = S3FileHandler(exporter, path_name)
    handler.proccess()