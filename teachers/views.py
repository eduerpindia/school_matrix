# teachers/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Prefetch
from django.db import transaction
from datetime import datetime, date

from .models import Teacher, TeacherSubject, TeacherAttendance, TeacherSalary
from classes.models import Class, Section, Subject, ClassSubject, TimeTable
from schools.models import SchoolSession
from .serializers import (
    TeacherListSerializer,
    TeacherDetailSerializer,
    TeacherCreateSerializer,
    TeacherUpdateSerializer,
    SubjectAssignmentSerializer,
    TeacherSubjectSerializer,
    TimetableAssignmentSerializer,
    TimeTableSerializer,
    TeacherAttendanceSerializer,
    TeacherSalarySerializer,
)
from core.custom_permission import TeachersModulePermission
from core.models import Module, Permission

# ========================================
# TEACHER CRUD APIS
# ========================================

class TeacherListAPIView(APIView):
    """
    GET: List all teachers with filters
    
    URL: /api/teachers/
    
    Query Params:
    - search: Search by name, email, employee_id
    - is_active: Filter by active status (true/false)
    - employment_type: Filter by employment type (PERMANENT, CONTRACT, etc.)
    - is_class_teacher: Filter class teachers (true/false)
    - qualification: Filter by qualification
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20)
    """
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def get(self, request):
        # Check if user is admin
        if request.user.user_type not in ['school_admin', 'principal']:
            return Response({
                'success': False,
                'error': 'Permission denied',
                'message': 'Only school admin or principal can view teachers'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get query parameters
        search = request.GET.get('search', '').strip()
        is_active = request.GET.get('is_active')
        employment_type = request.GET.get('employment_type')
        is_class_teacher = request.GET.get('is_class_teacher')
        qualification = request.GET.get('qualification')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        # Base queryset
        queryset = Teacher.objects.select_related('user').prefetch_related(
            'subjects__subject',
            'taught_subjects__class_obj',
            'taught_subjects__section',
            'classes_as_class_teacher'
        ).all()
        
        # Apply filters
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(employee_id__icontains=search) |
                Q(phone__icontains=search)
            )
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        if employment_type:
            queryset = queryset.filter(employment_type=employment_type.upper())
        
        if is_class_teacher is not None:
            queryset = queryset.filter(is_class_teacher=is_class_teacher.lower() == 'true')
        
        if qualification:
            queryset = queryset.filter(qualification__icontains=qualification)
        
        # Order by
        queryset = queryset.order_by('-created_at')
        
        # Count total
        total_count = queryset.count()
        
        # Pagination
        start = (page - 1) * page_size
        end = start + page_size
        teachers = queryset[start:end]
        
        # Serialize
        serializer = TeacherListSerializer(teachers, many=True)
        
        return Response({
            'success': True,
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class TeacherCreateAPIView(APIView):
    """
    POST: Create new teacher
    
    URL: /api/teachers/create/
    
    Body:
    {
        "email": "teacher@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "9876543210",
        "password": "optional",
        "employee_id": "EMP001",
        "date_of_birth": "1990-05-15",
        "gender": "M",
        "blood_group": "O+",
        "address": "123 Main St",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400001",
        "emergency_contact": "9876543211",
        "qualification": "M.Ed",
        "specialization": "Mathematics",
        "experience_years": 5,
        "date_of_joining": "2023-06-01",
        "employment_type": "PERMANENT",
        "is_class_teacher": false,
        "is_active": true,
        "assign_teacher_role": true,
        "modules": ["students", "attendance", "classes"]
    }
    """
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def post(self, request):
        # Check if user is admin
        if request.user.user_type not in ['school_admin', 'principal']:
            return Response({
                'success': False,
                'error': 'Permission denied',
                'message': 'Only school admin or principal can create teachers'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validate data
        serializer = TeacherCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Validation error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create teacher
            teacher = serializer.save()
            
            # Return detailed response
            detail_serializer = TeacherDetailSerializer(teacher)
            
            return Response({
                'success': True,
                'message': f'Teacher created successfully with Employee ID: {teacher.employee_id}',
                'data': detail_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Failed to create teacher',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeacherDetailAPIView(APIView):
    """
    GET: Get teacher detail by ID
    
    URL: /api/teachers/<id>/
    """
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def get(self, request, pk):
        try:
            teacher = Teacher.objects.select_related('user').prefetch_related(
                'subjects__subject',
                'taught_subjects__class_obj',
                'taught_subjects__section',
                'taught_subjects__subject',
                'classes_as_class_teacher'
            ).get(pk=pk)
        except Teacher.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Teacher not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TeacherDetailSerializer(teacher)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class TeacherUpdateAPIView(APIView):
    """
    PUT/PATCH: Update teacher information
    
    URL: /api/teachers/<id>/update/
    
    Body: (all fields optional for PATCH)
    {
        "first_name": "John",
        "last_name": "Doe",
        "phone": "9876543210",
        "address": "New Address",
        "qualification": "M.Ed, PhD",
        "experience_years": 6,
        "is_active": true
    }
    """
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def put(self, request, pk):
        return self._update(request, pk, partial=False)
    
    def patch(self, request, pk):
        return self._update(request, pk, partial=True)
    
    def _update(self, request, pk, partial=False):
        # Check if user is admin
        if request.user.user_type not in ['school_admin', 'principal']:
            return Response({
                'success': False,
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            teacher = Teacher.objects.get(pk=pk)
        except Teacher.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Teacher not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validate and update
        serializer = TeacherUpdateSerializer(
            teacher,
            data=request.data,
            partial=partial
        )
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Validation error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            teacher = serializer.save()
            
            # Return updated data
            detail_serializer = TeacherDetailSerializer(teacher)
            
            return Response({
                'success': True,
                'message': 'Teacher updated successfully',
                'data': detail_serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Failed to update teacher',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeacherActivateDeactivateAPIView(APIView):
    """
    POST: Activate or deactivate teacher
    
    URL: /api/teachers/<id>/toggle-status/
    
    Body:
    {
        "is_active": true/false
    }
    """
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def post(self, request, pk):
        # Check if user is admin
        if request.user.user_type not in ['school_admin', 'principal']:
            return Response({
                'success': False,
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            teacher = Teacher.objects.get(pk=pk)
        except Teacher.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Teacher not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        is_active = request.data.get('is_active')
        
        if is_active is None:
            return Response({
                'success': False,
                'error': 'is_active field is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        teacher.is_active = is_active
        teacher.user.is_active = is_active
        
        teacher.save()
        teacher.user.save()
        
        action = 'activated' if is_active else 'deactivated'
        
        return Response({
            'success': True,
            'message': f'Teacher {action} successfully',
            'data': {
                'id': teacher.id,
                'employee_id': teacher.employee_id,
                'name': teacher.user.get_full_name(),
                'is_active': teacher.is_active
            }
        }, status=status.HTTP_200_OK)


class TeacherDeleteAPIView(APIView):
    """
    DELETE: Delete teacher (soft delete by default)
    
    URL: /api/teachers/<id>/delete/
    
    Query Params:
    - hard_delete: true/false (default: false)
    """
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def delete(self, request, pk):
        # Check if user is admin
        if request.user.user_type not in ['school_admin', 'principal']:
            return Response({
                'success': False,
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            teacher = Teacher.objects.get(pk=pk)
        except Teacher.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Teacher not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        hard_delete = request.GET.get('hard_delete', 'false').lower() == 'true'
        
        employee_id = teacher.employee_id
        name = teacher.user.get_full_name()
        
        if hard_delete:
            # Hard delete - permanently remove
            teacher.user.delete()  # Cascade will delete teacher
            message = f'Teacher {name} ({employee_id}) permanently deleted'
        else:
            # Soft delete - just deactivate
            teacher.is_active = False
            teacher.user.is_active = False
            teacher.save()
            teacher.user.save()
            message = f'Teacher {name} ({employee_id}) deactivated'
        
        return Response({
            'success': True,
            'message': message
        }, status=status.HTTP_200_OK)


# ========================================
# SUBJECT ASSIGNMENT APIS
# ========================================

class AssignSubjectsToTeacherAPIView(APIView):
    """
    POST: Assign subjects to teacher
    
    URL: /api/teachers/assign-subjects/
    
    Body:
    {
        "teacher_id": 1,
        "subject_ids": [1, 2, 3],
        "class_ids": [5, 6],  // Optional
        "academic_year": "2024-2025"  // Optional, defaults to current
    }
    """
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def post(self, request):
        # Check if user is admin
        if request.user.user_type not in ['school_admin', 'principal']:
            return Response({
                'success': False,
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SubjectAssignmentSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Validation error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            assignments = serializer.save()
            
            response_serializer = TeacherSubjectSerializer(assignments, many=True)
            
            return Response({
                'success': True,
                'message': f'{len(assignments)} subject(s) assigned successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Failed to assign subjects',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RemoveSubjectFromTeacherAPIView(APIView):
    """
    DELETE: Remove subject from teacher
    
    URL: /api/teachers/remove-subject/<teacher_subject_id>/
    """
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def delete(self, request, pk):
        # Check if user is admin
        if request.user.user_type not in ['school_admin', 'principal']:
            return Response({
                'success': False,
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            teacher_subject = TeacherSubject.objects.get(pk=pk)
        except TeacherSubject.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Subject assignment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        teacher_name = teacher_subject.teacher.user.get_full_name()
        subject_name = teacher_subject.subject.name
        
        teacher_subject.delete()
        
        return Response({
            'success': True,
            'message': f'Subject {subject_name} removed from {teacher_name}'
        }, status=status.HTTP_200_OK)


class TeacherSubjectsListAPIView(APIView):
    """
    GET: Get all subjects assigned to a teacher
    
    URL: /api/teachers/<teacher_id>/subjects/
    
    Query Params:
    - academic_year: Filter by academic year
    """
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def get(self, request, teacher_id):
        try:
            teacher = Teacher.objects.get(pk=teacher_id)
        except Teacher.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Teacher not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        academic_year = request.GET.get('academic_year')
        
        queryset = TeacherSubject.objects.filter(
            teacher=teacher,
            subject__is_active=True
        ).select_related('subject')
        
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
        
        serializer = TeacherSubjectSerializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'teacher': {
                'id': teacher.id,
                'name': teacher.user.get_full_name(),
                'employee_id': teacher.employee_id
            },
            'data': serializer.data
        }, status=status.HTTP_200_OK)


# ========================================
# TIMETABLE ASSIGNMENT APIS
# ========================================

class AssignTimetableToTeacherAPIView(APIView):
    """
    POST: Assign timetable period to teacher
    
    URL: /api/teachers/assign-timetable/
    
    Body:
    {
        "class_id": 5,
        "section_id": 1,
        "subject_id": 3,
        "teacher_id": 2,
        "day": "MON",
        "period": 1,
        "start_time": "09:00:00",
        "end_time": "09:45:00",
        "room_number": "101"
    }
    """
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def post(self, request):
        # Check if user is admin
        if request.user.user_type not in ['school_admin', 'principal']:
            return Response({
                'success': False,
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = TimetableAssignmentSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Validation error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            timetable = serializer.save()
            
            response_serializer = TimeTableSerializer(timetable)
            
            return Response({
                'success': True,
                'message': 'Timetable period assigned successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Failed to assign timetable',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateTimetableAPIView(APIView):
    """
    PUT/PATCH: Update timetable entry
    
    URL: /api/teachers/timetable/<id>/update/
    """
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def put(self, request, pk):
        return self._update(request, pk, partial=False)
    
    def patch(self, request, pk):
        return self._update(request, pk, partial=True)
    
    def _update(self, request, pk, partial=False):
        # Check if user is admin
        if request.user.user_type not in ['school_admin', 'principal']:
            return Response({
                'success': False,
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            timetable = TimeTable.objects.get(pk=pk)
        except TimeTable.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Timetable entry not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TimeTableSerializer(
            timetable,
            data=request.data,
            partial=partial
        )
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Validation error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            timetable = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Timetable updated successfully',
                'data': TimeTableSerializer(timetable).data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Failed to update timetable',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RemoveTimetableAPIView(APIView):
    """
    DELETE: Remove timetable entry
    
    URL: /api/teachers/timetable/<id>/delete/
    """
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def delete(self, request, pk):
        # Check if user is admin
        if request.user.user_type not in ['school_admin', 'principal']:
            return Response({
                'success': False,
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            timetable = TimeTable.objects.get(pk=pk)
        except TimeTable.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Timetable entry not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        timetable.delete()
        
        return Response({
            'success': True,
            'message': 'Timetable entry deleted successfully'
        }, status=status.HTTP_200_OK)


class TeacherTimetableAPIView(APIView):
    """
    GET: Get teacher's complete timetable
    
    URL: /api/teachers/<teacher_id>/timetable/
    
    Query Params:
    - day: Filter by specific day (MON, TUE, etc.)
    """
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def get(self, request, teacher_id):
        try:
            teacher = Teacher.objects.get(pk=teacher_id)
        except Teacher.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Teacher not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        day = request.GET.get('day')
        
        # Get current session
        try:
            current_session = SchoolSession.objects.get(is_current=True)
        except SchoolSession.DoesNotExist:
            return Response({
                'success': False,
                'error': 'No active session found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = TimeTable.objects.filter(
            teacher=teacher,
            session=current_session,
            is_active=True
        ).select_related(
            'class_obj',
            'section',
            'subject'
        ).order_by('day', 'period')
        
        if day:
            queryset = queryset.filter(day=day.upper())
        
        serializer = TimeTableSerializer(queryset, many=True)
        
        # Group by day
        timetable_by_day = {}
        for item in serializer.data:
            day_name = item['day']
            if day_name not in timetable_by_day:
                timetable_by_day[day_name] = []
            timetable_by_day[day_name].append(item)
        
        return Response({
            'success': True,
            'teacher': {
                'id': teacher.id,
                'name': teacher.user.get_full_name(),
                'employee_id': teacher.employee_id
            },
            'session': current_session.name,
            'total_periods': queryset.count(),
            'timetable_by_day': timetable_by_day,
            'all_periods': serializer.data
        }, status=status.HTTP_200_OK)


class TeacherTodayClassesAPIView(APIView):
    """
    GET: Get teacher's classes for today
    
    URL: /api/teachers/<teacher_id>/today-classes/
    """
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def get(self, request, teacher_id):
        try:
            teacher = Teacher.objects.get(pk=teacher_id, is_active=True)
        except Teacher.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Teacher not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get current day
        days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
        today = days[date.today().weekday()]
        
        # Get current session
        try:
            current_session = SchoolSession.objects.get(is_current=True)
        except SchoolSession.DoesNotExist:
            return Response({
                'success': False,
                'error': 'No active session found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get today's timetable
        queryset = TimeTable.objects.filter(
            teacher=teacher,
            day=today,
            session=current_session,
            is_active=True
        ).select_related(
            'class_obj',
            'section',
            'subject'
        ).order_by('period')
        
        serializer = TimeTableSerializer(queryset, many=True)
        
        return Response({
            'success': True,
            'teacher': {
                'id': teacher.id,
                'name': teacher.user.get_full_name(),
                'employee_id': teacher.employee_id
            },
            'date': date.today(),
            'day': today,
            'total_classes': queryset.count(),
            'classes': serializer.data
        }, status=status.HTTP_200_OK)


# ========================================
# TEACHER WORKLOAD & REPORTS
# ========================================

class TeacherWorkloadReportAPIView(APIView):
    """
    GET: Get teacher workload report
    
    URL: /api/teachers/<teacher_id>/workload/
    """
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def get(self, request, teacher_id):
        try:
            teacher = Teacher.objects.get(pk=teacher_id)
        except Teacher.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Teacher not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get current session
        try:
            current_session = SchoolSession.objects.get(is_current=True)
        except SchoolSession.DoesNotExist:
            return Response({
                'success': False,
                'error': 'No active session found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Count subjects
        total_subjects = teacher.subjects.filter(
            subject__is_active=True
        ).values('subject').distinct().count()
        
        # Count classes
        total_classes = teacher.taught_subjects.filter(
            session=current_session
        ).values('class_obj', 'section').distinct().count()
        
        # Count periods per week
        periods_per_week = TimeTable.objects.filter(
            teacher=teacher,
            session=current_session,
            is_active=True
        ).count()
        
        # Count periods per day
        periods_by_day = {}
        for day_code, day_name in TimeTable.DAY_CHOICES:
            count = TimeTable.objects.filter(
                teacher=teacher,
                day=day_code,
                session=current_session,
                is_active=True
            ).count()
            periods_by_day[day_name] = count
        
        return Response({
            'success': True,
            'teacher': {
                'id': teacher.id,
                'name': teacher.user.get_full_name(),
                'employee_id': teacher.employee_id,
                'is_class_teacher': teacher.is_class_teacher
            },
            'workload': {
                'total_subjects': total_subjects,
                'total_classes': total_classes,
                'periods_per_week': periods_per_week,
                'periods_by_day': periods_by_day
            }
        }, status=status.HTTP_200_OK)


class AllTeachersWorkloadAPIView(APIView):
    """
    GET: Get workload summary for all teachers
    
    URL: /api/teachers/workload-summary/
    """
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def get(self, request):
        # Check if user is admin
        if request.user.user_type not in ['school_admin', 'principal']:
            return Response({
                'success': False,
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get current session
        try:
            current_session = SchoolSession.objects.get(is_current=True)
        except SchoolSession.DoesNotExist:
            return Response({
                'success': False,
                'error': 'No active session found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        teachers = Teacher.objects.filter(is_active=True).select_related('user')
        
        workload_data = []
        
        for teacher in teachers:
            total_periods = TimeTable.objects.filter(
                teacher=teacher,
                session=current_session,
                is_active=True
            ).count()
            
            total_subjects = teacher.subjects.filter(
                subject__is_active=True
            ).values('subject').distinct().count()
            
            total_classes = teacher.taught_subjects.filter(
                session=current_session
            ).values('class_obj', 'section').distinct().count()
            
            workload_data.append({
                'teacher_id': teacher.id,
                'employee_id': teacher.employee_id,
                'name': teacher.user.get_full_name(),
                'is_class_teacher': teacher.is_class_teacher,
                'total_subjects': total_subjects,
                'total_classes': total_classes,
                'periods_per_week': total_periods
            })
        
        # Sort by periods_per_week descending
        workload_data.sort(key=lambda x: x['periods_per_week'], reverse=True)
        
        return Response({
            'success': True,
            'session': current_session.name,
            'total_teachers': len(workload_data),
            'data': workload_data
        }, status=status.HTTP_200_OK)




# Permission

from .serializers import *
from django.shortcuts import get_object_or_404
class PermissionModuleListView(APIView):
    """
    API 1: Get all modules with their permissions
    GET /api/permissions/modules/
    """
    permission_classes = [TeachersModulePermission]
    
    def get(self, request):
        """List all active modules with permissions"""
        if not request.user.is_superuser and getattr(request.user, 'user_type', None) != 'school_admin':
            return Response(
                {"error": "Only school admins can view modules"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        modules = Module.objects.filter(is_active=True).prefetch_related('permissions')
        serializer = ModuleSerializer(modules, many=True)
        return Response(serializer.data)


class AssignTeacherPermissionView(APIView):
    """
    API 2: Assign permissions to teacher
    POST /api/permissions/assign/
    """
    permission_classes = [TeachersModulePermission]
    
    def post(self, request):
        """Assign permissions to teacher"""
        if not request.user.is_superuser and getattr(request.user, 'user_type', None) != 'school_admin':
            return Response(
                {"error": "Only school admins can assign permissions"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AssignPermissionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherPermissionDetailView(APIView):
    """
    API 3: Get teacher's permission details
    GET /api/permissions/teacher/<teacher_id>/
    """
    permission_classes = [TeachersModulePermission]
    
    def get(self, request, teacher_id):
        """Get teacher permission details"""
        if not request.user.is_superuser and getattr(request.user, 'user_type', None) != 'school_admin':
            return Response(
                {"error": "Only school admins can view permissions"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        teacher = get_object_or_404(Teacher, id=teacher_id, is_active=True)
        serializer = TeacherPermissionDetailSerializer(teacher)
        return Response(serializer.data)


class EditTeacherPermissionView(APIView):
    """
    API 4: Edit teacher permissions (add/remove)
    POST /api/permissions/edit/
    """
    permission_classes = [TeachersModulePermission]
    
    def post(self, request):
        """Edit teacher permissions"""
        if not request.user.is_superuser and getattr(request.user, 'user_type', None) != 'school_admin':
            return Response(
                {"error": "Only school admins can edit permissions"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = EditPermissionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)