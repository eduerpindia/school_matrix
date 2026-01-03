# urls.py

from django.urls import path

from .views import*
urlpatterns = [
    # ============================================================
    # STUDENT ADMIN CRUD / LISTING  Done All 
    # ============================================================
    path('students/', StudentListAPIView.as_view(), name='student-list'),
    path('students/create/', StudentCreateAPIView.as_view(), name='student-create'),
    path('students/<int:pk>/', StudentRetrieveAPIView.as_view(), name='student-detail'),
    path('students/<int:pk>/update/', StudentUpdateAPIView.as_view(), name='student-update'),
    path('students/<int:pk>/deactivate/', StudentSoftDeleteAPIView.as_view(), name='student-soft-delete'),
    path('students/<int:pk>/delete/', StudentHardDeleteAPIView.as_view(), name='student-hard-delete'),
    path('students/search/', StudentSearchAPIView.as_view(), name='student-search'),

    # Parent details (Admin side)
    path('students/<int:student_id>/parents/', ParentDetailAPIView.as_view(), name='student-parents-detail'),

    # ============================================================
    # STUDENT ACADEMIC RECORDS (ADMIN)
    # ============================================================
    path('academic-records/', StudentAcademicRecordListAPIView.as_view(), name='academic-record-list'),
    path('academic-records/create/', StudentAcademicRecordCreateAPIView.as_view(), name='academic-record-create'),
    path('academic-records/<int:pk>/', StudentAcademicRecordRetrieveAPIView.as_view(), name='academic-record-detail'),
    path('academic-records/<int:pk>/update/', StudentAcademicRecordUpdateAPIView.as_view(), name='academic-record-update'),
    path('academic-records/<int:pk>/delete/', StudentAcademicRecordDeleteAPIView.as_view(), name='academic-record-delete'),

    # ============================================================
    # STUDENT DOCUMENTS (ADMIN)
    # ============================================================
    path('documents/', StudentDocumentListAPIView.as_view(), name='document-list'),
    path('documents/create/', StudentDocumentCreateAPIView.as_view(), name='document-create'),
    path('documents/<int:pk>/', StudentDocumentRetrieveAPIView.as_view(), name='document-detail'),
    path('documents/<int:pk>/update/',  StudentDocumentUpdateAPIView.as_view(), name='document-update'),
    path('documents/<int:pk>/delete/',  StudentDocumentDeleteAPIView.as_view(), name='document-delete'),

    # ============================================================
    # ATTENDANCE (ADMIN)
    # ============================================================
    path('attendance/',  StudentAttendanceListAPIView.as_view(), name='attendance-list'),
    path('attendance/create/',  StudentAttendanceCreateAPIView.as_view(), name='attendance-create'),
    path('attendance/<int:pk>/',  StudentAttendanceRetrieveAPIView.as_view(), name='attendance-detail'),
    path('attendance/<int:pk>/update/',  StudentAttendanceUpdateAPIView.as_view(), name='attendance-update'),
    path('attendance/<int:pk>/delete/',  StudentAttendanceDeleteAPIView.as_view(), name='attendance-delete'),
    path('attendance/bulk/',  BulkAttendanceCreateAPIView.as_view(), name='attendance-bulk'),
    path('attendance/<int:student_id>/summary/',  StudentAttendanceSummaryAPIView.as_view(), name='attendance-summary-admin'),

    # Class + Section student list
    path('classes/<int:class_id>/sections/<int:section_id>/students/',  StudentClassSectionAPIView.as_view(), name='class-section-students'),

    # Assign section & roll
    path('students/<int:student_id>/assign-section/',  AssignSectionAPIView.as_view(), name='assign-section'),

    # ============================================================
    # PROMOTION (ADMIN)
    # ============================================================
    # Manual promotion using payload (StudentPromotionSerializer)
    path('students/promote/',  StudentPromotionAPIView.as_view(), name='student-promote-manual'),
    # Bulk promotion
    path('students/promote/bulk/',  BulkPromotionAPIView.as_view(), name='student-promote-bulk'),
    # Auto promotion based on class name (numeric)
    path('students/<int:student_id>/promote-auto/',  StudentPromoteAPIView.as_view(), name='student-promote-auto'),

    # ============================================================
    # DASHBOARD (ADMIN)
    # ============================================================
    path('dashboard/students/',  StudentDashboardAPIView.as_view(), name='student-dashboard'),

    # Generic admin-initiated fee payment placeholder
    path('fees/admin/payment/',  StudentFeePaymentAPIView.as_view(), name='admin-fee-payment'),

    # ============================================================
    # STUDENT PORTAL (SELF) - PROFILE & PARENTS
    # ============================================================
    path('me/profile/',  StudentProfileAPIView.as_view(), name='student-profile'),
    path('me/profile/photo/',  UpdateProfilePictureAPIView.as_view(), name='student-profile-photo'),
    path('me/parents/',  ParentInfoAPIView.as_view(), name='student-parents-self'),

    # ============================================================
    # STUDENT PORTAL (SELF) - TIMETABLE / SUBJECTS / TEACHERS
    # ============================================================
    path('me/timetable/',  ClassTimetableAPIView.as_view(), name='student-timetable'),
    path('me/subjects/',  AssignedSubjectsAPIView.as_view(), name='student-subjects'),
    path('me/teachers/',  TeachersListAPIView.as_view(), name='student-teachers'),

    # ============================================================
    # STUDENT PORTAL (SELF) - ASSIGNMENTS
    # ============================================================
    path('me/assignments/',  AssignmentsAPIView.as_view(), name='student-assignments'),
    path('me/assignments/<int:assignment_id>/',  AssignmentDetailAPIView.as_view(), name='student-assignment-detail'),
    path('me/assignments/<int:assignment_id>/submit/',  SubmitAssignmentAPIView.as_view(), name='student-assignment-submit'),

    # ============================================================
    # STUDENT PORTAL (SELF) - EXAMS
    # ============================================================
    path('me/exams/schedule/',  ExamScheduleAPIView.as_view(), name='student-exam-schedule'),
    path('me/exams/results/',  ExamResultsAPIView.as_view(), name='student-exam-results'),

    # ============================================================
    # STUDENT PORTAL (SELF) - ATTENDANCE
    # ============================================================
    path('me/attendance/summary/',  AttendanceSummaryStudentAPIView.as_view(), name='student-attendance-summary'),
    path('me/attendance/daily/',  DailyAttendanceAPIView.as_view(), name='student-daily-attendance'),

    # ============================================================
    # STUDENT PORTAL (SELF) - FEES
    # ============================================================
    path('me/fees/',  FeeDetailsAPIView.as_view(), name='student-fees'),
    path('me/fees/history/',  FeePaymentHistoryAPIView.as_view(), name='student-fees-history'),
    path('me/fees/<int:fee_structure_id>/pay/',  PayFeeAPIView.as_view(), name='student-fee-pay'),
    path('me/fees/receipt/<int:payment_id>/',  DownloadFeeReceiptAPIView.as_view(), name='student-fee-receipt'),

    # ============================================================
    # STUDENT PORTAL (SELF) - REPORT CARD
    # ============================================================
    path('me/report-card/',  ReportCardAPIView.as_view(), name='student-report-card-current'),
    path('me/report-card/<str:academic_year>/',  ReportCardAPIView.as_view(), name='student-report-card'),
]
