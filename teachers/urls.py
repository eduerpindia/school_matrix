from django.urls import path
from .views import (
    TeacherListCreateAPIView, TeacherDetailAPIView,
    TeacherSubjectListCreateAPIView, TeacherSubjectDetailAPIView,
    TeacherAttendanceListCreateAPIView, TeacherAttendanceDetailAPIView,
    TeacherSalaryListCreateAPIView, TeacherSalaryDetailAPIView,
    TeacherDashboardAPIView, TeacherBulkAttendanceAPIView
)

urlpatterns = [
    # Teacher endpoints
    path('teachers/', TeacherListCreateAPIView.as_view(), name='teacher-list-create'),
    path('teachers/<int:pk>/', TeacherDetailAPIView.as_view(), name='teacher-detail'),
    
    # Teacher Subject endpoints
    path('teacher-subjects/', TeacherSubjectListCreateAPIView.as_view(), name='teacher-subject-list-create'),
    path('teacher-subjects/<int:pk>/', TeacherSubjectDetailAPIView.as_view(), name='teacher-subject-detail'),
    
    # Teacher Attendance endpoints
    path('teacher-attendance/', TeacherAttendanceListCreateAPIView.as_view(), name='teacher-attendance-list-create'),
    path('teacher-attendance/<int:pk>/', TeacherAttendanceDetailAPIView.as_view(), name='teacher-attendance-detail'),
    path('teacher-attendance/bulk/', TeacherBulkAttendanceAPIView.as_view(), name='teacher-attendance-bulk'),
    
    # Teacher Salary endpoints
    path('teacher-salaries/', TeacherSalaryListCreateAPIView.as_view(), name='teacher-salary-list-create'),
    path('teacher-salaries/<int:pk>/', TeacherSalaryDetailAPIView.as_view(), name='teacher-salary-detail'),
    
    # Dashboard endpoints
    path('dashboard/', TeacherDashboardAPIView.as_view(), name='teacher-dashboard'),
]