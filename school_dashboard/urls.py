from django.urls import path, include
from .views import*
from classes.views import *
from students.views import *
from teachers.views import *
urlpatterns = [
    path('dashboard-details/', AdminDashboardDetails.as_view(), name='school-user-details'),
    path('current/school-session/', CurrentSessionView.as_view(), name='current-session'),
    
    
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
    
    
    # ============================================================
    # STUDENT ADMIN CRUD /  Done
    # ============================================================
    path('students-lists/', StudentListAPIView.as_view(), name='student-list'),
    path('students/create/', StudentCreateAPIView.as_view(), name='student-create'),
    path('students/<int:pk>/', StudentRetrieveAPIView.as_view(), name='student-detail'),
    path('students/<int:pk>/update/', StudentUpdateAPIView.as_view(), name='student-update'),
    path('students/<int:pk>/deactivate/', StudentSoftDeleteAPIView.as_view(), name='student-soft-delete'),
    path('students/<int:pk>/delete/', StudentHardDeleteAPIView.as_view(), name='student-hard-delete'),
    path('students/search/', StudentSearchAPIView.as_view(), name='student-search'),
    path('students/<int:student_id>/parents/', ParentDetailAPIView.as_view(), name='student-parents-detail'),
    path('students/<int:student_id>/parents/', ParentDetailAPIView.as_view(), name='student-parents-detail'),
    path('students/parents/contacts/', ParentContactListAPIView.as_view(), name='parent-contact-list'),
    # ============================================================
    # STUDENT DOCUMENTS
    # ============================================================
    path('students/documents/types/', DocumentTypesAPIView.as_view(), name='document-types-list'),
    path('students/<int:student_id>/documents/upload/', StudentDocumentUploadAPIView.as_view(), name='student-document-upload'),
    path('students/<int:student_id>/documents/', StudentDocumentListAPIView.as_view(), name='student-document-list'),
    path('students/<int:student_id>/documents/<int:document_id>/update/', StudentDocumentUpdateAPIView.as_view(), name='student-document-update'),
    path('students/<int:student_id>/documents/<int:document_id>/replace/', StudentDocumentReplaceAPIView.as_view(), name='student-document-replace'),
    path('students/<int:student_id>/documents/<int:document_id>/delete/', StudentDocumentDeleteAPIView.as_view(), name='student-document-delete'),
    path('students/<int:student_id>/documents/<int:document_id>/download/', StudentDocumentDownloadAPIView.as_view(), name='student-document-download'),
    
    # ============================================================
    # STUDENT ID Card APIs
    # ============================================================
    path('id-cards/generate/', GenerateStudentIDCardAPIView.as_view(), name='generate-id-cards'),
    path('id-cards/templates/', GetAvailableTemplatesAPIView.as_view(), name='available-templates'),
    path('id-cards/available-fields/', GetAvailableFieldsAPIView.as_view(), name='available-fields'),
    
    
    
    
    
    
    
    # ============================================================
    # STUDENT ACADEMIC RECORDS
    # ============================================================
    path('academic-records/', StudentAcademicRecordListAPIView.as_view(), name='academic-record-list'),
    path('academic-records/create/', StudentAcademicRecordCreateAPIView.as_view(), name='academic-record-create'),
    path('academic-records/<int:pk>/', StudentAcademicRecordRetrieveAPIView.as_view(), name='academic-record-detail'),
    path('academic-records/<int:pk>/update/', StudentAcademicRecordUpdateAPIView.as_view(), name='academic-record-update'),
    path('academic-records/<int:pk>/delete/', StudentAcademicRecordDeleteAPIView.as_view(), name='academic-record-delete'),

    
    
    
    
    
    
    
    
    
    # path('students/<int:student_id>/documents/<int:document_id>/', StudentDocumentDetailAPIView.as_view(), name='student-document-detail'),

    
    
    
    
    
    # path('documents/', StudentDocumentListAPIView.as_view(), name='document-list'),
    path('documents/create/', StudentDocumentCreateAPIView.as_view(), name='document-create'),
    path('documents/<int:pk>/', StudentDocumentRetrieveAPIView.as_view(), name='document-detail'),
    path('documents/<int:pk>/update/', StudentDocumentUpdateAPIView.as_view(), name='document-update'),
    path('documents/<int:pk>/delete/', StudentDocumentDeleteAPIView.as_view(), name='document-delete'),

    # ============================================================
    # ATTENDANCE
    # ============================================================
    path('attendance/mark/', AdminMarkAttendanceAPIView.as_view(), name='admin-mark-attendance'),
    path('admin/attendance/bulk-mark/', AdminBulkMarkAttendanceAPIView.as_view(), name='admin-bulk-mark-attendance'),
    path('admin/attendance-details-list/', AdminGetAttendanceAPIView.as_view(), name='admin-get-attendance'),

    # ============================================================
    # CLASS & SECTION MANAGEMENT
    # ============================================================
    path('classes/<int:class_id>/sections/<int:section_id>/students/', StudentClassSectionAPIView.as_view(), name='class-section-students'),
    path('students/<int:student_id>/assign-section/', AssignSectionAPIView.as_view(), name='assign-section'),

    # ============================================================
    # PROMOTION
    # ============================================================
    path('students/promote/', StudentPromotionAPIView.as_view(), name='student-promote-manual'),
    path('students/promote/bulk/', BulkPromotionAPIView.as_view(), name='student-promote-bulk'),
    path('students/<int:student_id>/promote-auto/', StudentPromoteAPIView.as_view(), name='student-promote-auto'),

    # ============================================================
    # DASHBOARD
    # ============================================================
    path('dashboard/students/', StudentDashboardAPIView.as_view(), name='student-dashboard'),

    # ============================================================
    # FEE MANAGEMENT (Placeholder)
    # ============================================================
    path('fees/admin/payment/', StudentFeePaymentAPIView.as_view(), name='admin-fee-payment'),
    
    
    
    
    
    
    
    
    
    
    
    #-------------------------- Start Teacher ---------------------------------------------------------------------------------
    
   # GET /api/teacher-lists - List all teachers with filters
    path('teacher-lists/', TeacherListAPIView.as_view(), name='teacher-list'),
    
    # POST /api/teacher-create/ - Create new teacher
    path('teacher-create/', TeacherCreateAPIView.as_view(), name='teacher-create'),
    
    # GET /api/teacher-details/<id>/ - Get teacher detail
    path('teacher-details/<int:pk>/', TeacherDetailAPIView.as_view(), name='teacher-detail'),
    
    # PUT/PATCH /api/teachers/<id>/update/ - Update teacher
    path('teachers/<int:pk>/update/', TeacherUpdateAPIView.as_view(), name='teacher-update'),
    
    # POST /api/teachers/<id>/toggle-status/ - Activate/Deactivate teacher
    path('teachers/<int:pk>/toggle-status/', TeacherActivateDeactivateAPIView.as_view(), name='teacher-toggle-status'),
    
    # DELETE /api/teachers/<id>/delete/ - Delete teacher (soft/hard)
    path('teachers/<int:pk>/delete/', TeacherDeleteAPIView.as_view(), name='teacher-delete'),
    
    
    # ========================================
    # SUBJECT ASSIGNMENT APIS
    # ========================================
    
    # POST /api/teachers/assign-subjects/ - Assign subjects to teacher
    path('teachers/assign-subjects/', AssignSubjectsToTeacherAPIView.as_view(), name='assign-subjects'),
    
    # DELETE /api/teachers/remove-subject/<id>/ - Remove subject from teacher
    path('teachers/remove-subject/<int:pk>/', RemoveSubjectFromTeacherAPIView.as_view(), name='remove-subject'),
    
    # GET /api/teachers/<teacher_id>/subjects/ - Get teacher's subjects
    path('teachers/<int:teacher_id>/subjects/', TeacherSubjectsListAPIView.as_view(), name='teacher-subjects'),
    
    
    # ========================================
    # TIMETABLE ASSIGNMENT APIS
    # ========================================
    
    # POST /api/teachers/assign-timetable/ - Assign timetable period to teacher
    path('teachers/assign-timetable/', AssignTimetableToTeacherAPIView.as_view(), name='assign-timetable'),
    
    # PUT/PATCH /api/teachers/timetable/<id>/update/ - Update timetable entry
    path('teachers/timetable/<int:pk>/update/', UpdateTimetableAPIView.as_view(), name='update-timetable'),
    
    # DELETE /api/teachers/timetable/<id>/delete/ - Remove timetable entry
    path('teachers/timetable/<int:pk>/delete/', RemoveTimetableAPIView.as_view(), name='remove-timetable'),
    
    # GET /api/teachers/<teacher_id>/timetable/ - Get teacher's complete timetable
    path('teachers/<int:teacher_id>/timetable/', TeacherTimetableAPIView.as_view(), name='teacher-timetable'),
    
    # GET /api/teachers/<teacher_id>/today-classes/ - Get today's classes
    path('teachers/<int:teacher_id>/today-classes/', TeacherTodayClassesAPIView.as_view(), name='teacher-today-classes'),
    
    
    # ========================================
    # WORKLOAD & REPORTS
    # ========================================
    
    # GET /api/teachers/<teacher_id>/workload/ - Get teacher workload report
    path('teachers/<int:teacher_id>/workload/', TeacherWorkloadReportAPIView.as_view(), name='teacher-workload'),
    
    # GET /api/teachers/workload-summary/ - Get all teachers workload summary
    path('teachers/workload-summary/', AllTeachersWorkloadAPIView.as_view(), name='workload-summary'),
    
    #-------------------------- END Teacher ---------------------------------------------------------------------------------
    
    
    
    # Permission Management APIs (4 endpoints)
    path('permissions/modules/', PermissionModuleListView.as_view(), name='permission-modules'),
    path('permissions/assign/', AssignTeacherPermissionView.as_view(), name='assign-permission'),
    path('permissions/teacher/<int:teacher_id>/', TeacherPermissionDetailView.as_view(), name='teacher-permission-detail'),
    path('permissions/edit/', EditTeacherPermissionView.as_view(), name='edit-permission'),
    
    
    
    
    
    
    
    
    
]