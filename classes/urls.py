from django.urls import path
from .views import  *

urlpatterns = [
    # Class endpoints
    path('classes/', ClassListCreateAPIView.as_view(), name='class-list-create'),
    path('classes/<int:pk>/', ClassDetailAPIView.as_view(), name='class-detail'),
    path('classes-with-sections/', ClassWithSectionsAPIView.as_view(), name='class-with-sections'),
    
    # Section endpoints
    path('sections/', SectionListCreateAPIView.as_view(), name='section-list-create'),
    path('sections/<int:pk>/', SectionDetailAPIView.as_view(), name='section-detail'),
    
    # Subject endpoints
    path('subjects/', SubjectListCreateAPIView.as_view(), name='subject-list-create'),
    path('subjects/<int:pk>/', SubjectDetailAPIView.as_view(), name='subject-detail'),
    
    # ClassSubject endpoints
    path('class-subjects/', ClassSubjectListCreateAPIView.as_view(), name='class-subject-list-create'),
    path('class-subjects/<int:pk>/', ClassSubjectDetailAPIView.as_view(), name='class-subject-detail'),
    
    # TimeTable endpoints
    path('timetable/', TimeTableListCreateAPIView.as_view(), name='timetable-list-create'),
    path('timetable/<int:pk>/', TimeTableDetailAPIView.as_view(), name='timetable-detail'),
]