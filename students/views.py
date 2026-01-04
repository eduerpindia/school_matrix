# views.py

from datetime import date, datetime, timedelta
import calendar

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from schools.models import SchoolSession
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Student,
    StudentAcademicRecord,
    StudentDocument,
    StudentAttendance,
)
from .serializers import *
from core.custom_permission import StudentsModulePermission
from core.models import AcademicYear
from classes.models import Class, Section, ClassSubject
from assignments.models import Assignment, AssignmentSubmission
from examinations.models import ExamResult
from fees.models import FeeStructure, FeePayment
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .utils import *
from schools.models import *
import os
from django.db.models import Count
# ============================================================
# STUDENT ADMIN CRUD / LISTING
# ============================================================


class StudentCreateAPIView(APIView):
    """POST: Create student with auto-generated admission number, college email & password"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        data = request.data
        
        # Get tenant school from request (set by middleware)
        tenant_school = request.tenant
        
        # ========== VALIDATE REQUIRED FIELDS (NO admission_number) ==========
        required_fields = [
            'first_name', 'last_name',
            'admission_date', 'date_of_birth', 'gender',
            'address', 'city', 'state', 'pincode', 'emergency_contact',
            'current_class', 'section', 'roll_number',
            'father_name', 'mother_name'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in data or not data.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            return Response({
                'success': False,
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract basic info
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        # ========== AUTO-GENERATE ADMISSION NUMBER ==========
        try:
            admission_number = generate_admission_number(tenant_school)
            print(f"✅ Generated admission number: {admission_number}")
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Failed to generate admission number',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # ========== AUTO-GENERATE COLLEGE EMAIL & PASSWORD ==========
        try:
            college_email, plain_password = create_student_credentials(
                first_name,
                admission_number,
                tenant_school
            )
            print(f"✅ Generated college email: {college_email}")
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Failed to generate credentials',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # ========== VALIDATE CLASS & SECTION ==========
        try:
            current_class = Class.objects.get(id=data.get('current_class'))
        except Class.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid class'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            section = Section.objects.get(id=data.get('section'))
        except Section.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid section'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ========== VALIDATE ROLL NUMBER ==========
        roll_number = data.get('roll_number')
        try:
            roll_number = int(roll_number)
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'error': 'Invalid roll number'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if roll number already taken
        if Student.objects.filter(
            current_class=current_class,
            section=section,
            roll_number=roll_number,
            is_active=True
        ).exists():
            return Response({
                'success': False,
                'error': 'Roll number already taken',
                'details': f'Roll number {roll_number} is already assigned in this section'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ========== CREATE STUDENT ==========
        try:
            with transaction.atomic():
                # Create user with college email
                user = User.objects.create(
                    email=college_email,
                    username=college_email,
                    first_name=first_name,
                    last_name=last_name,
                    phone=data.get('phone', '').strip(),
                    user_type='student'
                )
                user.set_password(plain_password)
                user.save()
                
                # Create student
                student = Student.objects.create(
                    user=user,
                    college_email=college_email,
                    admission_number=admission_number,  # ✅ Auto-generated
                    admission_date=data.get('admission_date'),
                    date_of_birth=data.get('date_of_birth'),
                    gender=data.get('gender', '').strip().upper(),
                    blood_group=data.get('blood_group', '').strip(),
                    nationality=data.get('nationality', 'Indian').strip(),
                    religion=data.get('religion', '').strip(),
                    category=data.get('category', 'GEN').strip().upper(),
                    aadhaar_number=data.get('aadhaar_number', '').strip(),
                    address=data.get('address', '').strip(),
                    city=data.get('city', '').strip(),
                    state=data.get('state', '').strip(),
                    pincode=data.get('pincode', '').strip(),
                    emergency_contact=data.get('emergency_contact', '').strip(),
                    current_class=current_class,
                    section=section,
                    roll_number=roll_number,
                    father_name=data.get('father_name', '').strip(),
                    father_occupation=data.get('father_occupation', '').strip(),
                    father_phone=data.get('father_phone', '').strip(),
                    father_email=data.get('father_email', '').strip(),
                    mother_name=data.get('mother_name', '').strip(),
                    mother_occupation=data.get('mother_occupation', '').strip(),
                    mother_phone=data.get('mother_phone', '').strip(),
                    mother_email=data.get('mother_email', '').strip(),
                    guardian_name=data.get('guardian_name', '').strip(),
                    guardian_relation=data.get('guardian_relation', '').strip(),
                    guardian_phone=data.get('guardian_phone', '').strip(),
                    guardian_email=data.get('guardian_email', '').strip(),
                    medical_conditions=data.get('medical_conditions', '').strip(),
                    allergies=data.get('allergies', '').strip(),
                    regular_medications=data.get('regular_medications', '').strip(),
                    photo=request.FILES.get('photo'),
                    birth_certificate=request.FILES.get('birth_certificate'),
                    aadhaar_card=request.FILES.get('aadhaar_card')
                )
                
                # Create academic record
                current_session = SchoolSession.objects.filter(is_current=True).first()
                if current_session:
                    StudentAcademicRecord.objects.create(
                        student=student,
                        session=current_session,
                        class_enrolled=current_class,
                        section=section,
                        roll_number=student.roll_number,
                        status='NEW_ADMISSION'
                    )
                
                # SUCCESS: Return credentials
                return Response({
                    'success': True,
                    'message': 'Student created successfully',
                    'credentials': {
                        'admission_number': admission_number,  # ✅ Include admission number
                        'college_email': college_email,
                        'password': plain_password,
                        'note': 'Please save these credentials securely'
                    },
                    'data': StudentSerializer(student).data
                }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StudentListAPIView(APIView):
    """
    GET: List all students with filters, search, pagination
    
    Query Parameters:
    - class: Filter by class ID
    - section: Filter by section ID
    - is_active: Filter by active status (true/false)
    - search: Search by name, admission number, email
    - gender: Filter by gender (M/F/O)
    - blood_group: Filter by blood group
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - sort_by: Sort field (admission_number, name, roll_number, created_at)
    - sort_order: asc or desc (default: asc)
    
    Examples:
    - /api/students/
    - /api/students/?class=1&section=1
    - /api/students/?search=rahul
    - /api/students/?is_active=false
    - /api/students/?page=2&page_size=50
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def get(self, request):
        # ========== GET QUERY PARAMETERS ==========
        class_id = request.GET.get('class')
        section_id = request.GET.get('section')
        is_active_param = request.GET.get('is_active', 'true')
        search = request.GET.get('search', '').strip()
        gender = request.GET.get('gender', '').strip().upper()
        blood_group = request.GET.get('blood_group', '').strip()
        
        # Pagination
        try:
            page = int(request.GET.get('page', 1))
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            page = 1
        
        try:
            page_size = int(request.GET.get('page_size', 20))
            if page_size < 1:
                page_size = 20
            elif page_size > 100:  # Max limit
                page_size = 100
        except (ValueError, TypeError):
            page_size = 20
        
        # Sorting
        sort_by = request.GET.get('sort_by', 'roll_number')
        sort_order = request.GET.get('sort_order', 'asc')
        
        # ========== BUILD BASE QUERYSET ==========
        queryset = Student.objects.select_related(
            'user',
            'current_class',
            'section'
        ).all()
        
        # ========== APPLY FILTERS ==========
        
        # Filter by active status
        if is_active_param.lower() == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active_param.lower() == 'false':
            queryset = queryset.filter(is_active=False)
        # If not specified or 'all', show all
        
        # Filter by class
        if class_id:
            try:
                class_id = int(class_id)
                queryset = queryset.filter(current_class_id=class_id)
            except (ValueError, TypeError):
                return Response({
                    'success': False,
                    'error': 'Invalid class ID'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filter by section
        if section_id:
            try:
                section_id = int(section_id)
                queryset = queryset.filter(section_id=section_id)
            except (ValueError, TypeError):
                return Response({
                    'success': False,
                    'error': 'Invalid section ID'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filter by gender
        if gender and gender in ['M', 'F', 'O']:
            queryset = queryset.filter(gender=gender)
        
        # Filter by blood group
        if blood_group:
            queryset = queryset.filter(blood_group=blood_group)
        
        # ========== SEARCH ==========
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(admission_number__icontains=search) |
                Q(college_email__icontains=search) |
                Q(father_name__icontains=search) |
                Q(mother_name__icontains=search)
            )
        
        # ========== SORTING ==========
        valid_sort_fields = {
            'admission_number': 'admission_number',
            'name': 'user__first_name',
            'roll_number': 'roll_number',
            'created_at': 'created_at',
            'admission_date': 'admission_date'
        }
        
        sort_field = valid_sort_fields.get(sort_by, 'roll_number')
        
        if sort_order.lower() == 'desc':
            sort_field = f'-{sort_field}'
        
        # Default ordering: class -> section -> roll number
        queryset = queryset.order_by(
            'current_class__id',
            'section__id',
            sort_field
        )
        
        # ========== GET STATISTICS ==========
        total_count = queryset.count()
        
        # Get class/section wise count
        stats = {
            'total': total_count,
            'active': queryset.filter(is_active=True).count(),
            'inactive': queryset.filter(is_active=False).count(),
        }
        
        if class_id:
            stats['class_wise'] = {
                'male': queryset.filter(gender='M').count(),
                'female': queryset.filter(gender='F').count(),
                'other': queryset.filter(gender='O').count(),
            }
        
        # ========== PAGINATION ==========
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        paginated_students = queryset[start_index:end_index]
        
        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size
        
        # ========== SERIALIZE DATA ==========
        serializer = StudentListSerializer(
            paginated_students,
            many=True,
            context={'request': request}
        )
        
        # ========== RESPONSE ==========
        return Response({
            'success': True,
            'message': f'Retrieved {len(paginated_students)} students',
            'pagination': {
                'current_page': page,
                'page_size': page_size,
                'total_items': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1,
                'next_page': page + 1 if page < total_pages else None,
                'previous_page': page - 1 if page > 1 else None
            },
            'statistics': stats,
            'filters_applied': {
                'class': class_id,
                'section': section_id,
                'is_active': is_active_param,
                'search': search if search else None,
                'gender': gender if gender else None,
                'blood_group': blood_group if blood_group else None
            },
            'data': serializer.data
        }, status=status.HTTP_200_OK)



class StudentDetailAPIView(APIView):
    """
    GET: Get complete student profile with academic records and attendance summary
    
    URL: /api/students/{id}/
    
    Response includes:
    - Complete student profile
    - All academic records (session-wise)
    - Attendance summary (last 30 days)
    - Fee payment status (if fee module exists)
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def get(self, request, pk):
        try:
            # Get student with related data
            student = Student.objects.select_related(
                'user',
                'current_class',
                'section'
            ).get(pk=pk)
            
        except Student.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Student not found',
                'message': f'Student with ID {pk} does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # ========== STUDENT PROFILE DATA ==========
        serializer = StudentDetailSerializer(student, context={'request': request})
        
        # ========== ACADEMIC RECORDS ==========
        academic_records = StudentAcademicRecord.objects.filter(
            student=student
        ).select_related(
            'session',
            'class_enrolled',
            'section'
        ).order_by('-session__start_date')
        
        academic_records_data = StudentAcademicRecordSerializer(
            academic_records,
            many=True
        ).data
        
        # ========== ATTENDANCE SUMMARY (Last 30 Days) ==========
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        
        attendance_summary = {
            'period': 'Last 30 Days',
            'start_date': str(thirty_days_ago),
            'end_date': str(datetime.now().date()),
            'total_days': 0,
            'present': 0,
            'absent': 0,
            'late': 0,
            'half_day': 0,
            'attendance_percentage': 0
        }
        
        try:
            from attendance.models import Attendance
            
            attendances = Attendance.objects.filter(
                student=student,
                date__gte=thirty_days_ago
            )
            
            attendance_summary['total_days'] = attendances.count()
            attendance_summary['present'] = attendances.filter(status='P').count()
            attendance_summary['absent'] = attendances.filter(status='A').count()
            attendance_summary['late'] = attendances.filter(status='L').count()
            attendance_summary['half_day'] = attendances.filter(status='H').count()
            
            if attendance_summary['total_days'] > 0:
                attendance_summary['attendance_percentage'] = round(
                    (attendance_summary['present'] / attendance_summary['total_days']) * 100, 2
                )
        except Exception as e:
            # Attendance module might not exist
            attendance_summary['error'] = 'Attendance data not available'
        
        # ========== CURRENT SESSION ATTENDANCE ==========
        current_session_attendance = {
            'session_name': 'Current Session',
            'total_days': 0,
            'present': 0,
            'absent': 0,
            'attendance_percentage': 0
        }
        
        try:
            from schools.models import SchoolSession
            from attendance.models import Attendance
            
            current_session = SchoolSession.objects.filter(is_current=True).first()
            
            if current_session:
                session_attendances = Attendance.objects.filter(
                    student=student,
                    date__gte=current_session.start_date,
                    date__lte=current_session.end_date
                )
                
                current_session_attendance['session_name'] = current_session.name
                current_session_attendance['total_days'] = session_attendances.count()
                current_session_attendance['present'] = session_attendances.filter(status='P').count()
                current_session_attendance['absent'] = session_attendances.filter(status='A').count()
                
                if current_session_attendance['total_days'] > 0:
                    current_session_attendance['attendance_percentage'] = round(
                        (current_session_attendance['present'] / current_session_attendance['total_days']) * 100, 2
                    )
        except Exception as e:
            current_session_attendance['error'] = 'Session attendance data not available'
        
        # ========== FEE PAYMENT STATUS (Optional) ==========
        fee_summary = {
            'total_fee': 0,
            'paid': 0,
            'pending': 0,
            'last_payment_date': None
        }
        
        try:
            from fees.models import FeePayment
            
            fee_payments = FeePayment.objects.filter(student=student)
            
            if fee_payments.exists():
                from django.db.models import Sum
                
                total_paid = fee_payments.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
                fee_summary['paid'] = float(total_paid)
                
                last_payment = fee_payments.order_by('-payment_date').first()
                if last_payment:
                    fee_summary['last_payment_date'] = str(last_payment.payment_date)
        except Exception as e:
            # Fee module might not exist
            fee_summary['error'] = 'Fee data not available'
        
        # ========== STATISTICS ==========
        statistics = {
            'total_academic_records': academic_records.count(),
            'total_sessions_completed': academic_records.filter(
                status__in=['PROMOTED', 'PASSED_OUT']
            ).count(),
            'current_status': academic_records.first().status if academic_records.exists() else None,
            'years_in_school': academic_records.count()
        }
        
        # ========== RESPONSE ==========
        return Response({
            'success': True,
            'message': 'Student details retrieved successfully',
            'data': {
                'profile': serializer.data,
                'academic_records': academic_records_data,
                'attendance': {
                    'last_30_days': attendance_summary,
                    'current_session': current_session_attendance
                },
                'fee_summary': fee_summary,
                'statistics': statistics
            }
        }, status=status.HTTP_200_OK)





class StudentUpdateAPIView(APIView):
    """
    PATCH: Update student details
    
    URL: /api/students/{id}/update/
    
    Accepts:
    - JSON data
    - Form-data (for file uploads)
    
    Fields that can be updated:
    - Personal details (name, DOB, gender, blood group, etc.)
    - Contact information (address, phone, etc.)
    - Parent/Guardian information
    - Medical information
    - Academic information (class, section, roll number)
    
    Fields that CANNOT be updated:
    - admission_number (permanent)
    - college_email (permanent)
    - admission_date (permanent)
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def patch(self, request, pk):
        # ========== GET STUDENT ==========
        try:
            student = Student.objects.select_related('user').get(pk=pk)
        except Student.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Student not found',
                'message': f'Student with ID {pk} does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        data = request.data.copy()
        
        # ========== VALIDATE PROTECTED FIELDS ==========
        protected_fields = ['admission_number', 'college_email', 'admission_date']
        for field in protected_fields:
            if field in data:
                return Response({
                    'success': False,
                    'error': f'Cannot update {field}',
                    'message': f'{field} is a protected field and cannot be modified'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # ========== VALIDATE CLASS & SECTION (if provided) ==========
        if 'current_class' in data:
            try:
                new_class = Class.objects.get(id=data['current_class'])
            except Class.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Invalid class',
                    'message': 'Selected class does not exist'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if 'section' in data:
            try:
                new_section = Section.objects.get(id=data['section'])
            except Section.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Invalid section',
                    'message': 'Selected section does not exist'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if section belongs to class
            if 'current_class' in data:
                if new_section.class_obj_id != int(data['current_class']):
                    return Response({
                        'success': False,
                        'error': 'Invalid section',
                        'message': 'Section does not belong to the selected class'
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        # ========== VALIDATE ROLL NUMBER (if provided) ==========
        if 'roll_number' in data:
            try:
                new_roll = int(data['roll_number'])
            except (ValueError, TypeError):
                return Response({
                    'success': False,
                    'error': 'Invalid roll number',
                    'message': 'Roll number must be a valid number'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if roll number is already taken (in same class/section)
            class_id = data.get('current_class', student.current_class_id)
            section_id = data.get('section', student.section_id)
            
            duplicate = Student.objects.filter(
                current_class_id=class_id,
                section_id=section_id,
                roll_number=new_roll,
                is_active=True
            ).exclude(id=student.id).exists()
            
            if duplicate:
                return Response({
                    'success': False,
                    'error': 'Roll number already taken',
                    'message': f'Roll number {new_roll} is already assigned in this class/section'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # ========== UPDATE STUDENT ==========
        try:
            with transaction.atomic():
                # Update user fields if provided
                user = student.user
                user_updated = False
                
                if 'first_name' in data:
                    user.first_name = data.pop('first_name').strip()
                    user_updated = True
                
                if 'last_name' in data:
                    user.last_name = data.pop('last_name').strip()
                    user_updated = True
                
                if 'phone' in data:
                    user.phone = data.pop('phone', '').strip()
                    user_updated = True
                
                if user_updated:
                    user.save()
                
                # Update student using serializer
                serializer = StudentUpdateSerializer(
                    student,
                    data=data,
                    partial=True  # Allow partial updates
                )
                
                if serializer.is_valid():
                    serializer.save()
                    
                    # Return updated student details
                    detail_serializer = StudentDetailSerializer(
                        student,
                        context={'request': request}
                    )
                    
                    return Response({
                        'success': True,
                        'message': 'Student updated successfully',
                        'data': detail_serializer.data
                    }, status=status.HTTP_200_OK)
                
                else:
                    return Response({
                        'success': False,
                        'error': 'Validation error',
                        'details': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Update failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StudentDeactivateAPIView(APIView):
    """
    POST: Deactivate student (soft delete)
    
    URL: /api/students/{id}/deactivate/
    
    This will:
    - Set student.is_active = False
    - Set user.is_active = False
    - Student can be reactivated later
    - Data is preserved
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def post(self, request, pk):
        try:
            student = Student.objects.select_related('user').get(pk=pk)
        except Student.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Student not found',
                'message': f'Student with ID {pk} does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if already inactive
        if not student.is_active:
            return Response({
                'success': False,
                'error': 'Student already inactive',
                'message': f'Student {student.admission_number} is already deactivated'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Deactivate student
                student.is_active = False
                student.save()
                
                # Deactivate user account
                student.user.is_active = False
                student.user.save()
                
                return Response({
                    'success': True,
                    'message': 'Student deactivated successfully',
                    'data': {
                        'id': student.id,
                        'admission_number': student.admission_number,
                        'name': student.user.get_full_name(),
                        'is_active': student.is_active,
                        'deactivated_at': student.updated_at
                    }
                }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Deactivation failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentReactivateAPIView(APIView):
    """
    POST: Reactivate student
    
    URL: /api/students/{id}/reactivate/
    
    This will:
    - Set student.is_active = True
    - Set user.is_active = True
    - Restore student access
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def post(self, request, pk):
        try:
            student = Student.objects.select_related('user').get(pk=pk)
        except Student.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Student not found',
                'message': f'Student with ID {pk} does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if already active
        if student.is_active:
            return Response({
                'success': False,
                'error': 'Student already active',
                'message': f'Student {student.admission_number} is already active'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Reactivate student
                student.is_active = True
                student.save()
                
                # Reactivate user account
                student.user.is_active = True
                student.user.save()
                
                return Response({
                    'success': True,
                    'message': 'Student reactivated successfully',
                    'data': {
                        'id': student.id,
                        'admission_number': student.admission_number,
                        'name': student.user.get_full_name(),
                        'is_active': student.is_active,
                        'reactivated_at': student.updated_at
                    }
                }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Reactivation failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class ParentDetailAPIView(APIView):
    """
    GET: Get parent/guardian details of a student
    PATCH: Update parent/guardian details
    
    URL: /api/students/{student_id}/parents/
    
    Returns complete parent and guardian information
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    parser_classes = [JSONParser]
    
    def get(self, request, student_id):
        """Get parent/guardian details"""
        try:
            student = Student.objects.select_related(
                'user',
                'current_class',
                'section'
            ).get(pk=student_id)
        except Student.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Student not found',
                'message': f'Student with ID {student_id} does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Serialize parent details
        serializer = ParentDetailSerializer(student)
        
        # Additional parent statistics
        parent_stats = {
            'has_father_details': bool(student.father_name),
            'has_mother_details': bool(student.mother_name),
            'has_guardian_details': bool(student.guardian_name),
            'has_emergency_contact': bool(student.emergency_contact),
            'father_contact_available': bool(student.father_phone or student.father_email),
            'mother_contact_available': bool(student.mother_phone or student.mother_email),
        }
        
        # Format response with structured data
        response_data = {
            'student_info': {
                'id': student.id,
                'name': student.user.get_full_name(),
                'admission_number': student.admission_number,
                'class': student.current_class.display_name if student.current_class else None,
                'section': student.section.name if student.section else None,
            },
            'father': {
                'name': student.father_name,
                'occupation': student.father_occupation,
                'phone': student.father_phone,
                'email': student.father_email,
            },
            'mother': {
                'name': student.mother_name,
                'occupation': student.mother_occupation,
                'phone': student.mother_phone,
                'email': student.mother_email,
            },
            'guardian': {
                'name': student.guardian_name,
                'relation': student.guardian_relation,
                'phone': student.guardian_phone,
                'email': student.guardian_email,
            } if student.guardian_name else None,
            'emergency_contact': student.emergency_contact,
            'statistics': parent_stats
        }
        
        return Response({
            'success': True,
            'message': 'Parent details retrieved successfully',
            'data': response_data
        }, status=status.HTTP_200_OK)
    
    def patch(self, request, student_id):
        """Update parent/guardian details"""
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Student not found',
                'message': f'Student with ID {student_id} does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validate and update
        serializer = ParentUpdateSerializer(
            student,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    serializer.save()
                    
                    # Get updated details
                    updated_student = Student.objects.select_related(
                        'user',
                        'current_class',
                        'section'
                    ).get(pk=student_id)
                    
                    response_serializer = ParentDetailSerializer(updated_student)
                    
                    return Response({
                        'success': True,
                        'message': 'Parent details updated successfully',
                        'data': response_serializer.data
                    }, status=status.HTTP_200_OK)
            
            except Exception as e:
                return Response({
                    'success': False,
                    'error': 'Update failed',
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        else:
            return Response({
                'success': False,
                'error': 'Validation error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class ParentContactListAPIView(APIView):
    """
    GET: Get all parent contacts for a class/section
    
    URL: /api/students/parents/contacts/
    
    Query Parameters:
    - class: Filter by class ID
    - section: Filter by section ID
    
    Useful for sending bulk notifications to parents
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def get(self, request):
        class_id = request.GET.get('class')
        section_id = request.GET.get('section')
        
        # Build queryset
        queryset = Student.objects.filter(is_active=True).select_related(
            'user', 'current_class', 'section'
        )
        
        if class_id:
            queryset = queryset.filter(current_class_id=class_id)
        
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        
        # Extract parent contacts
        parent_contacts = []
        
        for student in queryset:
            contact = {
                'student_id': student.id,
                'student_name': student.user.get_full_name(),
                'admission_number': student.admission_number,
                'class': student.current_class.display_name if student.current_class else None,
                'section': student.section.name if student.section else None,
                'contacts': []
            }
            
            # Add father contact
            if student.father_name:
                contact['contacts'].append({
                    'relation': 'Father',
                    'name': student.father_name,
                    'phone': student.father_phone,
                    'email': student.father_email
                })
            
            # Add mother contact
            if student.mother_name:
                contact['contacts'].append({
                    'relation': 'Mother',
                    'name': student.mother_name,
                    'phone': student.mother_phone,
                    'email': student.mother_email
                })
            
            # Add guardian contact
            if student.guardian_name:
                contact['contacts'].append({
                    'relation': student.guardian_relation or 'Guardian',
                    'name': student.guardian_name,
                    'phone': student.guardian_phone,
                    'email': student.guardian_email
                })
            
            parent_contacts.append(contact)
        
        return Response({
            'success': True,
            'message': f'Retrieved {len(parent_contacts)} parent contacts',
            'count': len(parent_contacts),
            'data': parent_contacts
        }, status=status.HTTP_200_OK)

# ........................... Document Upload Apis View...................................................#

def get_document_description(doc_type):
    """Get description for each document type"""
    descriptions = {
        'BIRTH': 'Birth certificate issued by municipal authority',
        'AADHAAR': 'Aadhaar card or UID number proof',
        'TRANSFER': 'Transfer certificate from previous school',
        'MEDICAL': 'Medical fitness certificate or health records',
        'CAST': 'Caste certificate for reservation benefits',
        'INCOME': 'Income certificate for fee concession',
        'PHOTO': 'Recent passport size photograph',
        'OTHER': 'Any other relevant document'
    }
    return descriptions.get(doc_type, '')



class DocumentTypesAPIView(APIView):
    """
    GET: Get all available document types
    
    URL: /api/students/documents/types/
    
    Returns:
    - List of all document types
    - Display names
    - Required status
    - Document type codes
    
    No authentication required for this endpoint (can be public)
    """
    permission_classes = [IsAuthenticated]  # Remove if you want it public
    
    def get(self, request):
        """Get all document types with metadata"""
        
        # Define required documents
        required_document_types = ['BIRTH', 'AADHAAR', 'PHOTO']
        
        # Build document types list
        document_types = []
        
        for doc_type, doc_display_name in StudentDocument.DOCUMENT_TYPES:
            document_types.append({
                'type': doc_type,
                'display_name': doc_display_name,
                'is_required': doc_type in required_document_types,
                'description': get_document_description(doc_type)
            })
        
        return Response({
            'success': True,
            'message': f'Retrieved {len(document_types)} document types',
            'count': len(document_types),
            'data': document_types
        }, status=status.HTTP_200_OK)




class StudentDocumentUploadAPIView(APIView):
    """
    POST: Upload document for a student
    
    URL: /api/students/{student_id}/documents/upload/
    
    Headers:
    - Tenant-Name: School code (e.g., BFA01) - Set during login
    - Authorization: Bearer token
    
    Form Data:
    - document_type: Document type (BIRTH, AADHAAR, etc.)
    - title: Document title (optional - auto-generated if not provided)
    - file: File to upload (PDF, JPG, PNG - max 5MB)
    - description: Optional description
    
    File Storage Path:
    students/documents/{school_code}/{school_name}/{document_type}/{admission_number}/{filename}_{timestamp}.ext
    
    Example:
    students/documents/BFA01/BFA_School/Birth_Certificate/BFA01_ADM_0001/Birth_Certificate_20251207_223045.pdf
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, student_id):
        # ========== GET TENANT INFO FROM HEADER ==========
        tenant_name = request.headers.get('Tenant-Name')
        
        if not tenant_name:
            return Response({
                'success': False,
                'error': 'Missing tenant header',
                'message': 'Tenant-Name header is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get school by school_code (tenant is already set by middleware during login)
        try:
            school = School.objects.get(school_code=tenant_name)
        except School.DoesNotExist:
            return Response({
                'success': False,
                'error': 'School not found',
                'message': f'School with code {tenant_name} does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # ========== GET STUDENT ==========
        try:
            student = Student.objects.select_related('user').get(pk=student_id)
        except Student.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Student not found',
                'message': f'Student with ID {student_id} does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if student is active
        if not student.is_active:
            return Response({
                'success': False,
                'error': 'Student inactive',
                'message': 'Cannot upload documents for inactive student'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ========== VALIDATE FILE ==========
        if 'file' not in request.FILES:
            return Response({
                'success': False,
                'error': 'No file uploaded',
                'message': 'Please provide a file to upload'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        file_extension = os.path.splitext(file.name)[1].lower()
        
        # Check file extension
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        if file_extension not in allowed_extensions:
            return Response({
                'success': False,
                'error': 'Invalid file type',
                'message': f'File must be one of: {", ".join(allowed_extensions)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if file.size > max_size:
            return Response({
                'success': False,
                'error': 'File too large',
                'message': f'File size must not exceed 5MB. Current: {file.size / (1024*1024):.2f}MB'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ========== VALIDATE DOCUMENT TYPE ==========
        document_type = request.data.get('document_type', '').upper()
        
        if not document_type:
            return Response({
                'success': False,
                'error': 'Missing document type',
                'message': 'document_type field is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        valid_types = [choice[0] for choice in StudentDocument.DOCUMENT_TYPES]
        if document_type not in valid_types:
            return Response({
                'success': False,
                'error': 'Invalid document type',
                'message': f'Valid types: {", ".join(valid_types)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ========== CHECK DUPLICATE (For single-upload types) ==========
        single_document_types = ['BIRTH', 'AADHAAR']
        if document_type in single_document_types:
            existing = StudentDocument.objects.filter(
                student=student,
                document_type=document_type,
                is_active=True
            ).exists()
            
            if existing:
                document_type_display = dict(StudentDocument.DOCUMENT_TYPES)[document_type]
                return Response({
                    'success': False,
                    'error': 'Duplicate document',
                    'message': f'{document_type_display} already exists for this student. Delete existing one first.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # ========== PREPARE DATA ==========
        data = request.data.copy()
        data['student'] = student.id
        data['uploaded_by'] = request.user.id
        data['document_type'] = document_type
        
        # Auto-generate title if not provided
        if not data.get('title'):
            document_type_display = dict(StudentDocument.DOCUMENT_TYPES).get(
                document_type, 
                'Document'
            )
            data['title'] = f"{document_type_display} - {student.user.get_full_name()}"
        
        # ========== VALIDATE & SAVE ==========
        serializer = StudentDocumentUploadSerializer(data=data)
        
        if serializer.is_valid():
            try:
                # Save document (file path will be auto-generated by upload_to_path)
                document = serializer.save()
                
                # Return success response with document details
                response_serializer = StudentDocumentSerializer(
                    document,
                    context={'request': request}
                )
                
                return Response({
                    'success': True,
                    'message': 'Document uploaded successfully',
                    'data': response_serializer.data,
                    'file_info': {
                        'original_filename': file.name,
                        'saved_path': document.file.name,
                        'file_size': file.size,
                        'file_size_mb': round(file.size / (1024 * 1024), 2),
                        'file_extension': file_extension,
                        'school_code': school.school_code,
                        'school_name': school.name,
                        'student_admission_number': student.admission_number
                    }
                }, status=status.HTTP_201_CREATED)
            
            except Exception as e:
                return Response({
                    'success': False,
                    'error': 'Upload failed',
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        else:
            return Response({
                'success': False,
                'error': 'Validation error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)















































class StudentDocumentUpdateAPIView(APIView):
    """
    PATCH: Update document (title, description, and file)
    
    URL: /api/students/{student_id}/documents/{document_id}/update/
    
    Form Data:
    - title: Updated title (optional)
    - description: Updated description (optional)
    - file: New file to replace (optional)
    
    You can update any combination:
    - Only title
    - Only description
    - Only file
    - Title + Description
    - Title + File
    - Description + File
    - All three
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    parser_classes = [MultiPartParser, FormParser]
    
    def patch(self, request, student_id, document_id):
        # ========== GET DOCUMENT ==========
        try:
            document = StudentDocument.objects.select_related(
                'student',
                'student__user'
            ).get(
                pk=document_id,
                student_id=student_id,
                is_active=True
            )
        except StudentDocument.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Document not found',
                'message': f'Document with ID {document_id} does not exist for this student'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # ========== PREPARE UPDATE DATA ==========
        has_update = False
        
        # Get title if provided
        title = request.data.get('title')
        if title:
            has_update = True
        
        # Get description if provided
        description = request.data.get('description')
        if description:
            has_update = True
        
        # Get file if provided
        new_file = request.FILES.get('file')
        if new_file:
            has_update = True
            
            # Validate file extension
            file_extension = os.path.splitext(new_file.name)[1].lower()
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
            
            if file_extension not in allowed_extensions:
                return Response({
                    'success': False,
                    'error': 'Invalid file type',
                    'message': f'File must be one of: {", ".join(allowed_extensions)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check file size (max 5MB)
            max_size = 5 * 1024 * 1024
            if new_file.size > max_size:
                return Response({
                    'success': False,
                    'error': 'File too large',
                    'message': f'File size must not exceed 5MB. Current: {new_file.size / (1024*1024):.2f}MB'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if at least one field is provided
        if not has_update:
            return Response({
                'success': False,
                'error': 'No data to update',
                'message': 'Please provide at least one field to update (title, description, or file)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ========== UPDATE DOCUMENT ==========
        try:
            with transaction.atomic():
                # Store old file path for deletion
                old_file_path = None
                if new_file and document.file:
                    old_file_path = document.file.path
                
                # Update fields
                if title:
                    document.title = title
                
                if description is not None:  # Allow empty string
                    document.description = description
                
                if new_file:
                    document.file = new_file
                    document.uploaded_by = request.user
                
                # Save document
                document.save()
                
                # Delete old file if new file was uploaded
                if old_file_path and os.path.exists(old_file_path):
                    try:
                        os.remove(old_file_path)
                    except Exception as e:
                        # Log error but don't fail the request
                        print(f"Failed to delete old file: {e}")
                
                # Refresh from database
                document.refresh_from_db()
                
                # Serialize and return
                serializer = StudentDocumentSerializer(
                    document,
                    context={'request': request}
                )
                
                updated_fields = []
                if title:
                    updated_fields.append('title')
                if description is not None:
                    updated_fields.append('description')
                if new_file:
                    updated_fields.append('file')
                
                return Response({
                    'success': True,
                    'message': f'Document updated successfully',
                    'updated_fields': updated_fields,
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Update failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StudentDocumentReplaceAPIView(APIView):
    """
    PUT: Replace document file with new one
    
    URL: /api/students/{student_id}/documents/{document_id}/replace/
    
    Form Data:
    - file: New file to upload
    
    Keeps same title, description, document_type
    Deletes old file and uploads new one
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    parser_classes = [MultiPartParser, FormParser]
    
    def put(self, request, student_id, document_id):
        tenant_name = request.headers.get('Tenant-Name')
        
        if not tenant_name:
            return Response({
                'success': False,
                'error': 'Missing tenant header'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get school
        try:
            school = School.objects.get(school_code=tenant_name)
        except School.DoesNotExist:
            return Response({
                'success': False,
                'error': 'School not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get document
        try:
            document = StudentDocument.objects.select_related(
                'student',
                'student__user'
            ).get(
                pk=document_id,
                student_id=student_id,
                is_active=True
            )
        except StudentDocument.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Document not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validate file
        if 'file' not in request.FILES:
            return Response({
                'success': False,
                'error': 'No file uploaded'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = StudentDocumentReplaceSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # Delete old file
                    old_file_path = document.file.path if document.file else None
                    
                    # Save new file
                    document.file = request.FILES['file']
                    document.uploaded_by = request.user
                    document.upload_date = datetime.now()
                    document.save()
                    
                    # Delete old file from storage
                    if old_file_path and os.path.exists(old_file_path):
                        try:
                            os.remove(old_file_path)
                        except:
                            pass
                    
                    # Return updated document
                    response_serializer = StudentDocumentSerializer(
                        document,
                        context={'request': request}
                    )
                    
                    return Response({
                        'success': True,
                        'message': 'Document file replaced successfully',
                        'data': response_serializer.data
                    }, status=status.HTTP_200_OK)
            
            except Exception as e:
                return Response({
                    'success': False,
                    'error': 'Replace failed',
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        else:
            return Response({
                'success': False,
                'error': 'Validation error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class StudentDocumentDeleteAPIView(APIView):
    """
    DELETE: Delete document (soft delete by default)
    
    URL: /api/students/{student_id}/documents/{document_id}/delete/
    
    Query Parameters:
    - permanent=true : Hard delete (removes file from storage)
    
    Default: Soft delete (sets is_active=False)
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def delete(self, request, student_id, document_id):
        # Get document
        try:
            document = StudentDocument.objects.select_related(
                'student',
                'student__user'
            ).get(
                pk=document_id,
                student_id=student_id
            )
        except StudentDocument.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Document not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if permanent delete
        permanent = request.GET.get('permanent', 'false').lower() == 'true'
        
        try:
            document_info = {
                'id': document.id,
                'document_type': document.get_document_type_display(),
                'title': document.title,
                'student_name': document.student.user.get_full_name()
            }
            
            if permanent:
                # Hard delete - remove file from storage
                file_path = document.file.path if document.file else None
                
                document.delete()
                
                # Delete file from storage
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
                
                return Response({
                    'success': True,
                    'message': 'Document deleted permanently',
                    'deleted_document': document_info
                }, status=status.HTTP_200_OK)
            
            else:
                # Soft delete
                document.is_active = False
                document.save()
                
                return Response({
                    'success': True,
                    'message': 'Document deactivated successfully',
                    'data': document_info,
                    'note': 'Document is soft-deleted. Use permanent=true to delete permanently.'
                }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Delete failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentDocumentDownloadAPIView(APIView):
    """
    GET: Download document file
    
    URL: /api/students/{student_id}/documents/{document_id}/download/
    
    Returns file with proper Content-Disposition header for download
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def get(self, request, student_id, document_id):
        # Get document
        try:
            document = StudentDocument.objects.get(
                pk=document_id,
                student_id=student_id,
                is_active=True
            )
        except StudentDocument.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Document not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if file exists
        if not document.file:
            return Response({
                'success': False,
                'error': 'No file attached to this document'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            file_path = document.file.path
            
            if not os.path.exists(file_path):
                return Response({
                    'success': False,
                    'error': 'File not found on server'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get file info
            file_name = os.path.basename(file_path)
            
            # Open file and return as response
            file_handle = open(file_path, 'rb')
            response = FileResponse(file_handle)
            
            # Set headers for download
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            
            return response
        
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Download failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentDocumentBulkUploadAPIView(APIView):
    """
    POST: Upload multiple documents at once
    
    URL: /api/students/{student_id}/documents/bulk-upload/
    
    Form Data:
    - documents[]: Multiple files
    - document_types[]: Corresponding document types (same order)
    - titles[]: Optional titles (same order)
    - descriptions[]: Optional descriptions (same order)
    
    Example:
    documents[0]: birth_cert.pdf
    documents[1]: aadhaar.pdf
    documents[2]: photo.jpg
    document_types[0]: BIRTH
    document_types[1]: AADHAAR
    document_types[2]: PHOTO
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, student_id):
        tenant_name = request.headers.get('Tenant-Name')
        
        if not tenant_name:
            return Response({
                'success': False,
                'error': 'Missing tenant header'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get school
        try:
            school = School.objects.get(school_code=tenant_name)
        except School.DoesNotExist:
            return Response({
                'success': False,
                'error': 'School not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get student
        try:
            student = Student.objects.select_related('user').get(pk=student_id)
        except Student.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Student not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get files and metadata
        documents = request.FILES.getlist('documents')
        document_types = request.data.getlist('document_types')
        titles = request.data.getlist('titles', [])
        descriptions = request.data.getlist('descriptions', [])
        
        if not documents:
            return Response({
                'success': False,
                'error': 'No documents uploaded'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(documents) != len(document_types):
            return Response({
                'success': False,
                'error': 'Mismatch in documents and document types count'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Process each document
        results = {
            'success': [],
            'failed': []
        }
        
        for idx, (file, doc_type) in enumerate(zip(documents, document_types)):
            try:
                # Prepare data
                data = {
                    'student': student.id,
                    'document_type': doc_type.upper(),
                    'file': file,
                    'uploaded_by': request.user.id,
                    'title': titles[idx] if idx < len(titles) else f"{doc_type} - {student.user.get_full_name()}",
                    'description': descriptions[idx] if idx < len(descriptions) else ''
                }
                
                # Validate and save
                serializer = StudentDocumentUploadSerializer(data=data)
                
                if serializer.is_valid():
                    document = serializer.save()
                    results['success'].append({
                        'file_name': file.name,
                        'document_type': doc_type,
                        'document_id': document.id,
                        'message': 'Uploaded successfully'
                    })
                else:
                    results['failed'].append({
                        'file_name': file.name,
                        'document_type': doc_type,
                        'errors': serializer.errors
                    })
            
            except Exception as e:
                results['failed'].append({
                    'file_name': file.name,
                    'document_type': doc_type,
                    'error': str(e)
                })
        
        # Return summary
        return Response({
            'success': True if results['success'] else False,
            'message': f"Uploaded {len(results['success'])} of {len(documents)} documents",
            'summary': {
                'total': len(documents),
                'success_count': len(results['success']),
                'failed_count': len(results['failed'])
            },
            'results': results
        }, status=status.HTTP_201_CREATED if results['success'] else status.HTTP_400_BAD_REQUEST)


class StudentDocumentListAPIView(APIView):
    """
    GET: Get all documents of a student (Simple response)
    
    URL: /api/students/{student_id}/documents/
    
    Query Parameters:
    - document_type: Filter by document type (BIRTH, AADHAAR, etc.)
    - is_active: Filter by active status (true/false/all) - default: true
    
    Returns only the list of documents
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def get(self, request, student_id):
        # ========== GET STUDENT ==========
        try:
            student = Student.objects.select_related('user').get(pk=student_id)
        except Student.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Student not found',
                'message': f'Student with ID {student_id} does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # ========== GET QUERY PARAMS ==========
        document_type_filter = request.GET.get('document_type', '').upper()
        is_active_filter = request.GET.get('is_active', 'true').lower()
        
        # ========== BUILD QUERYSET ==========
        queryset = StudentDocument.objects.filter(student=student)
        
        # Filter by active status
        if is_active_filter == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active_filter == 'false':
            queryset = queryset.filter(is_active=False)
        # If 'all', don't filter
        
        # Filter by document type if provided
        if document_type_filter:
            valid_types = [choice[0] for choice in StudentDocument.DOCUMENT_TYPES]
            if document_type_filter in valid_types:
                queryset = queryset.filter(document_type=document_type_filter)
            else:
                return Response({
                    'success': False,
                    'error': 'Invalid document type',
                    'message': f'Valid types: {", ".join(valid_types)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Order by upload date (newest first)
        queryset = queryset.select_related('uploaded_by').order_by('-upload_date')
        
        # ========== SERIALIZE DOCUMENTS ==========
        serializer = StudentDocumentSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        
        # ========== SIMPLE RESPONSE ==========
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)



class AdminMarkAttendanceAPIView(APIView):
    """
    POST: Admin marks attendance for any class/section/subject/period
    
    URL: /api/admin/attendance/mark/
    
    Headers:
    - Tenant-Name: BFA01
    - Authorization: Bearer TOKEN
    
    Body (JSON):
    {
        "date": "2025-12-08",
        "class_id": 5,
        "section_id": 1,
        "subject_id": 3,
        "period_number": 2,
        "timetable_id": 15,
        "attendance": [
            {"student_id": 1, "status": "P"},
            {"student_id": 2, "status": "A", "remarks": "Sick leave"},
            {"student_id": 3, "status": "L", "remarks": "Came late"},
            {"student_id": 4, "status": "P"}
        ]
    }
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def post(self, request):
        # ========== CHECK ADMIN PERMISSION ==========
        if request.user.user_type not in ['school_admin', 'principal']:
            return Response({
                'success': False,
                'error': 'Permission denied',
                'message': 'Only school admin or principal can mark attendance'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # ========== VALIDATE REQUEST DATA ==========
        serializer = AdminMarkAttendanceSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Validation error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        
        # ========== GET CURRENT SESSION ==========
        try:
            current_session = SchoolSession.objects.get(is_current=True)
        except SchoolSession.DoesNotExist:
            return Response({
                'success': False,
                'error': 'No active session',
                'message': 'Please activate an academic session first'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ========== GET TIMETABLE IF PROVIDED ==========
        timetable = None
        if validated_data.get('timetable_id'):
            try:
                timetable = TimeTable.objects.get(
                    id=validated_data['timetable_id'],
                    is_active=True
                )
            except TimeTable.DoesNotExist:
                pass
        
        # ========== MARK ATTENDANCE ==========
        try:
            with transaction.atomic():
                attendance_records = []
                
                for attendance_item in validated_data['attendance']:
                    student = validated_data['students'].get(id=attendance_item['student_id'])
                    
                    # Check if attendance already exists
                    existing = StudentAttendance.objects.filter(
                        student=student,
                        date=validated_data['date'],
                        subject=validated_data['subject'],
                        period_number=validated_data['period_number']
                    ).first()
                    
                    if existing:
                        # Update existing attendance
                        existing.status = attendance_item['status']
                        existing.remarks = attendance_item.get('remarks', '')
                        existing.marked_by = request.user
                        existing.marked_at = datetime.now()
                        existing.save()
                        attendance_records.append(existing)
                    else:
                        # Create new attendance
                        attendance = StudentAttendance.objects.create(
                            student=student,
                            date=validated_data['date'],
                            class_obj=validated_data['class_obj'],
                            section=validated_data['section'],
                            subject=validated_data['subject'],
                            period_number=validated_data['period_number'],
                            timetable=timetable,
                            status=attendance_item['status'],
                            remarks=attendance_item.get('remarks', ''),
                            marked_by=request.user,
                            marked_at=datetime.now(),
                            session=current_session
                        )
                        attendance_records.append(attendance)
                
                # ========== SERIALIZE RESPONSE ==========
                response_serializer = StudentAttendanceDetailSerializer(
                    attendance_records,
                    many=True
                )
                
                # ========== CALCULATE SUMMARY ==========
                summary = {
                    'total_students': len(attendance_records),
                    'present': len([a for a in attendance_records if a.status == 'P']),
                    'absent': len([a for a in attendance_records if a.status == 'A']),
                    'late': len([a for a in attendance_records if a.status == 'L']),
                    'half_day': len([a for a in attendance_records if a.status == 'H']),
                    'excused': len([a for a in attendance_records if a.status == 'E']),
                }
                
                return Response({
                    'success': True,
                    'message': f'Attendance marked successfully for {len(attendance_records)} students',
                    'data': {
                        'date': str(validated_data['date']),
                        'class': validated_data['class_obj'].display_name,
                        'section': validated_data['section'].name,
                        'subject': validated_data['subject'].name,
                        'period': validated_data['period_number'],
                        'summary': summary,
                        'attendance': response_serializer.data
                    }
                }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Failed to mark attendance',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminBulkMarkAttendanceAPIView(APIView):
    """
    POST: Mark all students present/absent at once
    
    URL: /api/admin/attendance/bulk-mark/
    
    Body:
    {
        "date": "2025-12-08",
        "class_id": 5,
        "section_id": 1,
        "subject_id": 3,
        "period_number": 2,
        "mark_all_as": "P"
    }
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def post(self, request):
        if request.user.user_type not in ['school_admin', 'principal']:
            return Response({
                'success': False,
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = BulkAttendanceSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Validation error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            # Get class and section
            class_obj = Class.objects.get(id=data['class_id'], is_active=True)
            section = Section.objects.get(id=data['section_id'], class_obj=class_obj, is_active=True)
            subject = Subject.objects.get(id=data['subject_id'], is_active=True)
            
            # Get all students in class/section
            students = Student.objects.filter(
                current_class=class_obj,
                section=section,
                is_active=True
            )
            
            if not students.exists():
                return Response({
                    'success': False,
                    'error': 'No students found in this class/section'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get current session
            current_session = SchoolSession.objects.get(is_current=True)
            
            # Mark all students
            with transaction.atomic():
                attendance_records = []
                status_to_mark = data.get('mark_all_as', 'P')
                
                for student in students:
                    attendance, created = StudentAttendance.objects.update_or_create(
                        student=student,
                        date=data['date'],
                        subject=subject,
                        period_number=data['period_number'],
                        defaults={
                            'class_obj': class_obj,
                            'section': section,
                            'status': status_to_mark,
                            'marked_by': request.user,
                            'marked_at': datetime.now(),
                            'session': current_session
                        }
                    )
                    attendance_records.append(attendance)
                
                return Response({
                    'success': True,
                    'message': f'Marked {len(attendance_records)} students as {status_to_mark}',
                    'data': {
                        'total_students': len(attendance_records),
                        'status': status_to_mark,
                        'date': str(data['date']),
                        'class': class_obj.display_name,
                        'section': section.name,
                        'subject': subject.name,
                        'period': data['period_number']
                    }
                }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Failed to mark bulk attendance',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminGetAttendanceAPIView(APIView):
    """
    GET: Get attendance for specific class/section/date
    
    URL: /api/admin/attendance/?date=2025-12-08&class_id=5&section_id=1&subject_id=3&period=2
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def get(self, request):
        # Get query parameters
        date_str = request.GET.get('date')
        class_id = request.GET.get('class_id')
        section_id = request.GET.get('section_id')
        subject_id = request.GET.get('subject_id')
        period = request.GET.get('period')
        
        if not all([date_str, class_id, section_id]):
            return Response({
                'success': False,
                'error': 'Missing parameters',
                'message': 'date, class_id, and section_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'success': False,
                'error': 'Invalid date format',
                'message': 'Date must be in YYYY-MM-DD format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Build query
        queryset = StudentAttendance.objects.filter(
            date=attendance_date,
            class_obj_id=class_id,
            section_id=section_id
        ).select_related('student', 'student__user', 'subject', 'marked_by')
        
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        
        if period:
            queryset = queryset.filter(period_number=period)
        
        queryset = queryset.order_by('period_number', 'student__admission_number')
        
        # Serialize
        serializer = StudentAttendanceDetailSerializer(queryset, many=True)
        
        # Calculate summary
        summary = {
            'total_records': queryset.count(),
            'present': queryset.filter(status='P').count(),
            'absent': queryset.filter(status='A').count(),
            'late': queryset.filter(status='L').count(),
            'half_day': queryset.filter(status='H').count(),
            'excused': queryset.filter(status='E').count(),
        }
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'summary': summary,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

from .id_card_service import IDCardDataExtractor
from .id_card_config import TEMPLATE_CONFIGS, ALL_AVAILABLE_FIELDS




class GenerateStudentIDCardAPIView(APIView):
    """
    POST: Generate student ID card data
    
    URL: /api/students/id-cards/generate/
    
    Request:
    {
        "template_name": "template_3",
        "student_ids": [1, 2, 3],
        "issue_date": "2025-12-09",
        "valid_till": "2026-12-09"
    }
    
    Response for Single Page Template:
    {
        "success": true,
        "count": 3,
        "template": {
            "name": "template_1",
            "type": "single"
        },
        "data": [
            {
                "student_id": 1,
                "card_number": "ID20250001",
                "template_type": "single",
                "data": {
                    "photo_url": "/media/...",
                    "name": "John Doe",
                    ...
                }
            }
        ]
    }
    
    Response for Front & Back Template:
    {
        "success": true,
        "count": 3,
        "template": {
            "name": "template_3",
            "type": "front_and_back"
        },
        "data": [
            {
                "student_id": 1,
                "card_number": "ID20250001",
                "template_type": "front_and_back",
                "front": {
                    "photo_url": "/media/...",
                    "name": "John Doe",
                    ...
                },
                "back": {
                    "school_name": "ABC School",
                    "school_address": "...",
                    "principal_signature": "/media/...",
                    ...
                }
            }
        ]
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # ========== STEP 1: VALIDATE REQUEST ==========
        serializer = GenerateIDCardRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Validation error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        template_name = validated_data['template_name']
        student_ids = validated_data['student_ids']
        
        # ========== STEP 2: GET TEMPLATE CONFIG ==========
        template_config = TEMPLATE_CONFIGS.get(template_name)
        
        if not template_config:
            return Response({
                'success': False,
                'error': 'Invalid template'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        template_type = template_config['type']  # 'single' or 'front_and_back'
        
        # ========== STEP 3: GET STUDENTS ==========
        students = Student.objects.filter(
            id__in=student_ids,
            is_active=True
        ).select_related('user', 'current_class', 'section')
        
        if students.count() != len(student_ids):
            return Response({
                'success': False,
                'error': 'Some students not found or inactive'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # ========== STEP 4: GET SCHOOL & SESSION ==========
        try:
            school = School.objects.first()
        except School.DoesNotExist:
            return Response({
                'success': False,
                'error': 'School not configured'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            session = SchoolSession.objects.get(is_current=True)
        except SchoolSession.DoesNotExist:
            return Response({
                'success': False,
                'error': 'No active session'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ========== STEP 5: SET CARD DATES ==========
        issue_date = validated_data.get('issue_date', date.today())
        valid_till = validated_data.get('valid_till', issue_date + timedelta(days=365))
        
        # ========== STEP 6: GENERATE CARDS ==========
        cards_data = []
        
        for student in students:
            try:
                # Initialize extractor
                extractor = IDCardDataExtractor(student, school, session)
                
                # Generate card number
                card_number = extractor.generate_card_number()
                
                # Prepare card info
                card_info = {
                    'card_number': card_number,
                    'issue_date': issue_date,
                    'valid_till': valid_till
                }
                extractor.card_data = card_info
                
                # ========== SINGLE PAGE TEMPLATE ==========
                if template_type == 'single':
                    # Extract all fields
                    fields_to_extract = template_config['fields']
                    card_data = extractor.extract_fields(fields_to_extract)
                    
                    # Add card info
                    card_data['card_number'] = card_number
                    card_data['issue_date'] = issue_date.strftime('%d/%m/%Y')
                    card_data['valid_till'] = valid_till.strftime('%d/%m/%Y')
                    
                    # Append to response
                    cards_data.append({
                        'student_id': student.id,
                        'card_number': card_number,
                        'template_type': 'single',
                        'data': card_data
                    })
                
                # ========== FRONT & BACK TEMPLATE ==========
                elif template_type == 'front_and_back':
                    # Extract front side fields
                    front_fields = template_config['front_fields']
                    front_data = extractor.extract_fields(front_fields)
                    
                    # Add card info to front
                    front_data['card_number'] = card_number
                    front_data['issue_date'] = issue_date.strftime('%d/%m/%Y')
                    front_data['valid_till'] = valid_till.strftime('%d/%m/%Y')
                    
                    # Extract back side fields
                    back_fields = template_config['back_fields']
                    back_data = extractor.extract_fields(back_fields)
                    
                    # Append to response
                    cards_data.append({
                        'student_id': student.id,
                        'card_number': card_number,
                        'template_type': 'front_and_back',
                        'front': front_data,
                        'back': back_data
                    })
            
            except Exception as e:
                print(f"Error generating card for student {student.id}: {str(e)}")
                continue
        
        # ========== STEP 7: RETURN RESPONSE ==========
        return Response({
            'success': True,
            'count': len(cards_data),
            'template': {
                'name': template_name,
                'display_name': template_config['name'],
                'type': template_type,
                'description': template_config['description']
            },
            'data': cards_data
        }, status=status.HTTP_200_OK)


class GetAvailableTemplatesAPIView(APIView):
    """
    GET: Get all available templates with their configurations
    
    URL: /api/students/id-cards/templates/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        templates = []
        
        for template_name, config in TEMPLATE_CONFIGS.items():
            templates.append({
                'template_name': template_name,
                'display_name': config['name'],
                'description': config['description'],
                'type': config['type'],
                'has_back_side': config['type'] == 'front_and_back'
            })
        
        return Response({
            'success': True,
            'count': len(templates),
            'data': templates
        }, status=status.HTTP_200_OK)


class GetAvailableFieldsAPIView(APIView):
    """
    GET: Get all available fields
    
    URL: /api/students/id-cards/available-fields/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            'success': True,
            'data': {
                'fields': ALL_AVAILABLE_FIELDS,
                'templates': TEMPLATE_CONFIGS
            }
        }, status=status.HTTP_200_OK)



































#not Use
class StudentRetrieveAPIView(APIView):
    """GET: Retrieve a single student (admin view)"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def get(self, request, pk):
        try:
            student = Student.objects.select_related(
                'user', 'current_class', 'section'
            ).get(pk=pk)
        except Student.DoesNotExist:
            return Response(
                {"error": "Student not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = StudentDetailSerializer(student)
        return Response(serializer.data, status=status.HTTP_200_OK)

class StudentSoftDeleteAPIView(APIView):
    """DELETE: Soft delete student (is_active = False)"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def delete(self, request, pk):
        try:
            student = Student.objects.get(pk=pk)
        except Student.DoesNotExist:
            return Response(
                {"error": "Student not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        student.is_active = False
        student.save()
        return Response(
            {"message": "Student deactivated successfully"},
            status=status.HTTP_200_OK,
        )


class StudentHardDeleteAPIView(APIView):
    """DELETE: Permanently delete student + user"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def delete(self, request, pk):
        try:
            student = Student.objects.get(pk=pk)
        except Student.DoesNotExist:
            return Response(
                {"error": "Student not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = student.user
        student.delete()
        user.delete()
        return Response(
            {"message": "Student and user account deleted permanently"},
            status=status.HTTP_204_NO_CONTENT,
        )


class StudentSearchAPIView(APIView):
    """
    GET: Quick search (active students) – by name, email, phone, parents, admission no.
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def get(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Search query is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        students = Student.objects.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(admission_number__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__phone__icontains=query) |
            Q(father_name__icontains=query) |
            Q(mother_name__icontains=query) |
            Q(father_phone__icontains=query) |
            Q(mother_phone__icontains=query)
        ).filter(is_active=True)[:20]

        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# PARENT / GUARDIAN ADMIN APIs
# ============================================================

class ParentDetailAPIView(APIView):
    """GET/PUT: View & update parent/guardian details (admin side)"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def get(self, request, student_id):
        student = get_object_or_404(Student, id=student_id)
        parent_data = {
            'father_name': student.father_name,
            'father_occupation': student.father_occupation,
            'father_phone': student.father_phone,
            'father_email': student.father_email,
            'mother_name': student.mother_name,
            'mother_occupation': student.mother_occupation,
            'mother_phone': student.mother_phone,
            'mother_email': student.mother_email,
            'guardian_name': student.guardian_name,
            'guardian_relation': student.guardian_relation,
            'guardian_phone': student.guardian_phone,
            'guardian_email': student.guardian_email,
        }
        return Response(parent_data, status=status.HTTP_200_OK)

    def put(self, request, student_id):
        student = get_object_or_404(Student, id=student_id)
        serializer = ParentUpdateSerializer(student, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Parent details updated successfully'},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
# STUDENT ACADEMIC RECORDS (ADMIN)
# ============================================================

class StudentAcademicRecordListAPIView(APIView):
    """GET: List academic records with filters (student, class, year, status)"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def get(self, request):
        records = StudentAcademicRecord.objects.select_related(
            'student', 'student__user', 'class_enrolled', 'section', 'academic_year'
        )

        student_id = request.query_params.get('student_id')
        if student_id:
            records = records.filter(student_id=student_id)

        class_id = request.query_params.get('class_id')
        if class_id:
            records = records.filter(class_enrolled_id=class_id)

        academic_year_id = request.query_params.get('academic_year_id')
        if academic_year_id:
            records = records.filter(academic_year_id=academic_year_id)

        academic_year_name = request.query_params.get('academic_year')
        if academic_year_name:
            records = records.filter(academic_year__name=academic_year_name)

        status_param = request.query_params.get('status')
        if status_param:
            records = records.filter(status=status_param)

        serializer = StudentAcademicRecordSerializer(records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentAcademicRecordCreateAPIView(APIView):
    """POST: Create academic record"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def post(self, request):
        serializer = StudentAcademicRecordSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except DjangoValidationError as e:
                return Response(
                    {"error": "Validation error", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except IntegrityError as e:
                return Response(
                    {"error": "Database integrity error", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentAcademicRecordRetrieveAPIView(APIView):
    """GET: Retrieve a single academic record"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def get(self, request, pk):
        try:
            record = StudentAcademicRecord.objects.select_related(
                'student', 'student__user', 'class_enrolled', 'section', 'academic_year'
            ).get(pk=pk)
        except StudentAcademicRecord.DoesNotExist:
            return Response(
                {"error": "Academic record not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = StudentAcademicRecordSerializer(record)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentAcademicRecordUpdateAPIView(APIView):
    """PUT: Update an academic record"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def put(self, request, pk):
        try:
            record = StudentAcademicRecord.objects.get(pk=pk)
        except StudentAcademicRecord.DoesNotExist:
            return Response(
                {"error": "Academic record not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = StudentAcademicRecordSerializer(record, data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            except DjangoValidationError as e:
                return Response(
                    {"error": "Validation error", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentAcademicRecordDeleteAPIView(APIView):
    """DELETE: Delete an academic record"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def delete(self, request, pk):
        try:
            record = StudentAcademicRecord.objects.get(pk=pk)
        except StudentAcademicRecord.DoesNotExist:
            return Response(
                {"error": "Academic record not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        record.delete()
        return Response(
            {"message": "Academic record deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


# ============================================================
# STUDENT DOCUMENTS (ADMIN)
# ============================================================



class StudentDocumentCreateAPIView(APIView):
    """POST: Create a new student document"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def post(self, request):
        serializer = StudentDocumentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except DjangoValidationError as e:
                return Response(
                    {"error": "Validation error", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentDocumentRetrieveAPIView(APIView):
    """GET: Retrieve a document"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def get(self, request, pk):
        try:
            document = StudentDocument.objects.select_related(
                'student', 'student__user'
            ).get(pk=pk)
        except StudentDocument.DoesNotExist:
            return Response(
                {"error": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = StudentDocumentSerializer(document)
        return Response(serializer.data, status=status.HTTP_200_OK)



class StudentDocumentDeleteAPIView(APIView):
    """DELETE: Delete a document"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def delete(self, request, pk):
        try:
            document = StudentDocument.objects.get(pk=pk)
        except StudentDocument.DoesNotExist:
            return Response(
                {"error": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        document.delete()
        return Response(
            {"message": "Document deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


# ============================================================
# ATTENDANCE (ADMIN)
# ============================================================

class StudentAttendanceListAPIView(APIView):
    """GET: List attendance with rich filters"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def get(self, request):
        attendance_qs = StudentAttendance.objects.select_related(
            'student', 'student__user', 'marked_by'
        )

        student_id = request.query_params.get('student_id')
        if student_id:
            attendance_qs = attendance_qs.filter(student_id=student_id)

        # Date range
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date and end_date:
            attendance_qs = attendance_qs.filter(date__range=[start_date, end_date])

        # Single date
        date_str = request.query_params.get('date')
        if date_str:
            attendance_qs = attendance_qs.filter(date=date_str)

        # Status filter
        status_param = request.query_params.get('status')
        if status_param:
            attendance_qs = attendance_qs.filter(status=status_param)

        # Class + section
        class_id = request.query_params.get('class_id')
        section_id = request.query_params.get('section_id')
        if class_id:
            attendance_qs = attendance_qs.filter(student__current_class_id=class_id)
        if section_id:
            attendance_qs = attendance_qs.filter(student__section_id=section_id)

        serializer = StudentAttendanceSerializer(attendance_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentAttendanceCreateAPIView(APIView):
    """POST: Create a new attendance record"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def post(self, request):
        serializer = StudentAttendanceSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.validated_data['marked_by'] = request.user
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except DjangoValidationError as e:
                return Response(
                    {"error": "Validation error", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except IntegrityError as e:
                return Response(
                    {"error": "Duplicate attendance entry", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentAttendanceRetrieveAPIView(APIView):
    """GET: Retrieve a single attendance record"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def get(self, request, pk):
        try:
            attendance = StudentAttendance.objects.select_related(
                'student', 'student__user', 'marked_by'
            ).get(pk=pk)
        except StudentAttendance.DoesNotExist:
            return Response(
                {"error": "Attendance record not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = StudentAttendanceSerializer(attendance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentAttendanceUpdateAPIView(APIView):
    """PUT: Update an attendance record"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def put(self, request, pk):
        try:
            attendance = StudentAttendance.objects.get(pk=pk)
        except StudentAttendance.DoesNotExist:
            return Response(
                {"error": "Attendance record not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = StudentAttendanceSerializer(attendance, data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            except DjangoValidationError as e:
                return Response(
                    {"error": "Validation error", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentAttendanceDeleteAPIView(APIView):
    """DELETE: Delete an attendance record"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def delete(self, request, pk):
        try:
            attendance = StudentAttendance.objects.get(pk=pk)
        except StudentAttendance.DoesNotExist:
            return Response(
                {"error": "Attendance record not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        attendance.delete()
        return Response(
            {"message": "Attendance record deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class BulkAttendanceCreateAPIView(APIView):
    """
    POST: Bulk attendance
    - Option A: class_id + section_id + date (+ default_status)
                -> marks attendance for all students in that class/section
    - Option B: individual attendance_data list.
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def post(self, request):
        serializer = BulkAttendanceCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        attendance_date = data['date']
        class_id = data.get('class_id')
        section_id = data.get('section_id')
        attendance_data = data.get('attendance_data', [])
        default_status = data.get('default_status', 'P')

        created_count = 0
        updated_count = 0
        errors = []

        # Class + section bulk
        if class_id and section_id:
            try:
                students = Student.objects.filter(
                    current_class_id=class_id,
                    section_id=section_id,
                    is_active=True,
                )

                for student in students:
                    try:
                        attendance, created = StudentAttendance.objects.update_or_create(
                            student=student,
                            date=attendance_date,
                            defaults={
                                'status': default_status,
                                'marked_by': request.user,
                            },
                        )
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                    except Exception as e:
                        errors.append({
                            'student_id': student.id,
                            'error': str(e),
                        })

                return Response({
                    "message": f"Attendance marked for {students.count()} students",
                    "created": created_count,
                    "updated": updated_count,
                    "errors": errors,
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response(
                    {"error": "Bulk attendance failed", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Individual attendance list
        elif attendance_data:
            for item in attendance_data:
                try:
                    student = Student.objects.get(id=item['student_id'])
                    attendance, created = StudentAttendance.objects.update_or_create(
                        student=student,
                        date=item['date'],
                        defaults={
                            'status': item['status'],
                            'remarks': item.get('remarks', ''),
                            'marked_by': request.user,
                        },
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                except Student.DoesNotExist:
                    errors.append({
                        'student_id': item['student_id'],
                        'error': 'Student not found',
                    })
                except Exception as e:
                    errors.append({
                        'student_id': item.get('student_id'),
                        'error': str(e),
                    })

            return Response({
                "message": f"Attendance processed: {created_count} created, {updated_count} updated",
                "created": created_count,
                "updated": updated_count,
                "errors": errors,
            }, status=status.HTTP_201_CREATED)

        return Response(
            {"error": "Provide either class+section or individual attendance_data"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class StudentAttendanceSummaryAPIView(APIView):
    """GET: Attendance summary for a specific student (admin) for current month"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def get(self, request, student_id):
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response(
                {"error": "Student not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        today = date.today()
        first_day = today.replace(day=1)

        attendance = StudentAttendance.objects.filter(
            student=student,
            date__gte=first_day,
            date__lte=today,
        )

        total_days = (today - first_day).days + 1
        present_count = attendance.filter(status='P').count()
        absent_count = attendance.filter(status='A').count()
        late_count = attendance.filter(status='L').count()
        half_day_count = attendance.filter(status='H').count()

        attendance_rate = (present_count / total_days * 100) if total_days > 0 else 0

        return Response({
            "student": student.user.get_full_name(),
            "admission_number": student.admission_number,
            "class": student.current_class.display_name if student.current_class else None,
            "section": student.section.name if student.section else None,
            "period": f"{first_day} to {today}",
            "total_days": total_days,
            "present": present_count,
            "absent": absent_count,
            "late": late_count,
            "half_day": half_day_count,
            "attendance_rate": round(attendance_rate, 2),
            "attendance_details": StudentAttendanceSerializer(attendance, many=True).data,
        }, status=status.HTTP_200_OK)


# ============================================================
# CLASS / SECTION HELPERS & PROMOTION (ADMIN)
# ============================================================

class StudentClassSectionAPIView(APIView):
    """GET: List all students in a specific class+section"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def get(self, request, class_id, section_id):
        try:
            class_obj = Class.objects.get(id=class_id)
            section = Section.objects.get(id=section_id)
        except Class.DoesNotExist:
            return Response(
                {"error": "Class not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Section.DoesNotExist:
            return Response(
                {"error": "Section not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if getattr(section, 'class_obj', None) and section.class_obj != class_obj:
            return Response(
                {"error": "Section does not belong to the specified class"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        students = Student.objects.filter(
            current_class=class_obj,
            section=section,
            is_active=True,
        ).select_related('user').order_by('roll_number')

        serializer = StudentSerializer(students, many=True)
        return Response({
            "class": class_obj.display_name,
            "section": section.name,
            "total_students": students.count(),
            "students": serializer.data,
        }, status=status.HTTP_200_OK)


class AssignSectionAPIView(APIView):
    """POST: Assign/Change section & roll number of a student"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def post(self, request, student_id):
        section_id = request.data.get('section_id')
        roll_number = request.data.get('roll_number')

        if not section_id:
            return Response(
                {'error': 'section_id is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student = get_object_or_404(Student, id=student_id)
        section = get_object_or_404(Section, id=section_id)

        student.section = section
        if roll_number is not None:
            student.roll_number = roll_number
        student.save()

        return Response(
            {'message': 'Section assigned successfully'},
            status=status.HTTP_200_OK,
        )


class StudentPromotionAPIView(APIView):
    """
    POST: Promote a single student using serializer-driven fields (from code 1)
    Expected serializer: StudentPromotionSerializer with:
      - student_id, new_class_id, new_section_id, new_roll_number
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def post(self, request):
        serializer = StudentPromotionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        student = get_object_or_404(Student, id=data['student_id'])

        current_year = date.today().year
        next_year = current_year + 1

        # AcademicYear model integration
        academic_year, _ = AcademicYear.objects.get_or_create(
            name=f"{current_year}-{next_year}",
            defaults={
                'start_date': date(current_year, 4, 1),
                'end_date': date(next_year, 3, 31),
            },
        )

        # Create academic record for current class/section
        StudentAcademicRecord.objects.create(
            student=student,
            academic_year=academic_year,
            admission_year=str(student.admission_date.year),
            class_enrolled=student.current_class,
            section=student.section,
            roll_number=student.roll_number,
            status='PROMOTED',
        )

        # Update student to new class/section
        student.current_class_id = data['new_class_id']
        student.section_id = data['new_section_id']
        student.roll_number = data['new_roll_number']
        student.save()

        return Response(
            {'message': 'Student promoted successfully'},
            status=status.HTTP_200_OK,
        )


class BulkPromotionAPIView(APIView):
    """
    POST: Bulk promotion (from code 1), integrated with AcademicYear model.
    Uses BulkPromotionSerializer: {class_id, section_id?, new_class_id, new_section_id?}
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def post(self, request):
        serializer = BulkPromotionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        current_year = date.today().year
        next_year = current_year + 1

        academic_year, _ = AcademicYear.objects.get_or_create(
            name=f"{current_year}-{next_year}",
            defaults={
                'start_date': date(current_year, 4, 1),
                'end_date': date(next_year, 3, 31),
            },
        )

        students = Student.objects.filter(
            current_class_id=data['class_id'],
            is_active=True,
        )
        if data.get('section_id'):
            students = students.filter(section_id=data['section_id'])

        promoted_count = 0
        errors = []

        for student in students:
            try:
                StudentAcademicRecord.objects.create(
                    student=student,
                    academic_year=academic_year,
                    admission_year=str(student.admission_date.year),
                    class_enrolled=student.current_class,
                    section=student.section,
                    roll_number=student.roll_number,
                    status='PROMOTED',
                )

                student.current_class_id = data['new_class_id']
                if data.get('new_section_id'):
                    student.section_id = data['new_section_id']
                student.save()

                promoted_count += 1
            except Exception as e:
                errors.append(
                    f"Error promoting student {student.admission_number}: {str(e)}"
                )

        return Response({
            'message': f'Bulk promotion completed: {promoted_count} students promoted',
            'errors': errors if errors else None,
        }, status=status.HTTP_200_OK)


class StudentPromoteAPIView(APIView):
    """
    POST: Auto-promote based on numeric class name (from code 2).
    Kept for backward compatibility if you used this endpoint earlier.
    """
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def post(self, request, student_id):
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response(
                {"error": "Student not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        current_year = date.today().year
        next_year = current_year + 1

        current_class_name = student.current_class.name if student.current_class else None
        if not current_class_name:
            return Response(
                {"error": "Student is not assigned to any class"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            current_class_num = int(current_class_name)
            next_class_name = str(current_class_num + 1)

            try:
                next_class = Class.objects.get(name=next_class_name, is_active=True)
            except Class.DoesNotExist:
                return Response(
                    {"error": f"Next class {next_class_name} does not exist"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            academic_year, _ = AcademicYear.objects.get_or_create(
                name=f"{current_year}-{next_year}",
                defaults={
                    'start_date': date(current_year, 4, 1),
                    'end_date': date(next_year, 3, 31),
                },
            )

            record = StudentAcademicRecord.objects.create(
                student=student,
                academic_year=academic_year,
                admission_year=str(student.admission_date.year),
                class_enrolled=student.current_class,
                section=student.section,
                roll_number=student.roll_number,
                status='PROMOTED',
            )

            old_class_display = student.current_class.display_name if student.current_class else None

            student.current_class = next_class
            student.section = None
            student.roll_number = 0
            student.save()

            return Response({
                "message": f"Student promoted from {old_class_display} to {next_class.display_name}",
                "academic_record": StudentAcademicRecordSerializer(record).data,
                "updated_student": StudentSerializer(student).data,
            }, status=status.HTTP_200_OK)

        except ValueError:
            return Response(
                {"error": "Cannot determine next class automatically"},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ============================================================
# DASHBOARD (ADMIN)
# ============================================================

class StudentDashboardAPIView(APIView):
    """GET: Basic dashboard stats for students"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def get(self, request):
        total_students = Student.objects.filter(is_active=True).count()
        now = datetime.now()
        new_admissions = Student.objects.filter(
            admission_date__month=now.month,
            admission_date__year=now.year,
        ).count()

        class_stats = []
        classes = Class.objects.filter(is_active=True)
        for cls in classes:
            count = Student.objects.filter(
                current_class=cls,
                is_active=True,
            ).count()
            class_stats.append({
                'class_id': cls.id,
                'class_name': cls.display_name,
                'student_count': count,
            })

        return Response({
            'total_students': total_students,
            'new_admissions': new_admissions,
            'class_wise_stats': class_stats,
        }, status=status.HTTP_200_OK)


# ============================================================
# GENERIC FEE PAYMENT (ADMIN PLACEHOLDER)
# ============================================================

class StudentFeePaymentAPIView(APIView):
    """Basic placeholder for fee payment (admin-triggered)"""
    permission_classes = [IsAuthenticated, StudentsModulePermission]

    def post(self, request):
        serializer = FeePaymentSerializer(data=request.data)
        if serializer.is_valid():
            # Integrate with actual fee/payment logic
            return Response(
                {'message': 'Fee payment processed successfully'},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
# STUDENT PORTAL APIs (SELF)
# ============================================================

class StudentProfileAPIView(APIView):
    """GET: Student self profile"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = StudentProfileSerializer(student)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateProfilePictureAPIView(APIView):
    """PATCH: Update student profile picture (self)"""
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if 'photo' not in request.FILES:
            return Response(
                {'error': 'Photo file is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student.photo = request.FILES['photo']
        student.save()
        return Response(
            {'message': 'Profile picture updated successfully'},
            status=status.HTTP_200_OK,
        )


class ParentInfoAPIView(APIView):
    """GET: Parent/guardian info for logged-in student"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ParentInfoSerializer(student)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ClassTimetableAPIView(APIView):
    """GET: Timetable for logged-in student"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not student.current_class or not student.section:
            return Response(
                {'error': 'Student not assigned to any class/section'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        timetable = TimeTable.objects.filter(
            class_name=student.current_class,
            section=student.section,
            is_active=True,
        ).order_by('day', 'period')

        serializer = TimetableSerializer(timetable, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AssignedSubjectsAPIView(APIView):
    """GET: Subjects assigned to logged-in student for current academic year"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not student.current_class:
            return Response(
                {'error': 'Student not assigned to any class'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        current_year = date.today().year
        academic_year_name = f"{current_year}-{current_year + 1}"

        subjects = ClassSubject.objects.filter(
            class_name=student.current_class,
            academic_year__name=academic_year_name,
        )

        serializer = SubjectTeacherSerializer(subjects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TeachersListAPIView(APIView):
    """GET: Teachers list for logged-in student's class"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not student.current_class:
            return Response(
                {'error': 'Student not assigned to any class'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        current_year = date.today().year
        academic_year_name = f"{current_year}-{current_year + 1}"

        class_subjects = ClassSubject.objects.filter(
            class_name=student.current_class,
            academic_year__name=academic_year_name,
        ).select_related('teacher', 'subject')

        teachers = {cs.teacher for cs in class_subjects if cs.teacher}
        teacher_data = []

        for teacher in teachers:
            teacher_data.append({
                'id': teacher.id,
                'name': teacher.user.get_full_name(),
                'email': teacher.user.email,
                'phone': getattr(teacher.user, 'phone', None),
                'subjects': [
                    cs.subject.name for cs in class_subjects if cs.teacher == teacher
                ],
            })

        return Response(teacher_data, status=status.HTTP_200_OK)


class AssignmentsAPIView(APIView):
    """GET: List assignments for logged-in student"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not student.current_class:
            return Response(
                {'error': 'Student not assigned to any class'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        assignments = Assignment.objects.filter(
            class_name=student.current_class,
            section=student.section,
            is_active=True,
        ).order_by('-due_date')

        serializer = AssignmentSerializer(
            assignments, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class AssignmentDetailAPIView(APIView):
    """GET: Assignment details + submission for logged-in student"""
    permission_classes = [IsAuthenticated]

    def get(self, request, assignment_id):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        assignment = get_object_or_404(Assignment, id=assignment_id)
        submission = AssignmentSubmission.objects.filter(
            assignment=assignment,
            student=student,
        ).first()

        assignment_data = AssignmentSerializer(
            assignment, context={'request': request}
        ).data
        submission_data = (
            AssignmentSubmissionSerializer(submission).data if submission else None
        )

        return Response({
            'assignment': assignment_data,
            'submission': submission_data,
        }, status=status.HTTP_200_OK)


class SubmitAssignmentAPIView(APIView):
    """POST: Submit/Resubmit assignment (self)"""
    permission_classes = [IsAuthenticated]

    def post(self, request, assignment_id):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        assignment = get_object_or_404(Assignment, id=assignment_id)

        if assignment.due_date < timezone.now().date():
            return Response(
                {'error': 'Assignment submission deadline has passed'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        submission, created = AssignmentSubmission.objects.update_or_create(
            assignment=assignment,
            student=student,
            defaults={
                'submission_file': request.FILES.get('submission_file'),
                'submission_text': request.data.get('submission_text', ''),
                'submitted_at': timezone.now(),
            },
        )

        serializer = AssignmentSubmissionSerializer(submission)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ExamScheduleAPIView(APIView):
    """GET: Exam schedule for logged-in student"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not student.current_class:
            return Response(
                {'error': 'Student not assigned to any class'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        exams = Exam.objects.filter(
            class_name=student.current_class,
            is_active=True,
        ).order_by('exam_date', 'start_time')

        serializer = ExamScheduleSerializer(exams, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ExamResultsAPIView(APIView):
    """GET: Exam results for logged-in student"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        results = ExamResult.objects.filter(
            student=student,
        ).select_related('exam').order_by('-exam__exam_date')

        serializer = ExamResultSerializer(results, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AttendanceSummaryStudentAPIView(APIView):
    """
    GET: Monthly attendance summary for logged-in student
    (renamed from AttendanceSummaryAPIView to avoid name clash)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        month = int(request.query_params.get('month', datetime.now().month))
        year = int(request.query_params.get('year', datetime.now().year))

        _, num_days = calendar.monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, num_days)

        attendance = StudentAttendance.objects.filter(
            student=student,
            date__range=[start_date, end_date],
        )

        present = attendance.filter(status='P').count()
        absent = attendance.filter(status='A').count()
        late = attendance.filter(status='L').count()
        total_days = num_days

        percentage = (present / total_days * 100) if total_days > 0 else 0

        summary = {
            'month': calendar.month_name[month],
            'year': year,
            'total_days': total_days,
            'present_days': present,
            'absent_days': absent,
            'late_days': late,
            'percentage': round(percentage, 2),
        }

        serializer = AttendanceSummarySerializer(summary)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DailyAttendanceAPIView(APIView):
    """GET: Daily attendance logs for logged-in student (date range)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            today = timezone.now().date()
            start_date = today.replace(day=1)
            end_date = today

        attendance = StudentAttendance.objects.filter(
            student=student,
            date__range=[start_date, end_date],
        ).order_by('-date')

        serializer = DailyAttendanceSerializer(attendance, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# FEES (STUDENT PORTAL)
# ============================================================

class FeeDetailsAPIView(APIView):
    """GET: Fee structure & summary for logged-in student"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not student.current_class:
            return Response(
                {'error': 'Student not assigned to any class'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        current_year = date.today().year
        academic_year_name = f"{current_year}-{current_year + 1}"

        fee_structures = FeeStructure.objects.filter(
            class_name=student.current_class,
            academic_year__name=academic_year_name,
        )

        serializer = FeeDetailSerializer(
            fee_structures, many=True, context={'request': request}
        )

        total_amount = sum(fs.amount for fs in fee_structures)
        paid_amount = 0
        for fs in fee_structures:
            if FeePayment.objects.filter(
                student=student,
                fee_structure=fs,
                payment_status='PAID',
            ).exists():
                paid_amount += fs.amount

        return Response({
            'fee_details': serializer.data,
            'summary': {
                'total_amount': total_amount,
                'paid_amount': paid_amount,
                'pending_amount': total_amount - paid_amount,
            },
        }, status=status.HTTP_200_OK)


class FeePaymentHistoryAPIView(APIView):
    """GET: Fee payment history for logged-in student"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        payments = FeePayment.objects.filter(
            student=student,
        ).select_related('fee_structure').order_by('-payment_date')

        serializer = FeePaymentSerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PayFeeAPIView(APIView):
    """POST: Pay a fee item (student initiates payment)"""
    permission_classes = [IsAuthenticated]

    def post(self, request, fee_structure_id):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        fee_structure = get_object_or_404(FeeStructure, id=fee_structure_id)

        if FeePayment.objects.filter(
            student=student,
            fee_structure=fee_structure,
            payment_status='PAID',
        ).exists():
            return Response(
                {'error': 'Fee already paid'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = FeePayment.objects.create(
            student=student,
            fee_structure=fee_structure,
            amount_paid=fee_structure.amount,
            payment_mode=request.data.get('payment_mode', 'ONLINE'),
            transaction_id=request.data.get('transaction_id', ''),
            payment_status='PAID',
            payment_date=timezone.now().date(),
        )

        serializer = FeePaymentSerializer(payment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DownloadFeeReceiptAPIView(APIView):
    """GET: Fee receipt data for a payment (student)"""
    permission_classes = [IsAuthenticated]

    def get(self, request, payment_id):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        payment = get_object_or_404(FeePayment, id=payment_id, student=student)

        receipt_data = {
            'receipt_number': f"RCPT{payment.id:06d}",
            'payment_date': payment.payment_date,
            'student_name': student.user.get_full_name(),
            'admission_number': student.admission_number,
            'class': student.current_class.display_name if student.current_class else '',
            'section': student.section.name if student.section else '',
            'fee_type': payment.fee_structure.fee_type,
            'amount_paid': payment.amount_paid,
            'payment_mode': payment.payment_mode,
            'transaction_id': payment.transaction_id,
        }

        return Response(receipt_data, status=status.HTTP_200_OK)


# ============================================================
# REPORT CARD (STUDENT PORTAL)
# ============================================================

class ReportCardAPIView(APIView):
    """GET: Report card for logged-in student for given or current academic year"""
    permission_classes = [IsAuthenticated]

    def get(self, request, academic_year=None):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not academic_year:
            current_year = date.today().year
            academic_year = f"{current_year}-{current_year + 1}"

        results = ExamResult.objects.filter(
            student=student,
            exam__academic_year__name=academic_year,
        ).select_related('exam', 'exam__subject')

        if not results.exists():
            return Response(
                {'error': 'No results found for this academic year'},
                status=status.HTTP_404_NOT_FOUND,
            )

        total_marks = sum(result.exam.total_marks for result in results)
        obtained_marks = sum(result.marks_obtained for result in results)
        percentage = (obtained_marks / total_marks * 100) if total_marks > 0 else 0

        subjects_data = []
        for result in results:
            subjects_data.append({
                'subject': result.exam.subject.name,
                'total_marks': result.exam.total_marks,
                'obtained_marks': result.marks_obtained,
                'grade': result.grade,
                'remarks': result.remarks,
            })

        if percentage >= 90:
            grade = 'A'
        elif percentage >= 75:
            grade = 'B'
        elif percentage >= 60:
            grade = 'C'
        else:
            grade = 'D'

        # Rank calculation is domain-specific; placeholder:
        rank = 1

        report_card = {
            'academic_year': academic_year,
            'class_name': student.current_class.display_name if student.current_class else '',
            'section_name': student.section.name if student.section else '',
            'student_name': student.user.get_full_name(),
            'roll_number': student.roll_number,
            'total_marks': total_marks,
            'obtained_marks': obtained_marks,
            'percentage': round(percentage, 2),
            'grade': grade,
            'rank': rank,
            'subjects': subjects_data,
        }

        serializer = ReportCardSerializer(report_card)
        return Response(serializer.data, status=status.HTTP_200_OK)
