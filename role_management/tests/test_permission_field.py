from django.test import TestCase
from django.contrib.auth.models import Group
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from role_management.models import Module, ModuleAccess
from role_management.serializer import PermissionField
from role_management.enums import Actions


class TestSerializer(serializers.Serializer):
    permissions = PermissionField()


def get_permission_field(serializer):
    """Helper to get the PermissionField from serializer or ListSerializer."""
    if hasattr(serializer, 'child'):
        return serializer.child.fields["permissions"]
    return serializer.fields["permissions"]


class PermissionFieldRepresentationTest(TestCase):
    def setUp(self):
        self.module_users = Module.objects.create(name="Users")
        self.module_billing = Module.objects.create(name="Billing")
        self.group = Group.objects.create(name="Admins")

        # Example permission: READ + UPDATE
        self.access_users = ModuleAccess.objects.create(
            module=self.module_users,
            group=self.group,
            permissions=Actions.read.value | Actions.update.value
        )

        self.access_billing = ModuleAccess.objects.create(
            module=self.module_billing,
            group=self.group,
            permissions=Actions.read.value
        )

        self.serializer = TestSerializer()

    def test_to_representation_single_module(self):
        value = ModuleAccess.objects.filter(module=self.module_users)
        data = get_permission_field(self.serializer).to_representation(value) # type: ignore

        self.assertIn("Users", data)
        
        expected = {
            "read": True,
            "create": False,
            "update": True,
            "delete": False
        }
        
        for action in Actions:
            self.assertEqual(
                data["Users"][action.name],
                expected[str(action.name)]
            )

    def test_to_representation_multiple_modules(self):
        value = ModuleAccess.objects.all()
        data = get_permission_field(self.serializer).to_representation(value) # type: ignore
        self.assertEqual(set(data.keys()), {"Users", "Billing"})

    def test_to_representation_empty_queryset(self):
        value = ModuleAccess.objects.none()
        data = get_permission_field(self.serializer).to_representation(value) # type: ignore
        self.assertEqual(data, {})


class PermissionFieldValidInputTest(TestCase):
    def setUp(self):
        self.module = Module.objects.create(name="Users")
        self.serializer = TestSerializer()

    def test_valid_permissions_numeric(self):
        data = {
            "Users": {
                action.name: 1 for action in Actions
            }
        }

        value = get_permission_field(self.serializer).to_internal_value(data) # type: ignore

        self.assertIn("Users", value)
        self.assertEqual(value["Users"], 0b1111)

    def test_bit_shift_correctness(self):
        data = {
            "Users": {
                Actions.read.name: 1,
                Actions.create.name: 0,
                Actions.update.name: 1,
                Actions.delete.name: 0,
            }
        }

        value = get_permission_field(self.serializer).to_internal_value(data) # type: ignore

        expected = (
            Actions.read.value | Actions.update.value
        )

        self.assertEqual(bin(value["Users"]), bin(expected))

class PermissionFieldFormatErrorTest(TestCase):
    def setUp(self):
        self.serializer = TestSerializer()

    def test_non_dict_input(self):
        with self.assertRaises(ValidationError):
            get_permission_field(self.serializer).to_internal_value([]) # type: ignore

    def test_module_access_not_dict(self):
        data = {"Users": "invalid"}
        with self.assertRaises(ValidationError):
            get_permission_field(self.serializer).to_internal_value(data) # type: ignore

    def test_module_name_not_string(self):
        data = {123: {}}
        with self.assertRaises(ValidationError):
            get_permission_field(self.serializer).to_internal_value(data) # type: ignore

class PermissionFieldModuleErrorsTest(TestCase):
    def setUp(self):
        self.serializer = TestSerializer()

    def test_module_unavailable(self):
        data = {
            "UnknownModule": {
                action.name: 1 for action in Actions
            }
        }

        with self.assertRaises(ValidationError) as ctx:
            get_permission_field(self.serializer).to_internal_value(data) # type: ignore

        self.assertIn("module_unavailable", str(ctx.exception))


class PermissionFieldActionErrorsTest(TestCase):
    def setUp(self):
        self.module = Module.objects.create(name="Users")
        self.serializer = TestSerializer()

    def test_missing_actions(self):
        data = {
            "Users": {
                Actions.read.name: 1
            }
        }

        with self.assertRaises(ValidationError) as ctx:
            get_permission_field(self.serializer).to_internal_value(data)
        
        self.assertIn("module_insufficient_perms", str(ctx.exception))

    def test_extra_actions(self):
        data = {
            "Users": {
                **{action.name: 1 for action in Actions},
                "EXTRA": 1
            }
        }

        with self.assertRaises(ValidationError) as ctx:
            get_permission_field(self.serializer).to_internal_value(data)
        
        self.assertIn("unknown_action", str(ctx.exception))
        
    def test_invalid_action_permission_type(self):
        data = {
            "Users": {
                action.name: "yes" for action in Actions
            }
        }

        with self.assertRaises(ValidationError) as ctx:
            get_permission_field(self.serializer).to_internal_value(data)
        
        self.assertIn("invalid_action_permission", str(ctx.exception))
