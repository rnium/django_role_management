from role_management.models import Module, ModuleAccess
from django.shortcuts import get_object_or_404
from .role_permissions import sync_module_permissions

def save_module_access(role, access: dict[str, int] | None):
    if not isinstance(access, dict):
        return
    for module_name, permissions in access.items():
        module = get_object_or_404(Module, name=module_name)
        mod_access = ModuleAccess.objects.filter(
            module = module,
            group=role
        )
        if not mod_access:
            mod_access = ModuleAccess.objects.create(
                module=module,
                group=role,
                permissions=permissions
            )
        else:
            if permissions == 0:
                mod_access.delete()
                return
            mod_access.update(permissions=permissions)
        sync_module_permissions(role, module, permissions)