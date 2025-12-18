from django.test import TestCase
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from role_management.enums import Actions
from role_management.models import (
    Module,
    ModuleAccess,
    ModuleContentType,
)

class ModuleModelTest(TestCase):
    def test_create_module(self):
        module = Module.objects.create(name="Users")
        self.assertEqual(module.name, "Users")

    def test_module_name_unique(self):
        Module.objects.create(name="Users")
        with self.assertRaises(IntegrityError):
            Module.objects.create(name="Users")

    def test_module_str(self):
        module = Module.objects.create(name="Billing")
        self.assertEqual(str(module), "Billing")


class ModuleContentTypeModelTest(TestCase):
    def setUp(self):
        self.module = Module.objects.create(name="Users")
        self.content_type = ContentType.objects.get_for_model(Group)

    def test_create_module_content_type(self):
        mct = ModuleContentType.objects.create(
            module=self.module,
            content_type=self.content_type
        )
        self.assertEqual(mct.module, self.module)
        self.assertEqual(mct.content_type, self.content_type)

    def test_unique_content_type_constraint(self):
        ModuleContentType.objects.create(
            module=self.module,
            content_type=self.content_type
        )

        another_module = Module.objects.create(name="Billing")

        # Same content_type cannot be attached to another module
        with self.assertRaises(IntegrityError):
            ModuleContentType.objects.create(
                module=another_module,
                content_type=self.content_type
            )

    def test_module_has_content_type_relationship(self):
        self.module.content_types.add(self.content_type)
        self.assertIn(self.content_type, self.module.content_types.all())
        self.module.content_types.remove(self.content_type)        
        self.assertNotIn(self.content_type, self.module.content_types.all())


class ModuleAccessModelTest(TestCase):
    def setUp(self):
        self.module = Module.objects.create(name="Users")
        self.group = Group.objects.create(name="Admins")

    def test_create_module_access(self):
        access = ModuleAccess.objects.create(
            module=self.module,
            group=self.group,
            permissions=1
        )
        self.assertEqual(access.permissions, 1)

    def test_unique_module_group_constraint(self):
        ModuleAccess.objects.create(
            module=self.module,
            group=self.group,
            permissions=3
        )

        with self.assertRaises(IntegrityError):
            ModuleAccess.objects.create(
                module=self.module,
                group=self.group,
                permissions=7
            )

class ModuleAccessValidationTest(TestCase):
    def setUp(self):
        self.module = Module.objects.create(name="Users")
        self.group = Group.objects.create(name="Editors")

    def test_permissions_min_value(self):
        access = ModuleAccess(
            module=self.module,
            group=self.group,
            permissions=0
        )

        with self.assertRaises(ValidationError):
            access.full_clean()

    def test_permissions_max_value(self):
        access = ModuleAccess(
            module=self.module,
            group=self.group,
            permissions=16
        )

        with self.assertRaises(ValidationError):
            access.full_clean()

    def test_permissions_valid_range(self):
        access = ModuleAccess(
            module=self.module,
            group=self.group,
            permissions=15
        )

        # Should not raise
        access.full_clean()


class ModuleAccessPermissionMethodTest(TestCase):
    def setUp(self):
        self.module = Module.objects.create(name="Users")
        self.group = Group.objects.create(name="Managers")

        # Example: 0b0101 (read + delete, depending on your bit mapping)
        self.access = ModuleAccess.objects.create(
            module=self.module,
            group=self.group,
            permissions=0b0101
        )

    def test_has_permission(self):
        self.assertTrue(self.access.has_permission(Actions.read))
        self.assertFalse(self.access.has_permission(Actions.create))
        self.assertTrue(self.access.has_permission(Actions.update))
        self.assertFalse(self.access.has_permission(Actions.delete))
