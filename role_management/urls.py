from django.urls import path
from . import views

urlpatterns = [
    path('', views.RoleListCreate.as_view(), name='roles'),
    path('<int:pk>/', views.RoleDetail.as_view(), name='role_detail'),
]
