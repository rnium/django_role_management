from django.db import models
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, MaxValueValidator
from .utils import has_permission


class ModuleContentType(models.Model):
    module = models.ForeignKey('role_management.Module', on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['content_type'],
                name='unique_content_type_module'
            )
        ]

class Module(models.Model):
    name = models.CharField(max_length=100, db_index=True, unique=True)
    content_types = models.ManyToManyField(
        ContentType,
        through='role_management.ModuleContentType',
        related_name='modules'
    )
    
    def __str__(self) -> str:
        return self.name    


class ModuleAccess(models.Model):    
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='access')
    
    permissions = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, "A group need to have at least one permission in the module"),
            MaxValueValidator(15, "Currently a group cannot have more than four permissions in the module")
        ]
    )
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['module', 'group'], name='unique_module_group')
        ]
    
    def has_permission(self, action: int):
        return has_permission(self.permissions, action)
