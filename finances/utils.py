import os

from django.conf import settings


def get_upload_path(instance, filename):
    return os.path.join(str(instance.user.id), filename)
