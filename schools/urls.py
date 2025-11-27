from django.urls import path
from . import views

urlpatterns = [
    path('', views.SchoolListAPIView.as_view(), name='school_list'),
    path('create/', views.SchoolCreateAPIView.as_view(), name='school_create'),
]