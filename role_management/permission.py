from rest_framework.permissions import DjangoModelPermissions
from django.conf import settings

class ModelPermissionAll(DjangoModelPermissions):
    perms_map = settings.PERMS_MAP
