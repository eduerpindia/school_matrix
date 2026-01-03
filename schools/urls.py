from django.urls import path
from .views import *

urlpatterns = [
    path('', SchoolListAPIView.as_view(), name='school_list'),
    path('create/', CreateSchoolAPIView.as_view(), name='school_create'),
    path('scladmin/school-dashboard-details/', SchoolAndUserDetailsAPI.as_view(), name='school-user-details'),
]
