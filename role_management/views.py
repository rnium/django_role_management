from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .serializer import RoleSerializer
from .permission import ModelPermissionAll
from django.contrib.auth.models import Group as Role


class RoleListCreate(ListCreateAPIView):
    serializer_class = RoleSerializer
    queryset = Role.objects.all()
    permission_classes = [ModelPermissionAll]


class RoleDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = RoleSerializer
    permission_classes = [ModelPermissionAll]
    
    def get_queryset(self):
        return Role.objects.filter(pk=self.kwargs.get('pk'))