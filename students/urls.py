from django.urls import path
from .views import*

urlpatterns = [
    # Student management
    path('students/', StudentListCreateAPIView.as_view(), name='student-list-create'),
    path('students/<int:pk>/', StudentDetailAPIView.as_view(), name='student-detail'),
    path('students/search/', StudentSearchAPIView.as_view(), name='student-search'),
    
    # Attendance
    path('attendance/', StudentAttendanceListCreateAPIView.as_view(), name='student-attendance-list'),
    path('attendance/<int:pk>/', StudentAttendanceDetailAPIView.as_view(), name='student-attendance-detail'),
    path('attendance/bulk/', BulkAttendanceAPIView.as_view(), name='student-attendance-bulk'),
    
    # Promotion & Section
    path('promote/', StudentPromotionAPIView.as_view(), name='student-promote'),
    path('promote/bulk/', BulkPromotionAPIView.as_view(), name='student-promote-bulk'),
    path('students/<int:student_id>/assign-section/', AssignSectionAPIView.as_view(), name='assign-section'),
    
    # Parent/Guardian
    path('students/<int:student_id>/parent/', ParentDetailAPIView.as_view(), name='student-parent'),
    
    # Documents
    path('documents/', StudentDocumentListCreateAPIView.as_view(), name='student-documents'),
    path('documents/<int:pk>/', StudentDocumentDetailAPIView.as_view(), name='student-document-detail'),
    
    # Academic records
    path('academic-records/', StudentAcademicRecordListAPIView.as_view(), name='student-academic-records'),
    
    # Dashboard
    path('dashboard/', StudentDashboardAPIView.as_view(), name='student-dashboard'),
    
    # Fees
    path('fees/payment/', StudentFeePaymentAPIView.as_view(), name='student-fee-payment'),
    path('profile/', StudentProfileAPIView.as_view(), name='student-profile'),
    path('profile/picture/', UpdateProfilePictureAPIView.as_view(), name='update-profile-picture'),
    path('parents/', ParentInfoAPIView.as_view(), name='parent-info'),
    
    # Academics
    path('timetable/', ClassTimetableAPIView.as_view(), name='class-timetable'),
    path('subjects/', AssignedSubjectsAPIView.as_view(), name='assigned-subjects'),
    path('teachers/', TeachersListAPIView.as_view(), name='teachers-list'),
    path('assignments/', AssignmentsAPIView.as_view(), name='assignments'),
    path('assignments/<int:assignment_id>/', AssignmentDetailAPIView.as_view(), name='assignment-detail'),
    path('assignments/<int:assignment_id>/submit/', SubmitAssignmentAPIView.as_view(), name='submit-assignment'),
    path('exams/schedule/', ExamScheduleAPIView.as_view(), name='exam-schedule'),
    path('exams/results/', ExamResultsAPIView.as_view(), name='exam-results'),
    
    # Attendance
    path('attendance/summary/', AttendanceSummaryAPIView.as_view(), name='attendance-summary'),
    path('attendance/daily/', DailyAttendanceAPIView.as_view(), name='daily-attendance'),
    
    # Fees
    path('fees/details/', FeeDetailsAPIView.as_view(), name='fee-details'),
    path('fees/history/', FeePaymentHistoryAPIView.as_view(), name='fee-history'),
    path('fees/pay/<int:fee_structure_id>/', PayFeeAPIView.as_view(), name='pay-fee'),
    path('fees/receipt/<int:payment_id>/', DownloadFeeReceiptAPIView.as_view(), name='download-receipt'),
    
    # Report Card
    path('report-card/', ReportCardAPIView.as_view(), name='report-card'),
    path('report-card/<str:academic_year>/', ReportCardAPIView.as_view(), name='report-card-year'),
]