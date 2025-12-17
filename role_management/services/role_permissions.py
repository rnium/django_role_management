from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from role_management.models import Module
from role_management.utils import has_permission
from role_management.enums import Actions
from django.conf import settings


def sync_module_permissions(group: Group, module: Module, permissions: int):
    for contenttype in module.content_types.all():
        modelname = contenttype.model
        for action in Actions:
            if not isinstance(action.name, str):
                continue
            codename_templates = settings.PERMS_CODENAMES_MAP.get(action.name, [])
            apply_model_permission_to_group(
                contenttype,
                group,
                [c % modelname for c in codename_templates],
                add = has_permission(permissions, action.value)
            )


def apply_model_permission_to_group(ctype: ContentType, group: Group, codenames: list[str], add: bool):
    for codename in codenames:
        permission = Permission.objects.get(
            content_type=ctype,
            codename=codename
        )
        if add:
            group.permissions.add(permission)
        else:
            group.permissions.remove(permission)