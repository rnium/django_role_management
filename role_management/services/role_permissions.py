from django.contrib.auth.models import Group as Role
from rest_framework import serializers
from role_management.models import Module, ModuleAccess


def sync_module_permissions(group, module, permissions):
    pass