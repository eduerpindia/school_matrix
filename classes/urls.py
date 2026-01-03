from django.urls import path
from .views import *

urlpatterns = [
    # ==================== CLASS URLs ====================
    path('classes/list/', ClassListAPIView.as_view(), name='class-list'),
    path('classes/create/', ClassCreateAPIView.as_view(), name='class-create'),
    path('classes/<int:pk>/', ClassRetrieveAPIView.as_view(), name='class-retrieve'),
    path('classes/<int:pk>/update/', ClassUpdateAPIView.as_view(), name='class-update'),
    path('classes/<int:pk>/delete/', ClassDeleteAPIView.as_view(), name='class-delete'),
    
    # ==================== SECTION URLs ====================
    path('sections/list/', SectionListAPIView.as_view(), name='section-list'),
    path('sections/create/', SectionCreateAPIView.as_view(), name='section-create'),
    path('sections/<int:pk>/', SectionRetrieveAPIView.as_view(), name='section-retrieve'),
    path('sections/<int:pk>/update/', SectionUpdateAPIView.as_view(), name='section-update'),
    path('sections/<int:pk>/delete/', SectionDeleteAPIView.as_view(), name='section-delete'),
    
    # ==================== SUBJECT URLs ====================
    path('subjects/list/', SubjectListAPIView.as_view(), name='subject-list'),
    path('subjects/create/', SubjectCreateAPIView.as_view(), name='subject-create'),
    path('subjects/<int:pk>/', SubjectRetrieveAPIView.as_view(), name='subject-retrieve'),
    path('subjects/<int:pk>/update/', SubjectUpdateAPIView.as_view(), name='subject-update'),
    path('subjects/<int:pk>/delete/', SubjectDeleteAPIView.as_view(), name='subject-delete'),
    
    # ==================== CLASS SUBJECT URLs ====================
    path('class-subjects/list/', ClassSubjectListAPIView.as_view(), name='class-subject-list'),
    path('class-subjects/create/', ClassSubjectCreateAPIView.as_view(), name='class-subject-create'),
    path('class-subjects/<int:pk>/', ClassSubjectRetrieveAPIView.as_view(), name='class-subject-retrieve'),
    path('class-subjects/<int:pk>/update/', ClassSubjectUpdateAPIView.as_view(), name='class-subject-update'),
    path('class-subjects/<int:pk>/delete/', ClassSubjectDeleteAPIView.as_view(), name='class-subject-delete'),
    
    # ==================== TIMETABLE URLs ====================
    path('timetables/list/', TimeTableListAPIView.as_view(), name='timetable-list'),
    path('timetables/create/', TimeTableCreateAPIView.as_view(), name='timetable-create'),
    path('timetables/<int:pk>/', TimeTableRetrieveAPIView.as_view(), name='timetable-retrieve'),
    path('timetables/<int:pk>/update/', TimeTableUpdateAPIView.as_view(), name='timetable-update'),
    path('timetables/<int:pk>/delete/', TimeTableDeleteAPIView.as_view(), name='timetable-delete'),
    
    # ==================== SPECIAL URLs ====================
    path('classes/<int:class_id>/sections/', ClassSectionCheckAPIView.as_view(), name='class-sections'),
    path('class-subjects/bulk-assign/', BulkAssignSubjectsAPIView.as_view(), name='bulk-assign-subjects'),
    path('class-subjects/assigned/', AssignedSubjectsAPIView.as_view(), name='assigned-subjects'),
]