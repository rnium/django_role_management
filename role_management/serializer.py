from django.db import transaction
from django.contrib.auth.models import Group as Role
from rest_framework import serializers
from .models import Module, ModuleAccess
from .services import module_access

class PermissionField(serializers.Field):
    MODULE_NAMES = [mod.name for mod in Module.objects.all()]
    ACTION_MAP = {
        action.name: {
            'value': action.value,
            'shift': action.value.bit_length() - 1
        }
        for action in ModuleAccess.Actions
    }
    
    def __init__(self, *args, **kwargs):
        error_messages: dict = kwargs.pop('error_messages', {})
        error_messages.update({
            'invalid_format': "Format of the data is not valid",
            'unknown_action': "Unknown action specified in data",
            'module_insufficient_perms': "Permission is not specified for all actions of a module",
            'invalid_action_permission': "Action permission needs to be boolean or number",
            'module_unavailable': "Module Not Available"
        })
        return super().__init__(error_messages=error_messages, **kwargs)
                 
    def to_representation(self, value):
        ret = {}
        for mod_access in value.all():
            mod_perm_data = {
                action: mod_access.has_permission(prop["value"])
                for action, prop in self.ACTION_MAP.items()
            }
            ret[mod_access.module.name] = mod_perm_data
        return ret

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            self.fail('invalid_format')
        val = {}
        for module, access in data.items():
            if not (isinstance(access, dict) and isinstance(module, str)):
                self.fail('invalid_format')
            if module not in self.MODULE_NAMES:
                self.fail('module_unavailable')
            if len(access) != len(self.ACTION_MAP):
                self.fail('module_insufficient_perms')
            permissions = 0
            for action, perm in access.items():
                if action not in self.ACTION_MAP:
                    self.fail('unknown_action')
                    continue
                try:
                    perm = int(perm)
                except Exception:
                    self.fail('invalid_action_permission')
                    continue
                permissions ^= (perm << self.ACTION_MAP[action]["shift"])
            val[module] = permissions
        return val


class RoleSerializer(serializers.ModelSerializer):
    access = PermissionField()

    class Meta:
        model = Role
        fields = ['id', 'name', 'access']
    
    @transaction.atomic
    def create(self, validated_data):
        access = validated_data.pop('access', None)
        role = super().create(validated_data)
        module_access.save_module_access(role, access)
        return role
    
    @transaction.atomic
    def update(self, instance, validated_data):
        access = validated_data.pop('access', None)
        res = super().update(instance, validated_data)            
        module_access.save_module_access(instance, access)
        return res
    
    
