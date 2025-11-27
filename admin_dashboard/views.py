from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum
from datetime import datetime, timedelta
from core.custom_permission import*
from students.models import*
from teachers.models import*
from classes.models import*
from attendance.models import*
from fees.models import*
from library.models import*
from users.models import*
from examinations.models import*

class AdminDashboardOverviewAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentsModulePermission, TeachersModulePermission, 
                         AttendanceModulePermission, FeesModulePermission]
    
    def get(self, request):
        try:
            # Get overview statistics
            total_students = Student.objects.filter(is_active=True).count()
            total_teachers = Teacher.objects.filter(is_active=True).count()
            total_classes = Class.objects.count()
            total_sections = Section.objects.count()
            
            # Today's attendance
            today = datetime.now().date()
            todays_attendance = Attendance.objects.filter(date=today, status='present').count()
            
            # Pending fees
            pending_fees = FeeStructure.objects.filter(
                status='pending'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            data = {
                'total_students': total_students,
                'total_teachers': total_teachers,
                'total_classes': total_classes,
                'total_sections': total_sections,
                'todays_attendance': todays_attendance,
                'pending_fees': pending_fees,
                'last_updated': datetime.now().isoformat()
            }
            
            return Response({'status': 'success', 'data': data}, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to fetch dashboard overview', 'status': 'error'}, status=500)

# Input: GET /api/v1/admin/dashboard/overview/
# Output: {
#   "status": "success",
#   "data": {
#     "total_students": 1250,
#     "total_teachers": 85,
#     "total_classes": 12,
#     "total_sections": 24,
#     "todays_attendance": 1180,
#     "pending_fees": 125000.00,
#     "last_updated": "2025-09-06T23:44:00"
#   }
# }

class AdminStatisticsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get date range from query params
            days = int(request.GET.get('days', 30))
            start_date = datetime.now().date() - timedelta(days=days)
            
            # Monthly statistics
            monthly_stats = {
                'new_admissions': Student.objects.filter(
                    created_at__date__gte=start_date
                ).count(),
                'fee_collection': FeeStructure.objects.filter(
                    created_at__date__gte=start_date,
                    status='paid'
                ).aggregate(total=Sum('amount'))['total'] or 0,
                'attendance_rate': self.calculate_attendance_rate(start_date),
                'exam_results': ExamResult.objects.filter(
                    created_at__date__gte=start_date
                ).count()
            }
            
            return Response({'status': 'success', 'data': monthly_stats}, status=200)
            
        except ValueError:
            return Response({'error': 'Invalid days parameter', 'status': 'error'}, status=400)
        except Exception as e:
            return Response({'error': 'Failed to fetch statistics', 'status': 'error'}, status=500)
    
    def calculate_attendance_rate(self, start_date):
        total_present = Attendance.objects.filter(
            date__gte=start_date, status='present'
        ).count()
        total_records = Attendance.objects.filter(date__gte=start_date).count()
        
        return round((total_present / total_records) * 100, 2) if total_records > 0 else 0

# Input: GET /api/v1/admin/dashboard/statistics/?days=30
# Output: {
#   "status": "success",
#   "data": {
#     "new_admissions": 45,
#     "fee_collection": 450000.00,
#     "attendance_rate": 92.5,
#     "exam_results": 320
#   }
# }

class RecentActivitiesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            limit = int(request.GET.get('limit', 20))
            
            # Get recent activities from different modules
            recent_activities = []
            
            # Recent student admissions
            recent_students = Student.objects.filter(
                created_at__date__gte=datetime.now().date() - timedelta(days=7)
            ).order_by('-created_at')[:5]
            
            for student in recent_students:
                recent_activities.append({
                    'type': 'student_admission',
                    'message': f'New student {student.full_name} admitted to {student.class_name}',
                    'timestamp': student.created_at.isoformat(),
                    'user': student.created_by.username if student.created_by else 'System'
                })
            
            # Recent fee collections
            recent_fees = FeeStructure.objects.filter(
                status='paid',
                updated_at__date__gte=datetime.now().date() - timedelta(days=7)
            ).order_by('-updated_at')[:5]
            
            for fee in recent_fees:
                recent_activities.append({
                    'type': 'fee_collection',
                    'message': f'Fee payment of ₹{fee.amount} received from {fee.student.full_name}',
                    'timestamp': fee.updated_at.isoformat(),
                    'user': fee.collected_by.username if fee.collected_by else 'System'
                })
            
            # Sort by timestamp and limit
            recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
            recent_activities = recent_activities[:limit]
            
            return Response({'status': 'success', 'data': recent_activities}, status=200)
            
        except ValueError:
            return Response({'error': 'Invalid limit parameter', 'status': 'error'}, status=400)
        except Exception as e:
            return Response({'error': 'Failed to fetch recent activities', 'status': 'error'}, status=500)

# Input: GET /api/v1/admin/dashboard/activities/?limit=10
# Output: {
#   "status": "success",
#   "data": [
#     {
#       "type": "student_admission",
#       "message": "New student John Doe admitted to Class 10-A",
#       "timestamp": "2025-09-06T15:30:00",
#       "user": "admin"
#     }
#   ]
# }


class AdminStudentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def get(self, request):
        try:
            # Query parameters
            class_id = request.GET.get('class_id')
            section_id = request.GET.get('section_id')
            search = request.GET.get('search')
            page = int(request.GET.get('page', 1))
            limit = int(request.GET.get('limit', 20))
            
            # Base queryset
            queryset = Student.objects.filter(is_active=True)
            
            # Apply filters
            if class_id:
                queryset = queryset.filter(class_assigned_id=class_id)
            if section_id:
                queryset = queryset.filter(section_id=section_id)
            if search:
                queryset = queryset.filter(
                    Q(full_name__icontains=search) | 
                    Q(admission_number__icontains=search) |
                    Q(email__icontains=search)
                )
            
            # Pagination
            offset = (page - 1) * limit
            total_count = queryset.count()
            students = queryset[offset:offset + limit]
            
            # Serialize data
            students_data = []
            for student in students:
                students_data.append({
                    'id': student.id,
                    'admission_number': student.admission_number,
                    'full_name': student.full_name,
                    'email': student.email,
                    'phone': student.phone,
                    'class_name': student.class_assigned.name if student.class_assigned else None,
                    'section_name': student.section.name if student.section else None,
                    'status': student.status,
                    'created_at': student.created_at.isoformat()
                })
            
            return Response({
                'status': 'success',
                'data': {
                    'students': students_data,
                    'total_count': total_count,
                    'page': page,
                    'has_next': offset + limit < total_count
                }
            }, status=200)
            
        except ValueError:
            return Response({'error': 'Invalid pagination parameters', 'status': 'error'}, status=400)
        except Exception as e:
            return Response({'error': 'Failed to fetch students', 'status': 'error'}, status=500)
    
    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['full_name', 'email', 'phone', 'class_id', 'section_id']
            for field in required_fields:
                if not data.get(field):
                    return Response({'error': f'{field} is required', 'status': 'error'}, status=400)
            
            # Check if email already exists
            if Student.objects.filter(email=data['email']).exists():
                return Response({'error': 'Email already exists', 'status': 'error'}, status=400)
            
            # Generate admission number
            admission_number = self.generate_admission_number()
            
            # Create student
            student = Student.objects.create(
                admission_number=admission_number,
                full_name=data['full_name'],
                email=data['email'],
                phone=data['phone'],
                class_assigned_id=data['class_id'],
                section_id=data['section_id'],
                date_of_birth=data.get('date_of_birth'),
                gender=data.get('gender'),
                address=data.get('address'),
                parent_name=data.get('parent_name'),
                parent_phone=data.get('parent_phone'),
                created_by=request.user
            )
            
            return Response({
                'status': 'success',
                'data': {
                    'id': student.id,
                    'admission_number': student.admission_number,
                    'full_name': student.full_name,
                    'message': 'Student created successfully'
                }
            }, status=201)
            
        except Exception as e:
            return Response({'error': 'Failed to create student', 'status': 'error'}, status=500)
    
    def generate_admission_number(self):
        current_year = datetime.now().year
        last_student = Student.objects.filter(
            admission_number__startswith=str(current_year)
        ).order_by('-admission_number').first()
        
        if last_student:
            last_number = int(last_student.admission_number[-4:])
            new_number = last_number + 1
        else:
            new_number = 1
            
        return f"{current_year}{new_number:04d}"

# Input POST: {
#   "full_name": "John Doe",
#   "email": "john@example.com",
#   "phone": "9876543210",
#   "class_id": 1,
#   "section_id": 1,
#   "date_of_birth": "2005-05-15",
#   "gender": "male",
#   "parent_name": "Robert Doe",
#   "parent_phone": "9876543211"
# }


class AdminStudentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def get(self, request, pk):
        try:
            student = Student.objects.select_related('class_assigned', 'section').get(
                id=pk, is_active=True
            )
            
            # Get student's attendance summary
            attendance_summary = self.get_attendance_summary(student.id)
            
            # Get fee status
            fee_status = self.get_fee_status(student.id)
            
            student_data = {
                'id': student.id,
                'admission_number': student.admission_number,
                'full_name': student.full_name,
                'email': student.email,
                'phone': student.phone,
                'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else None,
                'gender': student.gender,
                'address': student.address,
                'class_name': student.class_assigned.name if student.class_assigned else None,
                'section_name': student.section.name if student.section else None,
                'parent_name': student.parent_name,
                'parent_phone': student.parent_phone,
                'status': student.status,
                'attendance_summary': attendance_summary,
                'fee_status': fee_status,
                'created_at': student.created_at.isoformat()
            }
            
            return Response({'status': 'success', 'data': student_data}, status=200)
            
        except Student.DoesNotExist:
            return Response({'error': 'Student not found', 'status': 'error'}, status=404)
        except Exception as e:
            return Response({'error': 'Failed to fetch student details', 'status': 'error'}, status=500)
    
    def put(self, request, pk):
        try:
            student = Student.objects.get(id=pk, is_active=True)
            data = request.data
            
            # Update student fields
            updatable_fields = [
                'full_name', 'email', 'phone', 'date_of_birth', 'gender',
                'address', 'parent_name', 'parent_phone', 'class_assigned_id', 'section_id'
            ]
            
            for field in updatable_fields:
                if field in data:
                    if field == 'class_assigned_id':
                        student.class_assigned_id = data[field]
                    else:
                        setattr(student, field, data[field])
            
            student.updated_by = request.user
            student.save()
            
            return Response({
                'status': 'success',
                'data': {'message': 'Student updated successfully'}
            }, status=200)
            
        except Student.DoesNotExist:
            return Response({'error': 'Student not found', 'status': 'error'}, status=404)
        except Exception as e:
            return Response({'error': 'Failed to update student', 'status': 'error'}, status=500)
    
    def delete(self, request, pk):
        try:
            student = Student.objects.get(id=pk, is_active=True)
            student.is_active = False
            student.deleted_by = request.user
            student.save()
            
            return Response({
                'status': 'success',
                'data': {'message': 'Student deleted successfully'}
            }, status=200)
            
        except Student.DoesNotExist:
            return Response({'error': 'Student not found', 'status': 'error'}, status=404)
        except Exception as e:
            return Response({'error': 'Failed to delete student', 'status': 'error'}, status=500)
    
    def get_attendance_summary(self, student_id):
        current_month = datetime.now().replace(day=1)
        total_days = Attendance.objects.filter(
            student_id=student_id,
            date__gte=current_month
        ).count()
        present_days = Attendance.objects.filter(
            student_id=student_id,
            date__gte=current_month,
            status='present'
        ).count()
        
        return {
            'total_days': total_days,
            'present_days': present_days,
            'attendance_percentage': round((present_days / total_days) * 100, 2) if total_days > 0 else 0
        }
    
    def get_fee_status(self, student_id):
        pending_fees = FeeStructure.objects.filter(
            student_id=student_id,
            status='pending'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return {
            'pending_amount': pending_fees,
            'status': 'pending' if pending_fees > 0 else 'paid'
        }

# Input PUT: {
#   "full_name": "John Smith",
#   "phone": "9876543210",
#   "class_assigned_id": 2
# }

class BulkStudentImportAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def post(self, request):
        try:
            if 'file' not in request.FILES:
                return Response({'error': 'No file provided', 'status': 'error'}, status=400)
            
            file = request.FILES['file']
            
            # Validate file format
            if not file.name.endswith('.csv'):
                return Response({'error': 'Only CSV files are allowed', 'status': 'error'}, status=400)
            
            # Process CSV file
            import pandas as pd
            df = pd.read_csv(file)
            
            # Validate required columns
            required_columns = ['full_name', 'email', 'phone', 'class_name', 'section_name']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return Response({
                    'error': f'Missing required columns: {", ".join(missing_columns)}',
                    'status': 'error'
                }, status=400)
            
            # Process each row
            success_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Check if student already exists
                    if Student.objects.filter(email=row['email']).exists():
                        errors.append(f'Row {index + 1}: Email {row["email"]} already exists')
                        error_count += 1
                        continue
                    
                    # Get class and section
                    class_obj = Class.objects.filter(name=row['class_name']).first()
                    section_obj = Section.objects.filter(name=row['section_name']).first()
                    
                    if not class_obj:
                        errors.append(f'Row {index + 1}: Class {row["class_name"]} not found')
                        error_count += 1
                        continue
                    
                    if not section_obj:
                        errors.append(f'Row {index + 1}: Section {row["section_name"]} not found')
                        error_count += 1
                        continue
                    
                    # Create student
                    Student.objects.create(
                        admission_number=self.generate_admission_number(),
                        full_name=row['full_name'],
                        email=row['email'],
                        phone=row['phone'],
                        class_assigned=class_obj,
                        section=section_obj,
                        date_of_birth=row.get('date_of_birth'),
                        gender=row.get('gender'),
                        parent_name=row.get('parent_name'),
                        parent_phone=row.get('parent_phone'),
                        created_by=request.user
                    )
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f'Row {index + 1}: {str(e)}')
                    error_count += 1
            
            return Response({
                'status': 'success',
                'data': {
                    'success_count': success_count,
                    'error_count': error_count,
                    'errors': errors[:10],  # Return first 10 errors
                    'message': f'Imported {success_count} students successfully'
                }
            }, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to import students', 'status': 'error'}, status=500)

# Input: CSV file with columns: full_name, email, phone, class_name, section_name, date_of_birth, gender, parent_name, parent_phone
# Output: {
#   "status": "success",
#   "data": {
#     "success_count": 45,
#     "error_count": 3,
#     "errors": ["Row 5: Email already exists"],
#     "message": "Imported 45 students successfully"
#   }
# }

class AdminTeacherListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def get(self, request):
        try:
            # Query parameters
            department = request.GET.get('department')
            search = request.GET.get('search')
            page = int(request.GET.get('page', 1))
            limit = int(request.GET.get('limit', 20))
            
            # Base queryset
            queryset = Teacher.objects.filter(is_active=True)
            
            # Apply filters
            if department:
                queryset = queryset.filter(department=department)
            if search:
                queryset = queryset.filter(
                    Q(full_name__icontains=search) | 
                    Q(employee_id__icontains=search) |
                    Q(email__icontains=search)
                )
            
            # Pagination
            offset = (page - 1) * limit
            total_count = queryset.count()
            teachers = queryset[offset:offset + limit]
            
            # Serialize data
            teachers_data = []
            for teacher in teachers:
                teachers_data.append({
                    'id': teacher.id,
                    'employee_id': teacher.employee_id,
                    'full_name': teacher.full_name,
                    'email': teacher.email,
                    'phone': teacher.phone,
                    'department': teacher.department,
                    'designation': teacher.designation,
                    'qualification': teacher.qualification,
                    'experience_years': teacher.experience_years,
                    'status': teacher.status,
                    'created_at': teacher.created_at.isoformat()
                })
            
            return Response({
                'status': 'success',
                'data': {
                    'teachers': teachers_data,
                    'total_count': total_count,
                    'page': page,
                    'has_next': offset + limit < total_count
                }
            }, status=200)
            
        except ValueError:
            return Response({'error': 'Invalid pagination parameters', 'status': 'error'}, status=400)
        except Exception as e:
            return Response({'error': 'Failed to fetch teachers', 'status': 'error'}, status=500)
    
    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['full_name', 'email', 'phone', 'department', 'designation']
            for field in required_fields:
                if not data.get(field):
                    return Response({'error': f'{field} is required', 'status': 'error'}, status=400)
            
            # Check if email already exists
            if Teacher.objects.filter(email=data['email']).exists():
                return Response({'error': 'Email already exists', 'status': 'error'}, status=400)
            
            # Generate employee ID
            employee_id = self.generate_employee_id()
            
            # Create teacher
            teacher = Teacher.objects.create(
                employee_id=employee_id,
                full_name=data['full_name'],
                email=data['email'],
                phone=data['phone'],
                department=data['department'],
                designation=data['designation'],
                qualification=data.get('qualification'),
                experience_years=data.get('experience_years', 0),
                date_of_birth=data.get('date_of_birth'),
                gender=data.get('gender'),
                address=data.get('address'),
                joining_date=data.get('joining_date', datetime.now().date()),
                salary=data.get('salary'),
                created_by=request.user
            )
            
            return Response({
                'status': 'success',
                'data': {
                    'id': teacher.id,
                    'employee_id': teacher.employee_id,
                    'full_name': teacher.full_name,
                    'message': 'Teacher created successfully'
                }
            }, status=201)
            
        except Exception as e:
            return Response({'error': 'Failed to create teacher', 'status': 'error'}, status=500)
    
    def generate_employee_id(self):
        current_year = datetime.now().year
        last_teacher = Teacher.objects.filter(
            employee_id__startswith=f"EMP{current_year}"
        ).order_by('-employee_id').first()
        
        if last_teacher:
            last_number = int(last_teacher.employee_id[-4:])
            new_number = last_number + 1
        else:
            new_number = 1
            
        return f"EMP{current_year}{new_number:04d}"

# Input POST: {
#   "full_name": "Jane Smith",
#   "email": "jane@example.com",
#   "phone": "9876543210",
#   "department": "Mathematics",
#   "designation": "Senior Teacher",
#   "qualification": "M.Sc Mathematics",
#   "experience_years": 5,
#   "salary": 50000
# }

class TeacherSubjectAssignmentAPIView(APIView):
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            if not data.get('teacher_id'):
                return Response({'error': 'teacher_id is required', 'status': 'error'}, status=400)
            if not data.get('subjects'):
                return Response({'error': 'subjects list is required', 'status': 'error'}, status=400)
            
            # Check if teacher exists
            teacher = Teacher.objects.filter(id=data['teacher_id'], is_active=True).first()
            if not teacher:
                return Response({'error': 'Teacher not found', 'status': 'error'}, status=404)
            
            # Clear existing subject assignments
            TeacherSubject.objects.filter(teacher=teacher).delete()
            
            # Assign new subjects
            assigned_subjects = []
            for subject_data in data['subjects']:
                subject = Subject.objects.filter(id=subject_data['subject_id']).first()
                class_obj = Class.objects.filter(id=subject_data['class_id']).first()
                section = Section.objects.filter(id=subject_data.get('section_id')).first()
                
                if not subject:
                    return Response({'error': f'Subject with id {subject_data["subject_id"]} not found', 'status': 'error'}, status=400)
                if not class_obj:
                    return Response({'error': f'Class with id {subject_data["class_id"]} not found', 'status': 'error'}, status=400)
                
                teacher_subject = TeacherSubject.objects.create(
                    teacher=teacher,
                    subject=subject,
                    class_assigned=class_obj,
                    section=section,
                    created_by=request.user
                )
                
                assigned_subjects.append({
                    'subject_name': subject.name,
                    'class_name': class_obj.name,
                    'section_name': section.name if section else None
                })
            
            return Response({
                'status': 'success',
                'data': {
                    'teacher_name': teacher.full_name,
                    'assigned_subjects': assigned_subjects,
                    'message': 'Subjects assigned successfully'
                }
            }, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to assign subjects', 'status': 'error'}, status=500)

# Input: {
#   "teacher_id": 1,
#   "subjects": [
#     {
#       "subject_id": 1,
#       "class_id": 1,
#       "section_id": 1
#     },
#     {
#       "subject_id": 2,
#       "class_id": 2
#     }
#   ]
# }

class AssignClassTeacherAPIView(APIView):
    permission_classes = [IsAuthenticated, TeachersModulePermission, ClassesModulePermission]
    
    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['teacher_id', 'class_id', 'section_id']
            for field in required_fields:
                if not data.get(field):
                    return Response({'error': f'{field} is required', 'status': 'error'}, status=400)
            
            # Check if teacher exists
            teacher = Teacher.objects.filter(id=data['teacher_id'], is_active=True).first()
            if not teacher:
                return Response({'error': 'Teacher not found', 'status': 'error'}, status=404)
            
            # Check if class and section exist
            class_obj = Class.objects.filter(id=data['class_id']).first()
            section = Section.objects.filter(id=data['section_id']).first()
            
            if not class_obj:
                return Response({'error': 'Class not found', 'status': 'error'}, status=404)
            if not section:
                return Response({'error': 'Section not found', 'status': 'error'}, status=404)
            
            # Check if class-section already has a class teacher
            existing_assignment = TeacherSubject.objects.filter(
                class_assigned=class_obj,
                section=section,
                is_active=True
            ).first()
            
            if existing_assignment:
                return Response({
                    'error': f'Class {class_obj.name}-{section.name} already has a class teacher',
                    'status': 'error'
                }, status=400)
            
            # Create class teacher assignment
            class_teacher = TeacherSubject.objects.create(
                teacher=teacher,
                class_assigned=class_obj,
                section=section,
                assigned_date=datetime.now().date(),
                created_by=request.user
            )
            
            return Response({
                'status': 'success',
                'data': {
                    'teacher_name': teacher.full_name,
                    'class_name': class_obj.name,
                    'section_name': section.name,
                    'message': 'Class teacher assigned successfully'
                }
            }, status=201)
            
        except Exception as e:
            return Response({'error': 'Failed to assign class teacher', 'status': 'error'}, status=500)

# Input: {
#   "teacher_id": 1,
#   "class_id": 1,
#   "section_id": 1
# }
class AdminClassListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, ClassesModulePermission]
    
    def get(self, request):
        try:
            classes = Class.objects.filter(is_active=True).order_by('name')
            
            classes_data = []
            for class_obj in classes:
                # Get sections count
                sections_count = Section.objects.filter(class_assigned=class_obj).count()
                # Get students count
                students_count = Student.objects.filter(class_assigned=class_obj, is_active=True).count()
                
                classes_data.append({
                    'id': class_obj.id,
                    'name': class_obj.name,
                    'description': class_obj.description,
                    'sections_count': sections_count,
                    'students_count': students_count,
                    'created_at': class_obj.created_at.isoformat()
                })
            
            return Response({'status': 'success', 'data': classes_data}, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to fetch classes', 'status': 'error'}, status=500)
    
    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            if not data.get('name'):
                return Response({'error': 'Class name is required', 'status': 'error'}, status=400)
            
            # Check if class already exists
            if Class.objects.filter(name=data['name']).exists():
                return Response({'error': 'Class name already exists', 'status': 'error'}, status=400)
            
            # Create class
            class_obj = Class.objects.create(
                name=data['name'],
                description=data.get('description', ''),
                created_by=request.user
            )
            
            return Response({
                'status': 'success',
                'data': {
                    'id': class_obj.id,
                    'name': class_obj.name,
                    'message': 'Class created successfully'
                }
            }, status=201)
            
        except Exception as e:
            return Response({'error': 'Failed to create class', 'status': 'error'}, status=500)

# Input POST: {
#   "name": "Class 10",
#   "description": "Tenth standard class"
# }

class AdminSectionListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, ClassesModulePermission]
    
    def get(self, request):
        try:
            class_id = request.GET.get('class_id')
            
            # Base queryset
            queryset = Section.objects.select_related('class_assigned')
            
            if class_id:
                queryset = queryset.filter(class_assigned_id=class_id)
            
            sections_data = []
            for section in queryset:
                # Get students count
                students_count = Student.objects.filter(
                    section=section,
                    is_active=True
                ).count()
                
                sections_data.append({
                    'id': section.id,
                    'name': section.name,
                    'class_name': section.class_assigned.name if section.class_assigned else None,
                    'capacity': section.capacity,
                    'students_count': students_count,
                    'created_at': section.created_at.isoformat()
                })
            
            return Response({'status': 'success', 'data': sections_data}, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to fetch sections', 'status': 'error'}, status=500)
    
    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['name', 'class_id']
            for field in required_fields:
                if not data.get(field):
                    return Response({'error': f'{field} is required', 'status': 'error'}, status=400)
            
            # Check if class exists
            class_obj = Class.objects.filter(id=data['class_id']).first()
            if not class_obj:
                return Response({'error': 'Class not found', 'status': 'error'}, status=404)
            
            # Check if section already exists for this class
            if Section.objects.filter(name=data['name'], class_assigned=class_obj).exists():
                return Response({'error': 'Section already exists for this class', 'status': 'error'}, status=400)
            
            # Create section
            section = Section.objects.create(
                name=data['name'],
                class_assigned=class_obj,
                capacity=data.get('capacity', 40),
                created_by=request.user
            )
            
            return Response({
                'status': 'success',
                'data': {
                    'id': section.id,
                    'name': section.name,
                    'class_name': class_obj.name,
                    'message': 'Section created successfully'
                }
            }, status=201)
            
        except Exception as e:
            return Response({'error': 'Failed to create section', 'status': 'error'}, status=500)

# Input POST: {
#   "name": "A",
#   "class_id": 1,
#   "capacity": 40
# }

class AdminSubjectListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, ClassesModulePermission]
    
    def get(self, request):
        try:
            class_id = request.GET.get('class_id')
            
            # Base queryset
            queryset = Subject.objects.all()
            
            if class_id:
                queryset = queryset.filter(classes__id=class_id)
            
            subjects_data = []
            for subject in queryset:
                subjects_data.append({
                    'id': subject.id,
                    'name': subject.name,
                    'code': subject.code,
                    'description': subject.description,
                    'is_optional': subject.is_optional,
                    'credits': subject.credits,
                    'created_at': subject.created_at.isoformat()
                })
            
            return Response({'status': 'success', 'data': subjects_data}, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to fetch subjects', 'status': 'error'}, status=500)
    
    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['name', 'code']
            for field in required_fields:
                if not data.get(field):
                    return Response({'error': f'{field} is required', 'status': 'error'}, status=400)
            
            # Check if subject code already exists
            if Subject.objects.filter(code=data['code']).exists():
                return Response({'error': 'Subject code already exists', 'status': 'error'}, status=400)
            
            # Create subject
            subject = Subject.objects.create(
                name=data['name'],
                code=data['code'],
                description=data.get('description', ''),
                is_optional=data.get('is_optional', False),
                credits=data.get('credits', 1),
                created_by=request.user
            )
            
            # Assign to classes if provided
            if data.get('class_ids'):
                classes = Class.objects.filter(id__in=data['class_ids'])
                subject.classes.set(classes)
            
            return Response({
                'status': 'success',
                'data': {
                    'id': subject.id,
                    'name': subject.name,
                    'code': subject.code,
                    'message': 'Subject created successfully'
                }
            }, status=201)
            
        except Exception as e:
            return Response({'error': 'Failed to create subject', 'status': 'error'}, status=500)

# Input POST: {
#   "name": "Mathematics",
#   "code": "MATH101",
#   "description": "Basic Mathematics",
#   "is_optional": false,
#   "credits": 4,
#   "class_ids": [1, 2, 3]
# }



class AdminAttendanceOverviewAPIView(APIView):
    permission_classes = [IsAuthenticated, AttendanceModulePermission]
    
    def get(self, request):
        try:
            # Query parameters
            date = request.GET.get('date', datetime.now().date())
            class_id = request.GET.get('class_id')
            section_id = request.GET.get('section_id')
            
            if isinstance(date, str):
                date = datetime.strptime(date, '%Y-%m-%d').date()
            
            # Base queryset for attendance
            attendance_queryset = Attendance.objects.filter(date=date)
            
            if class_id:
                attendance_queryset = attendance_queryset.filter(student__class_assigned_id=class_id)
            if section_id:
                attendance_queryset = attendance_queryset.filter(student__section_id=section_id)
            
            # Calculate statistics
            total_students = Student.objects.filter(is_active=True)
            if class_id:
                total_students = total_students.filter(class_assigned_id=class_id)
            if section_id:
                total_students = total_students.filter(section_id=section_id)
            
            total_count = total_students.count()
            present_count = attendance_queryset.filter(status='present').count()
            absent_count = attendance_queryset.filter(status='absent').count()
            late_count = attendance_queryset.filter(status='late').count()
            
            # Calculate percentage
            attendance_percentage = round((present_count / total_count) * 100, 2) if total_count > 0 else 0
            
            # Get class-wise breakdown
            class_breakdown = []
            classes = Class.objects.all()
            
            for class_obj in classes:
                class_attendance = Attendance.objects.filter(
                    date=date,
                    student__class_assigned=class_obj
                )
                class_total = Student.objects.filter(
                    class_assigned=class_obj,
                    is_active=True
                ).count()
                class_present = class_attendance.filter(status='present').count()
                
                if class_total > 0:
                    class_breakdown.append({
                        'class_id': class_obj.id,
                        'class_name': class_obj.name,
                        'total_students': class_total,
                        'present_students': class_present,
                        'absent_students': class_total - class_present,
                        'attendance_percentage': round((class_present / class_total) * 100, 2)
                    })
            
            return Response({
                'status': 'success',
                'data': {
                    'date': date.isoformat(),
                    'overall_statistics': {
                        'total_students': total_count,
                        'present_students': present_count,
                        'absent_students': absent_count,
                        'late_students': late_count,
                        'attendance_percentage': attendance_percentage
                    },
                    'class_breakdown': class_breakdown
                }
            }, status=200)
            
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD', 'status': 'error'}, status=400)
        except Exception as e:
            return Response({'error': 'Failed to fetch attendance overview', 'status': 'error'}, status=500)

# Input: GET /api/v1/admin/attendance/overview/?date=2025-09-06&class_id=1
# Output: {
#   "status": "success",
#   "data": {
#     "date": "2025-09-06",
#     "overall_statistics": {
#       "total_students": 50,
#       "present_students": 46,
#       "absent_students": 4,
#       "late_students": 0,
#       "attendance_percentage": 92.0
#     },
#     "class_breakdown": [...]
#   }
# }



class AdminBulkAttendanceAPIView(APIView):
    permission_classes = [IsAuthenticated, AttendanceModulePermission]
    
    def post(self, request):
        try:
            data = request.data
            attendance_list = data.get('attendance', [])
            
            if not attendance_list:
                return Response({'error': 'Attendance data list is required', 'status': 'error'}, status=400)
            
            # Validate data structure
            required_fields = ['student_id', 'date', 'status']
            success_count = 0
            errors = []
            
            for idx, record in enumerate(attendance_list):
                try:
                    # Validate required fields
                    for field in required_fields:
                        if not record.get(field):
                            errors.append(f'Record {idx + 1}: {field} is required')
                            continue
                    
                    # Validate date format
                    date = datetime.strptime(record['date'], '%Y-%m-%d').date()
                    
                    # Validate student exists
                    student = Student.objects.filter(id=record['student_id'], is_active=True).first()
                    if not student:
                        errors.append(f'Record {idx + 1}: Student not found')
                        continue
                    
                    # Validate status
                    valid_statuses = ['present', 'absent', 'late', 'excused']
                    if record['status'] not in valid_statuses:
                        errors.append(f'Record {idx + 1}: Invalid status. Must be one of {valid_statuses}')
                        continue
                    
                    # Create or update attendance
                    attendance_obj, created = Attendance.objects.update_or_create(
                        student=student,
                        date=date,
                        defaults={
                            'status': record['status'],
                            'remarks': record.get('remarks', ''),
                            'updated_by': request.user
                        }
                    )
                    success_count += 1
                    
                except ValueError:
                    errors.append(f'Record {idx + 1}: Invalid date format. Use YYYY-MM-DD')
                except Exception as e:
                    errors.append(f'Record {idx + 1}: {str(e)}')
            
            return Response({
                'status': 'success',
                'data': {
                    'total_records': len(attendance_list),
                    'success_count': success_count,
                    'error_count': len(errors),
                    'errors': errors[:10],  # Show first 10 errors
                    'message': f'Processed {success_count} attendance records successfully'
                }
            }, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to bulk mark attendance', 'status': 'error'}, status=500)

# Input: POST {
#   "attendance": [
#     {
#       "student_id": 1,
#       "date": "2025-09-06",
#       "status": "present",
#       "remarks": "On time"
#     },
#     {
#       "student_id": 2,
#       "date": "2025-09-06",
#       "status": "absent",
#       "remarks": "Sick leave"
#     }
#   ]
# }


class AttendanceReportsAPIView(APIView):
    permission_classes = [IsAuthenticated, AttendanceModulePermission]
    
    def get(self, request):
        try:
            # Query parameters
            student_id = request.GET.get('student_id')
            class_id = request.GET.get('class_id')
            section_id = request.GET.get('section_id')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            report_type = request.GET.get('type', 'detailed')  # detailed, summary, monthly
            page = int(request.GET.get('page', 1))
            limit = int(request.GET.get('limit', 50))
            
            # Base queryset
            queryset = Attendance.objects.select_related('student', 'student__class_assigned', 'student__section')
            
            # Apply filters
            if student_id:
                queryset = queryset.filter(student_id=student_id)
            if class_id:
                queryset = queryset.filter(student__class_assigned_id=class_id)
            if section_id:
                queryset = queryset.filter(student__section_id=section_id)
            if start_date:
                queryset = queryset.filter(date__gte=start_date)
            if end_date:
                queryset = queryset.filter(date__lte=end_date)
            
            if report_type == 'summary':
                # Summary report
                total_students = Student.objects.filter(is_active=True)
                if class_id:
                    total_students = total_students.filter(class_assigned_id=class_id)
                if section_id:
                    total_students = total_students.filter(section_id=section_id)
                
                total_count = total_students.count()
                present_count = queryset.filter(status='present').count()
                absent_count = queryset.filter(status='absent').count()
                late_count = queryset.filter(status='late').count()
                
                data = {
                    'summary': {
                        'total_students': total_count,
                        'present_students': present_count,
                        'absent_students': absent_count,
                        'late_students': late_count,
                        'attendance_percentage': round((present_count / (present_count + absent_count)) * 100, 2) if (present_count + absent_count) > 0 else 0
                    }
                }
            else:
                # Detailed report with pagination
                offset = (page - 1) * limit
                total_count = queryset.count()
                attendance_records = queryset.order_by('-date', 'student__full_name')[offset:offset + limit]
                
                attendance_data = []
                for attendance in attendance_records:
                    attendance_data.append({
                        'student_id': attendance.student.id,
                        'student_name': attendance.student.full_name,
                        'admission_number': attendance.student.admission_number,
                        'class_name': attendance.student.class_assigned.name if attendance.student.class_assigned else None,
                        'section_name': attendance.student.section.name if attendance.student.section else None,
                        'date': attendance.date.isoformat(),
                        'status': attendance.status,
                        'remarks': attendance.remarks,
                        'marked_by': attendance.updated_by.username if attendance.updated_by else None,
                        'marked_at': attendance.updated_at.isoformat()
                    })
                
                data = {
                    'attendance_records': attendance_data,
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total_count': total_count,
                        'has_next': offset + limit < total_count,
                        'has_previous': page > 1
                    }
                }
            
            return Response({'status': 'success', 'data': data}, status=200)
            
        except ValueError:
            return Response({'error': 'Invalid pagination parameters', 'status': 'error'}, status=400)
        except Exception as e:
            return Response({'error': 'Failed to fetch attendance reports', 'status': 'error'}, status=500)

# Input: GET /api/v1/admin/attendance/reports/?class_id=1&start_date=2025-09-01&end_date=2025-09-06&type=summary

# class AttendanceRegularizationAPIView(APIView):
#     permission_classes = [IsAuthenticated, AttendanceModulePermission]
    
#     def post(self, request):
#         try:
#             data = request.data
            
#             # Validate required fields
#             required_fields = ['student_id', 'date', 'reason']
#             for field in required_fields:
#                 if not data.get(field):
#                     return Response({'error': f'{field} is required', 'status': 'error'}, status=400)
            
#             # Validate date
#             try:
#                 date = datetime.strptime(data['date'], '%Y-%m-%d').date()
#             except ValueError:
#                 return Response({'error': 'Invalid date format. Use YYYY-MM-DD', 'status': 'error'}, status=400)
            
#             # Check if student exists
#             student = Student.objects.filter(id=data['student_id'], is_active=True).first()
#             if not student:
#                 return Response({'error': 'Student not found', 'status': 'error'}, status=404)
            
#             # Check if regularization already exists
#             existing = AttendanceRegularization.objects.filter(
#                 student=student,
#                 date=date
#             ).first()
            
#             if existing:
#                 return Response({'error': 'Regularization request for this date already exists', 'status': 'error'}, status=400)
            
#             # Check if date is within allowed range (e.g., last 30 days)
#             days_diff = (datetime.now().date() - date).days
#             if days_diff > 30:
#                 return Response({'error': 'Regularization can only be requested for last 30 days', 'status': 'error'}, status=400)
            
#             # Create regularization request
#             regularization = AttendanceRegularization.objects.create(
#                 student=student,
#                 date=date,
#                 reason=data['reason'],
#                 description=data.get('description', ''),
#                 requested_status=data.get('requested_status', 'present'),
#                 requested_by=request.user,
#                 status='pending'
#             )
            
#             return Response({
#                 'status': 'success',
#                 'data': {
#                     'id': regularization.id,
#                     'student_name': student.full_name,
#                     'date': date.isoformat(),
#                     'reason': regularization.reason,
#                     'status': regularization.status,
#                     'message': 'Regularization request submitted successfully'
#                 }
#             }, status=201)
            
#         except Exception as e:
#             return Response({'error': 'Failed to submit regularization request', 'status': 'error'}, status=500)
    
#     def get(self, request):
#         try:
#             # Get regularization requests
#             student_id = request.GET.get('student_id')
#             status = request.GET.get('status')  # pending, approved, rejected
            
#             queryset = AttendanceRegularization.objects.select_related('student')
            
#             if student_id:
#                 queryset = queryset.filter(student_id=student_id)
#             if status:
#                 queryset = queryset.filter(status=status)
            
#             regularizations = []
#             for reg in queryset.order_by('-created_at'):
#                 regularizations.append({
#                     'id': reg.id,
#                     'student_name': reg.student.full_name,
#                     'date': reg.date.isoformat(),
#                     'reason': reg.reason,
#                     'description': reg.description,
#                     'requested_status': reg.requested_status,
#                     'status': reg.status,
#                     'requested_by': reg.requested_by.username,
#                     'created_at': reg.created_at.isoformat(),
#                     'approved_by': reg.approved_by.username if reg.approved_by else None,
#                     'approved_at': reg.approved_at.isoformat() if reg.approved_at else None
#                 })
            
#             return Response({'status': 'success', 'data': regularizations}, status=200)
            
#         except Exception as e:
#             return Response({'error': 'Failed to fetch regularization requests', 'status': 'error'}, status=500)

# Input POST: {
#   "student_id": 1,
#   "date": "2025-09-05",
#   "reason": "Medical emergency",
#   "description": "Had to visit doctor for fever",
#   "requested_status": "present"
# }

class AdminFeeStructureAPIView(APIView):
    permission_classes = [IsAuthenticated, FeesModulePermission]
    
    def get(self, request, pk=None):
        try:
            if pk:
                # Get single fee structure
                fee_structure = FeeStructure.objects.prefetch_related('applicable_classes').filter(id=pk).first()
                if not fee_structure:
                    return Response({'error': 'Fee structure not found', 'status': 'error'}, status=404)
                
                data = {
                    'id': fee_structure.id,
                    'name': fee_structure.name,
                    'amount': float(fee_structure.amount),
                    'fee_type': fee_structure.fee_type,
                    'description': fee_structure.description,
                    'applicable_classes': [
                        {'id': cls.id, 'name': cls.name} 
                        for cls in fee_structure.applicable_classes.all()
                    ],
                    'due_date': fee_structure.due_date.isoformat() if fee_structure.due_date else None,
                    'late_fee_amount': float(fee_structure.late_fee_amount) if fee_structure.late_fee_amount else 0,
                    'is_active': fee_structure.is_active,
                    'created_at': fee_structure.created_at.isoformat()
                }
            else:
                # Get all fee structures
                fee_structures = FeeStructure.objects.prefetch_related('applicable_classes').filter(is_active=True)
                
                data = []
                for fee in fee_structures:
                    data.append({
                        'id': fee.id,
                        'name': fee.name,
                        'amount': float(fee.amount),
                        'fee_type': fee.fee_type,
                        'applicable_classes_count': fee.applicable_classes.count(),
                        'due_date': fee.due_date.isoformat() if fee.due_date else None,
                        'is_active': fee.is_active,
                        'created_at': fee.created_at.isoformat()
                    })
            
            return Response({'status': 'success', 'data': data}, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to fetch fee structure', 'status': 'error'}, status=500)
    
    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['name', 'amount', 'fee_type']
            for field in required_fields:
                if not data.get(field):
                    return Response({'error': f'{field} is required', 'status': 'error'}, status=400)
            
            # Validate amount
            try:
                amount = float(data['amount'])
                if amount < 0:
                    return Response({'error': 'Amount must be positive', 'status': 'error'}, status=400)
            except (ValueError, TypeError):
                return Response({'error': 'Invalid amount format', 'status': 'error'}, status=400)
            
            # Validate fee type
            valid_fee_types = ['tuition', 'admission', 'library', 'transport', 'examination', 'laboratory', 'other']
            if data['fee_type'] not in valid_fee_types:
                return Response({'error': f'Invalid fee type. Must be one of {valid_fee_types}', 'status': 'error'}, status=400)
            
            # Create fee structure
            fee_structure = FeeStructure.objects.create(
                name=data['name'],
                amount=amount,
                fee_type=data['fee_type'],
                description=data.get('description', ''),
                due_date=data.get('due_date'),
                late_fee_amount=data.get('late_fee_amount', 0),
                created_by=request.user
            )
            
            # Assign to classes if provided
            if data.get('applicable_class_ids'):
                classes = Class.objects.filter(id__in=data['applicable_class_ids'])
                fee_structure.applicable_classes.set(classes)
            
            return Response({
                'status': 'success',
                'data': {
                    'id': fee_structure.id,
                    'name': fee_structure.name,
                    'amount': float(fee_structure.amount),
                    'message': 'Fee structure created successfully'
                }
            }, status=201)
            
        except Exception as e:
            return Response({'error': 'Failed to create fee structure', 'status': 'error'}, status=500)

# Input POST: {
#   "name": "Annual Tuition Fee",
#   "amount": 25000.00,
#   "fee_type": "tuition",
#   "description": "Annual tuition fee for academic year 2025-26",
#   "due_date": "2025-12-31",
#   "late_fee_amount": 500.00,
#   "applicable_class_ids": [1, 2, 3]
# }

class FeeCollectionAPIView(APIView):
    permission_classes = [IsAuthenticated, FeesModulePermission]
    
    def get(self, request):
        try:
            # Query parameters
            student_id = request.GET.get('student_id')
            class_id = request.GET.get('class_id')
            fee_type = request.GET.get('fee_type')
            status = request.GET.get('status')  # pending, paid, overdue
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            page = int(request.GET.get('page', 1))
            limit = int(request.GET.get('limit', 20))
            
            # Base queryset
            queryset = FeeStructure.objects.select_related('student', 'fee_structure')
            
            # Apply filters
            if student_id:
                queryset = queryset.filter(student_id=student_id)
            if class_id:
                queryset = queryset.filter(student__class_assigned_id=class_id)
            if fee_type:
                queryset = queryset.filter(fee_structure__fee_type=fee_type)
            if status:
                queryset = queryset.filter(status=status)
            if start_date:
                queryset = queryset.filter(created_at__date__gte=start_date)
            if end_date:
                queryset = queryset.filter(created_at__date__lte=end_date)
            
            # Pagination
            offset = (page - 1) * limit
            total_count = queryset.count()
            collections = queryset.order_by('-created_at')[offset:offset + limit]
            
            # Calculate totals
            total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0
            paid_amount = queryset.filter(status='paid').aggregate(total=Sum('amount_paid'))['total'] or 0
            pending_amount = queryset.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
            
            collections_data = []
            for collection in collections:
                collections_data.append({
                    'id': collection.id,
                    'student_id': collection.student.id,
                    'student_name': collection.student.full_name,
                    'admission_number': collection.student.admission_number,
                    'fee_structure_name': collection.fee_structure.name,
                    'fee_type': collection.fee_structure.fee_type,
                    'amount': float(collection.amount),
                    'amount_paid': float(collection.amount_paid or 0),
                    'remaining_amount': float(collection.amount - (collection.amount_paid or 0)),
                    'status': collection.status,
                    'due_date': collection.due_date.isoformat() if collection.due_date else None,
                    'payment_date': collection.payment_date.isoformat() if collection.payment_date else None,
                    'payment_method': collection.payment_method,
                    'transaction_id': collection.transaction_id,
                    'created_at': collection.created_at.isoformat()
                })
            
            return Response({
                'status': 'success',
                'data': {
                    'collections': collections_data,
                    'summary': {
                        'total_amount': float(total_amount),
                        'paid_amount': float(paid_amount),
                        'pending_amount': float(pending_amount)
                    },
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total_count': total_count,
                        'has_next': offset + limit < total_count
                    }
                }
            }, status=200)
            
        except ValueError:
            return Response({'error': 'Invalid pagination parameters', 'status': 'error'}, status=400)
        except Exception as e:
            return Response({'error': 'Failed to fetch fee collections', 'status': 'error'}, status=500)
    
    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['student_id', 'amount_paid', 'payment_method']
            for field in required_fields:
                if not data.get(field):
                    return Response({'error': f'{field} is required', 'status': 'error'}, status=400)
            
            # Validate student
            student = Student.objects.filter(id=data['student_id'], is_active=True).first()
            if not student:
                return Response({'error': 'Student not found', 'status': 'error'}, status=404)
            
            # Validate amount
            try:
                amount_paid = float(data['amount_paid'])
                if amount_paid <= 0:
                    return Response({'error': 'Amount must be positive', 'status': 'error'}, status=400)
            except (ValueError, TypeError):
                return Response({'error': 'Invalid amount format', 'status': 'error'}, status=400)
            
            # Find pending fee collection or create new one
            collection_id = data.get('collection_id')
            if collection_id:
                collection = FeeStructure.objects.filter(id=collection_id, student=student).first()
                if not collection:
                    return Response({'error': 'Fee collection record not found', 'status': 'error'}, status=404)
            else:
                return Response({'error': 'collection_id is required', 'status': 'error'}, status=400)
            
            # Update payment
            collection.amount_paid = (collection.amount_paid or 0) + amount_paid
            collection.payment_date = datetime.now().date()
            collection.payment_method = data['payment_method']
            collection.transaction_id = data.get('transaction_id')
            collection.remarks = data.get('remarks', '')
            
            # Update status
            if collection.amount_paid >= collection.amount:
                collection.status = 'paid'
            else:
                collection.status = 'partial'
            
            collection.collected_by = request.user
            collection.save()
            
            return Response({
                'status': 'success',
                'data': {
                    'collection_id': collection.id,
                    'student_name': student.full_name,
                    'amount_paid': float(amount_paid),
                    'remaining_amount': float(collection.amount - collection.amount_paid),
                    'status': collection.status,
                    'message': 'Payment recorded successfully'
                }
            }, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to record payment', 'status': 'error'}, status=500)

# Input POST: {
#   "collection_id": 1,
#   "student_id": 1,
#   "amount_paid": 5000.00,
#   "payment_method": "cash",
#   "transaction_id": "TXN123456",
#   "remarks": "Partial payment for tuition fee"
# }


class FeeReportsAPIView(APIView):
    permission_classes = [IsAuthenticated, FeesModulePermission]
    
    def get(self, request):
        try:
            # Query parameters
            report_type = request.GET.get('type', 'summary')  # summary, detailed, defaulters
            class_id = request.GET.get('class_id')
            fee_type = request.GET.get('fee_type')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            # Base queryset
            queryset = FeeStructure.objects.select_related('student', 'fee_structure')
            
            # Apply date filters
            if start_date:
                queryset = queryset.filter(created_at__date__gte=start_date)
            if end_date:
                queryset = queryset.filter(created_at__date__lte=end_date)
            
            if class_id:
                queryset = queryset.filter(student__class_assigned_id=class_id)
            if fee_type:
                queryset = queryset.filter(fee_structure__fee_type=fee_type)
            
            if report_type == 'summary':
                # Summary report
                total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0
                paid_amount = queryset.filter(status='paid').aggregate(total=Sum('amount_paid'))['total'] or 0
                pending_amount = queryset.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
                overdue_amount = queryset.filter(
                    status='pending',
                    due_date__lt=datetime.now().date()
                ).aggregate(total=Sum('amount'))['total'] or 0
                
                # Collection by fee type
                fee_type_summary = queryset.values('fee_structure__fee_type').annotate(
                    total_amount=Sum('amount'),
                    paid_amount=Sum('amount_paid', filter=Q(status='paid')),
                    pending_amount=Sum('amount', filter=Q(status='pending'))
                )
                
                data = {
                    'overall_summary': {
                        'total_amount': float(total_amount),
                        'paid_amount': float(paid_amount),
                        'pending_amount': float(pending_amount),
                        'overdue_amount': float(overdue_amount),
                        'collection_percentage': round((paid_amount / total_amount) * 100, 2) if total_amount > 0 else 0
                    },
                    'fee_type_summary': [
                        {
                            'fee_type': item['fee_structure__fee_type'],
                            'total_amount': float(item['total_amount'] or 0),
                            'paid_amount': float(item['paid_amount'] or 0),
                            'pending_amount': float(item['pending_amount'] or 0)
                        }
                        for item in fee_type_summary
                    ]
                }
                
            elif report_type == 'defaulters':
                # Defaulters report (overdue payments)
                defaulters = queryset.filter(
                    status='pending',
                    due_date__lt=datetime.now().date()
                ).order_by('due_date')
                
                defaulters_data = []
                for collection in defaulters:
                    overdue_days = (datetime.now().date() - collection.due_date).days
                    defaulters_data.append({
                        'student_id': collection.student.id,
                        'student_name': collection.student.full_name,
                        'admission_number': collection.student.admission_number,
                        'class_name': collection.student.class_assigned.name if collection.student.class_assigned else None,
                        'fee_type': collection.fee_structure.fee_type,
                        'amount': float(collection.amount),
                        'due_date': collection.due_date.isoformat(),
                        'overdue_days': overdue_days,
                        'parent_phone': collection.student.parent_phone
                    })
                
                data = {
                    'defaulters': defaulters_data,
                    'total_defaulters': len(defaulters_data),
                    'total_overdue_amount': float(sum(item['amount'] for item in defaulters_data))
                }
                
            else:
                # Detailed report
                collections = queryset.order_by('-created_at')[:100]  # Limit to 100 records
                
                detailed_data = []
                for collection in collections:
                    detailed_data.append({
                        'collection_id': collection.id,
                        'student_name': collection.student.full_name,
                        'admission_number': collection.student.admission_number,
                        'fee_structure_name': collection.fee_structure.name,
                        'fee_type': collection.fee_structure.fee_type,
                        'amount': float(collection.amount),
                        'amount_paid': float(collection.amount_paid or 0),
                        'status': collection.status,
                        'payment_date': collection.payment_date.isoformat() if collection.payment_date else None,
                        'payment_method': collection.payment_method,
                        'collected_by': collection.collected_by.username if collection.collected_by else None
                    })
                
                data = {'detailed_collections': detailed_data}
            
            return Response({'status': 'success', 'data': data}, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to generate fee reports', 'status': 'error'}, status=500)

# Input: GET /api/v1/admin/fee-reports/?type=summary&start_date=2025-09-01&end_date=2025-09-06

class FeeDiscountAPIView(APIView):
    permission_classes = [IsAuthenticated, FeesModulePermission]
    
    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['student_id', 'discount_type', 'discount_value']
            for field in required_fields:
                if not data.get(field):
                    return Response({'error': f'{field} is required', 'status': 'error'}, status=400)
            
            # Validate student
            student = Student.objects.filter(id=data['student_id'], is_active=True).first()
            if not student:
                return Response({'error': 'Student not found', 'status': 'error'}, status=404)
            
            # Validate discount type and value
            discount_type = data['discount_type']  # percentage, fixed_amount
            discount_value = data['discount_value']
            
            if discount_type not in ['percentage', 'fixed_amount']:
                return Response({'error': 'Invalid discount type. Must be percentage or fixed_amount', 'status': 'error'}, status=400)
            
            try:
                discount_value = float(discount_value)
                if discount_value <= 0:
                    return Response({'error': 'Discount value must be positive', 'status': 'error'}, status=400)
                
                if discount_type == 'percentage' and discount_value > 100:
                    return Response({'error': 'Percentage discount cannot exceed 100%', 'status': 'error'}, status=400)
                    
            except (ValueError, TypeError):
                return Response({'error': 'Invalid discount value format', 'status': 'error'}, status=400)
            
            # Create discount
            discount = FeeConcession.objects.create(
                student=student,
                discount_type=discount_type,
                discount_value=discount_value,
                reason=data.get('reason', ''),
                description=data.get('description', ''),
                applicable_fee_types=data.get('applicable_fee_types', []),
                valid_from=data.get('valid_from', datetime.now().date()),
                valid_until=data.get('valid_until'),
                created_by=request.user
            )
            
            return Response({
                'status': 'success',
                'data': {
                    'discount_id': discount.id,
                    'student_name': student.full_name,
                    'discount_type': discount_type,
                    'discount_value': float(discount_value),
                    'reason': discount.reason,
                    'message': 'Discount created successfully'
                }
            }, status=201)
            
        except Exception as e:
            return Response({'error': 'Failed to create fee discount', 'status': 'error'}, status=500)
    
    def get(self, request):
        try:
            student_id = request.GET.get('student_id')
            
            queryset = FeeConcession.objects.select_related('student').filter(is_active=True)
            
            if student_id:
                queryset = queryset.filter(student_id=student_id)
            
            discounts_data = []
            for discount in queryset.order_by('-created_at'):
                discounts_data.append({
                    'id': discount.id,
                    'student_name': discount.student.full_name,
                    'discount_type': discount.discount_type,
                    'discount_value': float(discount.discount_value),
                    'reason': discount.reason,
                    'applicable_fee_types': discount.applicable_fee_types,
                    'valid_from': discount.valid_from.isoformat(),
                    'valid_until': discount.valid_until.isoformat() if discount.valid_until else None,
                    'created_by': discount.created_by.username,
                    'created_at': discount.created_at.isoformat()
                })
            
            return Response({'status': 'success', 'data': discounts_data}, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to fetch fee discounts', 'status': 'error'}, status=500)

# Input POST: {
#   "student_id": 1,
#   "discount_type": "percentage",
#   "discount_value": 20.0,
#   "reason": "Merit scholarship",
#   "description": "20% discount on tuition fee for academic excellence",
#   "applicable_fee_types": ["tuition"],
#   "valid_from": "2025-09-01",
#   "valid_until": "2026-08-31"
# }

class AdminExamAPIView(APIView):
    permission_classes = [IsAuthenticated, ExaminationsModulePermission]
    
    def get(self, request, pk=None):
        try:
            if pk:
                # Get single exam
                exam = ExamType.objects.prefetch_related('exam_subjects__subject', 'exam_subjects__class_assigned').filter(id=pk).first()
                if not exam:
                    return Response({'error': 'Exam not found', 'status': 'error'}, status=404)
                
                exam_subjects = []
                for exam_subject in exam.exam_subjects.all():
                    exam_subjects.append({
                        'subject_id': exam_subject.subject.id,
                        'subject_name': exam_subject.subject.name,
                        'class_id': exam_subject.class_assigned.id,
                        'class_name': exam_subject.class_assigned.name,
                        'exam_date': exam_subject.exam_date.isoformat() if exam_subject.exam_date else None,
                        'start_time': exam_subject.start_time.strftime('%H:%M') if exam_subject.start_time else None,
                        'end_time': exam_subject.end_time.strftime('%H:%M') if exam_subject.end_time else None,
                        'max_marks': exam_subject.max_marks,
                        'duration_minutes': exam_subject.duration_minutes
                    })
                
                data = {
                    'id': exam.id,
                    'name': exam.name,
                    'exam_type': exam.exam_type,
                    'start_date': exam.start_date.isoformat() if exam.start_date else None,
                    'end_date': exam.end_date.isoformat() if exam.end_date else None,
                    'description': exam.description,
                    'instructions': exam.instructions,
                    'is_active': exam.is_active,
                    'exam_subjects': exam_subjects,
                    'created_at': exam.created_at.isoformat()
                }
            else:
                # Get all exams
                exams = ExamType.objects.all().order_by('-created_at')
                
                data = []
                for exam in exams:
                    subjects_count = ExamType.objects.filter(exam=exam).count()
                    data.append({
                        'id': exam.id,
                        'name': exam.name,
                        'exam_type': exam.exam_type,
                        'start_date': exam.start_date.isoformat() if exam.start_date else None,
                        'end_date': exam.end_date.isoformat() if exam.end_date else None,
                        'subjects_count': subjects_count,
                        'is_active': exam.is_active,
                        'created_at': exam.created_at.isoformat()
                    })
            
            return Response({'status': 'success', 'data': data}, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to fetch exams', 'status': 'error'}, status=500)
    
    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['name', 'exam_type']
            for field in required_fields:
                if not data.get(field):
                    return Response({'error': f'{field} is required', 'status': 'error'}, status=400)
            
            # Validate exam type
            valid_exam_types = ['mid_term', 'final', 'unit_test', 'quarterly', 'half_yearly', 'annual']
            if data['exam_type'] not in valid_exam_types:
                return Response({'error': f'Invalid exam type. Must be one of {valid_exam_types}', 'status': 'error'}, status=400)
            
            # Create exam
            exam = ExamType.objects.create(
                name=data['name'],
                exam_type=data['exam_type'],
                start_date=data.get('start_date'),
                end_date=data.get('end_date'),
                description=data.get('description', ''),
                instructions=data.get('instructions', ''),
                created_by=request.user
            )
            
            # Add exam subjects if provided
            if data.get('subjects'):
                for subject_data in data['subjects']:
                    ExamType.objects.create(
                        exam=exam,
                        subject_id=subject_data['subject_id'],
                        class_assigned_id=subject_data['class_id'],
                        exam_date=subject_data.get('exam_date'),
                        start_time=subject_data.get('start_time'),
                        end_time=subject_data.get('end_time'),
                        max_marks=subject_data.get('max_marks', 100),
                        duration_minutes=subject_data.get('duration_minutes', 180)
                    )
            
            return Response({
                'status': 'success',
                'data': {
                    'exam_id': exam.id,
                    'name': exam.name,
                    'exam_type': exam.exam_type,
                    'message': 'Exam created successfully'
                }
            }, status=201)
            
        except Exception as e:
            return Response({'error': 'Failed to create exam', 'status': 'error'}, status=500)

# Input POST: {
#   "name": "Mid Term Examination 2025",
#   "exam_type": "mid_term",
#   "start_date": "2025-10-15",
#   "end_date": "2025-10-25",
#   "description": "Mid term exam for all classes",
#   "subjects": [
#     {
#       "subject_id": 1,
#       "class_id": 1,
#       "exam_date": "2025-10-15",
#       "start_time": "10:00",
#       "end_time": "13:00",
#       "max_marks": 100,
#       "duration_minutes": 180
#     }
#   ]
# }

class UploadExamMarksAPIView(APIView):
    permission_classes = [IsAuthenticated, ExaminationsModulePermission]
    
    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            if not data.get('exam_id'):
                return Response({'error': 'exam_id is required', 'status': 'error'}, status=400)
            
            marks_data = data.get('marks', [])
            if not marks_data:
                return Response({'error': 'marks data is required', 'status': 'error'}, status=400)
            
            # Validate exam exists
            exam = Exam.objects.filter(id=data['exam_id']).first()
            if not exam:
                return Response({'error': 'Exam not found', 'status': 'error'}, status=404)
            
            success_count = 0
            errors = []
            
            for idx, mark_record in enumerate(marks_data):
                try:
                    # Validate required fields in mark record
                    required_fields = ['student_id', 'subject_id', 'marks_obtained']
                    for field in required_fields:
                        if field not in mark_record:
                            errors.append(f'Record {idx + 1}: {field} is required')
                            continue
                    
                    student_id = mark_record['student_id']
                    subject_id = mark_record['subject_id']
                    marks_obtained = mark_record['marks_obtained']
                    
                    # Validate student exists
                    student = Student.objects.filter(id=student_id, is_active=True).first()
                    if not student:
                        errors.append(f'Record {idx + 1}: Student not found')
                        continue
                    
                    # Validate subject exists
                    subject = Subject.objects.filter(id=subject_id).first()
                    if not subject:
                        errors.append(f'Record {idx + 1}: Subject not found')
                        continue
                    
                    # Validate marks
                    try:
                        marks_obtained = float(marks_obtained)
                        max_marks = float(mark_record.get('max_marks', 100))
                        
                        if marks_obtained < 0 or marks_obtained > max_marks:
                            errors.append(f'Record {idx + 1}: Invalid marks. Must be between 0 and {max_marks}')
                            continue
                            
                    except (ValueError, TypeError):
                        errors.append(f'Record {idx + 1}: Invalid marks format')
                        continue
                    
                    # Calculate grade
                    grade = self.calculate_grade(marks_obtained, max_marks)
                    
                    # Create or update exam result
                    exam_result, created = ExamResult.objects.update_or_create(
                        exam=exam,
                        student=student,
                        subject=subject,
                        defaults={
                            'marks_obtained': marks_obtained,
                            'max_marks': max_marks,
                            'grade': grade,
                            'percentage': round((marks_obtained / max_marks) * 100, 2),
                            'remarks': mark_record.get('remarks', ''),
                            'updated_by': request.user
                        }
                    )
                    
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f'Record {idx + 1}: {str(e)}')
            
            return Response({
                'status': 'success',
                'data': {
                    'exam_name': exam.name,
                    'total_records': len(marks_data),
                    'success_count': success_count,
                    'error_count': len(errors),
                    'errors': errors[:10],  # Show first 10 errors
                    'message': f'Successfully uploaded marks for {success_count} students'
                }
            }, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to upload exam marks', 'status': 'error'}, status=500)
    
    def calculate_grade(self, marks_obtained, max_marks):
        """Calculate grade based on percentage"""
        percentage = (marks_obtained / max_marks) * 100
        
        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B+'
        elif percentage >= 60:
            return 'B'
        elif percentage >= 50:
            return 'C+'
        elif percentage >= 40:
            return 'C'
        elif percentage >= 33:
            return 'D'
        else:
            return 'F'

# Input POST: {
#   "exam_id": 1,
#   "marks": [
#     {
#       "student_id": 1,
#       "subject_id": 1,
#       "marks_obtained": 85,
#       "max_marks": 100,
#       "remarks": "Good performance"
#     },
#     {
#       "student_id": 2,
#       "subject_id": 1,
#       "marks_obtained": 92,
#       "max_marks": 100,
#       "remarks": "Excellent"
#     }
#   ]
# }

class ExamResultsAPIView(APIView):
    permission_classes = [IsAuthenticated, ExaminationsModulePermission]
    
    def get(self, request):
        try:
            # Query parameters
            exam_id = request.GET.get('exam_id')
            student_id = request.GET.get('student_id')
            class_id = request.GET.get('class_id')
            subject_id = request.GET.get('subject_id')
            
            if not exam_id:
                return Response({'error': 'exam_id parameter is required', 'status': 'error'}, status=400)
            
            # Validate exam exists
            exam = ExamType.objects.filter(id=exam_id).first()
            if not exam:
                return Response({'error': 'Exam not found', 'status': 'error'}, status=404)
            
            # Base queryset
            queryset = ExamResult.objects.select_related('student', 'subject').filter(exam_id=exam_id)
            
            # Apply filters
            if student_id:
                queryset = queryset.filter(student_id=student_id)
            if class_id:
                queryset = queryset.filter(student__class_assigned_id=class_id)
            if subject_id:
                queryset = queryset.filter(subject_id=subject_id)
            
            # If specific student requested, return detailed results
            if student_id:
                results_data = []
                student_results = queryset.order_by('subject__name')
                
                total_marks = 0
                total_max_marks = 0
                
                for result in student_results:
                    results_data.append({
                        'subject_name': result.subject.name,
                        'marks_obtained': result.marks_obtained,
                        'max_marks': result.max_marks,
                        'percentage': result.percentage,
                        'grade': result.grade,
                        'remarks': result.remarks
                    })
                    
                    total_marks += result.marks_obtained
                    total_max_marks += result.max_marks
                
                overall_percentage = round((total_marks / total_max_marks) * 100, 2) if total_max_marks > 0 else 0
                overall_grade = self.calculate_overall_grade(overall_percentage)
                
                student = Student.objects.get(id=student_id)
                data = {
                    'student_info': {
                        'student_id': student.id,
                        'student_name': student.full_name,
                        'admission_number': student.admission_number,
                        'class_name': student.class_assigned.name if student.class_assigned else None
                    },
                    'exam_info': {
                        'exam_id': exam.id,
                        'exam_name': exam.name,
                        'exam_type': exam.exam_type
                    },
                    'subject_results': results_data,
                    'overall_result': {
                        'total_marks': total_marks,
                        'total_max_marks': total_max_marks,
                        'overall_percentage': overall_percentage,
                        'overall_grade': overall_grade,
                        'result_status': 'Pass' if overall_percentage >= 33 else 'Fail'
                    }
                }
            else:
                # Return class/exam summary
                results = queryset.order_by('student__full_name', 'subject__name')
                
                # Group by student
                students_results = {}
                for result in results:
                    student_id = result.student.id
                    if student_id not in students_results:
                        students_results[student_id] = {
                            'student_info': {
                                'student_id': result.student.id,
                                'student_name': result.student.full_name,
                                'admission_number': result.student.admission_number,
                                'class_name': result.student.class_assigned.name if result.student.class_assigned else None
                            },
                            'subjects': [],
                            'total_marks': 0,
                            'total_max_marks': 0
                        }
                    
                    students_results[student_id]['subjects'].append({
                        'subject_name': result.subject.name,
                        'marks_obtained': result.marks_obtained,
                        'max_marks': result.max_marks,
                        'percentage': result.percentage,
                        'grade': result.grade
                    })
                    
                    students_results[student_id]['total_marks'] += result.marks_obtained
                    students_results[student_id]['total_max_marks'] += result.max_marks
                
                # Calculate overall results for each student
                results_summary = []
                for student_data in students_results.values():
                    overall_percentage = round(
                        (student_data['total_marks'] / student_data['total_max_marks']) * 100, 2
                    ) if student_data['total_max_marks'] > 0 else 0
                    
                    results_summary.append({
                        'student_info': student_data['student_info'],
                        'total_marks': student_data['total_marks'],
                        'total_max_marks': student_data['total_max_marks'],
                        'overall_percentage': overall_percentage,
                        'overall_grade': self.calculate_overall_grade(overall_percentage),
                        'result_status': 'Pass' if overall_percentage >= 33 else 'Fail',
                        'subjects_count': len(student_data['subjects'])
                    })
                
                data = {
                    'exam_info': {
                        'exam_id': exam.id,
                        'exam_name': exam.name,
                        'exam_type': exam.exam_type
                    },
                    'results_summary': sorted(results_summary, key=lambda x: x['overall_percentage'], reverse=True),
                    'statistics': {
                        'total_students': len(results_summary),
                        'passed_students': len([r for r in results_summary if r['result_status'] == 'Pass']),
                        'failed_students': len([r for r in results_summary if r['result_status'] == 'Fail']),
                        'pass_percentage': round(
                            (len([r for r in results_summary if r['result_status'] == 'Pass']) / len(results_summary)) * 100, 2
                        ) if results_summary else 0
                    }
                }
            
            return Response({'status': 'success', 'data': data}, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to fetch exam results', 'status': 'error'}, status=500)
    
    def calculate_overall_grade(self, percentage):
        """Calculate overall grade based on percentage"""
        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B+'
        elif percentage >= 60:
            return 'B'
        elif percentage >= 50:
            return 'C+'
        elif percentage >= 40:
            return 'C'
        elif percentage >= 33:
            return 'D'
        else:
            return 'F'

# Input: GET /api/v1/admin/exams/results/?exam_id=1&student_id=1

# class GenerateReportCardsAPIView(APIView):
#     permission_classes = [IsAuthenticated, ExaminationsModulePermission]
    
#     def post(self, request):
#         try:
#             data = request.data
            
#             # Validate required fields
#             exam_id = data.get('exam_id')
#             if not exam_id:
#                 return Response({'error': 'exam_id is required', 'status': 'error'}, status=400)
            
#             # Validate exam exists
#             exam = ExamType.objects.filter(id=exam_id).first()
#             if not exam:
#                 return Response({'error': 'Exam not found', 'status': 'error'}, status=404)
            
#             # Get optional filters
#             class_id = data.get('class_id')
#             student_ids = data.get('student_ids', [])
            
#             # Build queryset for students
#             students_queryset = Student.objects.filter(is_active=True)
            
#             if class_id:
#                 students_queryset = students_queryset.filter(class_assigned_id=class_id)
#             if student_ids:
#                 students_queryset = students_queryset.filter(id__in=student_ids)
            
#             students = students_queryset.select_related('class_assigned', 'section')
            
#             if not students.exists():
#                 return Response({'error': 'No students found for the given criteria', 'status': 'error'}, status=400)
            
#             # Generate report cards
#             generated_count = 0
#             errors = []
#             report_cards = []
            
#             for student in students:
#                 try:
#                     # Get student's exam results
#                     results = ExamResult.objects.filter(
#                         exam=exam,
#                         student=student
#                     ).select_related('subject')
                    
#                     if not results.exists():
#                         errors.append(f'No results found for student {student.full_name}')
#                         continue
                    
#                     # Calculate totals
#                     total_marks = sum(result.marks_obtained for result in results)
#                     total_max_marks = sum(result.max_marks for result in results)
#                     overall_percentage = round((total_marks / total_max_marks) * 100, 2) if total_max_marks > 0 else 0
#                     overall_grade = self.calculate_overall_grade(overall_percentage)
                    
#                     # Prepare subject-wise results
#                     subject_results = []
#                     for result in results.order_by('subject__name'):
#                         subject_results.append({
#                             'subject_name': result.subject.name,
#                             'marks_obtained': result.marks_obtained,
#                             'max_marks': result.max_marks,
#                             'percentage': result.percentage,
#                             'grade': result.grade,
#                             'remarks': result.remarks
#                         })
                    
#                     # Create/update report card record
#                     report_card, created = Re.objects.update_or_create(
#                         exam=exam,
#                         student=student,
#                         defaults={
#                             'total_marks': total_marks,
#                             'total_max_marks': total_max_marks,
#                             'overall_percentage': overall_percentage,
#                             'overall_grade': overall_grade,
#                             'result_status': 'Pass' if overall_percentage >= 33 else 'Fail',
#                             'generated_by': request.user,
#                             'generated_at': datetime.now()
#                         }
#                     )
                    
#                     report_cards.append({
#                         'report_card_id': report_card.id,
#                         'student_id': student.id,
#                         'student_name': student.full_name,
#                         'overall_percentage': overall_percentage,
#                         'overall_grade': overall_grade,
#                         'result_status': report_card.result_status
#                     })
                    
#                     generated_count += 1
                    
#                 except Exception as e:
#                     errors.append(f'Error generating report card for {student.full_name}: {str(e)}')
            
#             # In a real implementation, you might trigger a background job to generate PDF files
#             # or send notifications to parents
            
#             return Response({
#                 'status': 'success',
#                 'data': {
#                     'exam_name': exam.name,
#                     'total_students': students.count(),
#                     'generated_count': generated_count,
#                     'error_count': len(errors),
#                     'errors': errors[:5],  # Show first 5 errors
#                     'report_cards': report_cards,
#                     'message': f'Successfully generated {generated_count} report cards'
#                 }
#             }, status=200)
            
#         except Exception as e:
#             return Response({'error': 'Failed to generate report cards', 'status': 'error'}, status=500)
    
#     def calculate_overall_grade(self, percentage):
#         """Calculate overall grade based on percentage"""
#         if percentage >= 90:
#             return 'A+'
#         elif percentage >= 80:
#             return 'A'
#         elif percentage >= 70:
#             return 'B+'
#         elif percentage >= 60:
#             return 'B'
#         elif percentage >= 50:
#             return 'C+'
#         elif percentage >= 40:
#             return 'C'
#         elif percentage >= 33:
#             return 'D'
#         else:
#             return 'F'

# Input POST: {
#   "exam_id": 1,
#   "class_id": 1,
#   "student_ids": [1, 2, 3]
# }

# class AdminAssignmentAPIView(APIView):
#     permission_classes = [IsAuthenticated, AssignmentsModulePermission]
    
#     def get(self, request, pk=None):
#         try:
#             if pk:
#                 # Get single assignment
#                 assignment = Assignment.objects.select_related('subject', 'class_assigned', 'created_by').filter(id=pk).first()
#                 if not assignment:
#                     return Response({'error': 'Assignment not found', 'status': 'error'}, status=404)
                
#                 # Get submission statistics
#                 total_submissions = AssignmentSubmission.objects.filter(assignment=assignment).count()
#                 pending_submissions = AssignmentSubmission.objects.filter(
#                     assignment=assignment,
#                     status='pending'
#                 ).count()
                
#                 data = {
#                     'id': assignment.id,
#                     'title': assignment.title,
#                     'description': assignment.description,
#                     'subject_name': assignment.subject.name if assignment.subject else None,
#                     'class_name': assignment.class_assigned.name if assignment.class_assigned else None,
#                     'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
#                     'max_marks': assignment.max_marks,
#                     'instructions': assignment.instructions,
#                     'attachment_url': assignment.attachment.url if assignment.attachment else None,
#                     'status': assignment.status,
#                     'created_by': assignment.created_by.username,
#                     'created_at': assignment.created_at.isoformat(),
#                     'submission_stats': {
#                         'total_submissions': total_submissions,
#                         'pending_submissions': pending_submissions,
#                         'completed_submissions': total_submissions - pending_submissions
#                     }
#                 }
#             else:
#                 # Get all assignments with filters
#                 subject_id = request.GET.get('subject_id')
#                 class_id = request.GET.get('class_id')
#                 status = request.GET.get('status')
#                 page = int(request.GET.get('page', 1))
#                 limit = int(request.GET.get('limit', 20))
                
#                 queryset = Assignment.objects.select_related('subject', 'class_assigned', 'created_by')
                
#                 if subject_id:
#                     queryset = queryset.filter(subject_id=subject_id)
#                 if class_id:
#                     queryset = queryset.filter(class_assigned_id=class_id)
#                 if status:
#                     queryset = queryset.filter(status=status)
                
#                 # Pagination
#                 offset = (page - 1) * limit
#                 total_count = queryset.count()
#                 assignments = queryset.order_by('-created_at')[offset:offset + limit]
                
#                 assignments_data = []
#                 for assignment in assignments:
#                     assignments_data.append({
#                         'id': assignment.id,
#                         'title': assignment.title,
#                         'subject_name': assignment.subject.name if assignment.subject else None,
#                         'class_name': assignment.class_assigned.name if assignment.class_assigned else None,
#                         'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
#                         'max_marks': assignment.max_marks,
#                         'status': assignment.status,
#                         'created_by': assignment.created_by.username,
#                         'created_at': assignment.created_at.isoformat()
#                     })
                
#                 data = {
#                     'assignments': assignments_data,
#                     'pagination': {
#                         'page': page,
#                         'limit': limit,
#                         'total_count': total_count,
#                         'has_next': offset + limit < total_count
#                     }
#                 }
            
#             return Response({'status': 'success', 'data': data}, status=200)
            
#         except ValueError:
#             return Response({'error': 'Invalid pagination parameters', 'status': 'error'}, status=400)
#         except Exception as e:
#             return Response({'error': 'Failed to fetch assignments', 'status': 'error'}, status=500)
    
#     def post(self, request):
#         try:
#             data = request.data
            
#             # Validate required fields
#             required_fields = ['title', 'class_id']
#             for field in required_fields:
#                 if not data.get(field):
#                     return Response({'error': f'{field} is required', 'status': 'error'}, status=400)
            
#             # Validate class exists
#             class_obj = Class.objects.filter(id=data['class_id']).first()
#             if not class_obj:
#                 return Response({'error': 'Class not found', 'status': 'error'}, status=404)
            
#             # Validate subject if provided
#             subject = None
#             if data.get('subject_id'):
#                 subject = Subject.objects.filter(id=data['subject_id']).first()
#                 if not subject:
#                     return Response({'error': 'Subject not found', 'status': 'error'}, status=404)
            
#             # Validate due date
#             due_date = None
#             if data.get('due_date'):
#                 try:
#                     due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
#                     if due_date < datetime.now().date():
#                         return Response({'error': 'Due date cannot be in the past', 'status': 'error'}, status=400)
#                 except ValueError:
#                     return Response({'error': 'Invalid due date format. Use YYYY-MM-DD', 'status': 'error'}, status=400)
            
#             # Create assignment
#             assignment = Assignment.objects.create(
#                 title=data['title'],
#                 description=data.get('description', ''),
#                 subject=subject,
#                 class_assigned=class_obj,
#                 due_date=due_date,
#                 max_marks=data.get('max_marks', 100),
#                 instructions=data.get('instructions', ''),
#                 created_by=request.user
#             )
            
#             # Handle file attachment if provided
#             if 'attachment' in request.FILES:
#                 assignment.attachment = request.FILES['attachment']
#                 assignment.save()
            
#             return Response({
#                 'status': 'success',
#                 'data': {
#                     'assignment_id': assignment.id,
#                     'title': assignment.title,
#                     'class_name': class_obj.name,
#                     'subject_name': subject.name if subject else None,
#                     'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
#                     'message': 'Assignment created successfully'
#                 }
#             }, status=201)
            
#         except Exception as e:
#             return Response({'error': 'Failed to create assignment', 'status': 'error'}, status=500)

# Input POST: {
#   "title": "Mathematics Assignment - Quadratic Equations",
#   "description": "Solve the given quadratic equations using different methods",
#   "subject_id": 1,
#   "class_id": 1,
#   "due_date": "2025-09-15",
#   "max_marks": 50,
#   "instructions": "Show all working steps clearly"
# }
# class AssignmentSubmissionsAPIView(APIView):
#     permission_classes = [IsAuthenticated, AssignmentsModulePermission]
    
#     def get(self, request):
#         try:
#             # Query parameters
#             assignment_id = request.GET.get('assignment_id')
#             student_id = request.GET.get('student_id')
#             status = request.GET.get('status')  # pending, submitted, graded, late
            
#             if not assignment_id:
#                 return Response({'error': 'assignment_id parameter is required', 'status': 'error'}, status=400)
            
#             # Validate assignment exists
#             assignment = Assignment.objects.filter(id=assignment_id).first()
#             if not assignment:
#                 return Response({'error': 'Assignment not found', 'status': 'error'}, status=404)
            
#             # Base queryset
#             queryset = AssignmentSubmission.objects.select_related('student', 'assignment').filter(
#                 assignment=assignment
#             )
            
#             # Apply filters
#             if student_id:
#                 queryset = queryset.filter(student_id=student_id)
#             if status:
#                 queryset = queryset.filter(status=status)
            
#             submissions_data = []
#             for submission in queryset.order_by('-submitted_at'):
#                 # Determine if submission is late
#                 is_late = False
#                 if assignment.due_date and submission.submitted_at:
#                     is_late = submission.submitted_at.date() > assignment.due_date
                
#                 submissions_data.append({
#                     'submission_id': submission.id,
#                     'student_id': submission.student.id,
#                     'student_name': submission.student.full_name,
#                     'admission_number': submission.student.admission_number,
#                     'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
#                     'status': submission.status,
#                     'is_late': is_late,
#                     'marks_obtained': submission.marks_obtained,
#                     'max_marks': assignment.max_marks,
#                     'percentage': round((submission.marks_obtained / assignment.max_marks) * 100, 2) if submission.marks_obtained and assignment.max_marks else None,
#                     'remarks': submission.remarks,
#                     'attachment_url': submission.attachment.url if submission.attachment else None,
#                     'graded_by': submission.graded_by.username if submission.graded_by else None,
#                     'graded_at': submission.graded_at.isoformat() if submission.graded_at else None
#                 })
            
#             # Calculate statistics
#             total_submissions = queryset.count()
#             pending_submissions = queryset.filter(status='pending').count()
#             graded_submissions = queryset.filter(status='graded').count()
#             late_submissions = 0
            
#             if assignment.due_date:
#                 late_submissions = queryset.filter(
#                     submitted_at__date__gt=assignment.due_date
#                 ).count()
            
#             return Response({
#                 'status': 'success',
#                 'data': {
#                     'assignment_info': {
#                         'assignment_id': assignment.id,
#                         'title': assignment.title,
#                         'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
#                         'max_marks': assignment.max_marks
#                     },
#                     'submissions': submissions_data,
#                     'statistics': {
#                         'total_submissions': total_submissions,
#                         'pending_submissions': pending_submissions,
#                         'graded_submissions': graded_submissions,
#                         'late_submissions': late_submissions,
#                         'submission_rate': round((total_submissions / assignment.class_assigned.student_set.filter(is_active=True).count()) * 100, 2) if assignment.class_assigned else 0
#                     }
#                 }
#             }, status=200)
            
#         except Exception as e:
#             return Response({'error': 'Failed to fetch assignment submissions', 'status': 'error'}, status=500)
    
#     def put(self, request):
#         """Grade assignment submission"""
#         try:
#             data = request.data
            
#             # Validate required fields
#             submission_id = data.get('submission_id')
#             marks_obtained = data.get('marks_obtained')
            
#             if not submission_id:
#                 return Response({'error': 'submission_id is required', 'status': 'error'}, status=400)
#             if marks_obtained is None:
#                 return Response({'error': 'marks_obtained is required', 'status': 'error'}, status=400)
            
#             # Validate submission exists
#             submission = AssignmentSubmission.objects.select_related('assignment', 'student').filter(
#                 id=submission_id
#             ).first()
#             if not submission:
#                 return Response({'error': 'Assignment submission not found', 'status': 'error'}, status=404)
            
#             # Validate marks
#             try:
#                 marks_obtained = float(marks_obtained)
#                 max_marks = submission.assignment.max_marks
                
#                 if marks_obtained < 0 or marks_obtained > max_marks:
#                     return Response({'error': f'Marks must be between 0 and {max_marks}', 'status': 'error'}, status=400)
                    
#             except (ValueError, TypeError):
#                 return Response({'error': 'Invalid marks format', 'status': 'error'}, status=400)
            
#             # Update submission
#             submission.marks_obtained = marks_obtained
#             submission.remarks = data.get('remarks', '')
#             submission.status = 'graded'
#             submission.graded_by = request.user
#             submission.graded_at = datetime.now()
#             submission.save()
            
#             return Response({
#                 'status': 'success',
#                 'data': {
#                     'submission_id': submission.id,
#                     'student_name': submission.student.full_name,
#                     'assignment_title': submission.assignment.title,
#                     'marks_obtained': marks_obtained,
#                     'max_marks': max_marks,
#                     'percentage': round((marks_obtained / max_marks) * 100, 2),
#                     'message': 'Assignment graded successfully'
#                 }
#             }, status=200)
            
#         except Exception as e:
#             return Response({'error': 'Failed to grade assignment submission', 'status': 'error'}, status=500)

# Input GET: /api/v1/admin/assignments/submissions/?assignment_id=1&status=submitted
# Input PUT: {
#   "submission_id": 1,
#   "marks_obtained": 45,
#   "remarks": "Good work, but could improve on presentation"
# }


class AdminUserManagementAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk=None):
        try:
            if pk:
                # Get single user
                user = User.objects.select_related().filter(id=pk).first()
                if not user:
                    return Response({'error': 'User not found', 'status': 'error'}, status=404)
                
                # Get user's roles and permissions
                user_roles = user.groups.all()
                user_permissions = user.user_permissions.all()
                
                data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'date_joined': user.date_joined.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'roles': [{'id': role.id, 'name': role.name} for role in user_roles],
                    'permissions': [{'id': perm.id, 'name': perm.name, 'codename': perm.codename} for perm in user_permissions]
                }
            else:
                # Get all users with filters
                search = request.GET.get('search')
                is_active = request.GET.get('is_active')
                role = request.GET.get('role')
                page = int(request.GET.get('page', 1))
                limit = int(request.GET.get('limit', 20))
                
                queryset = User.objects.all()
                
                if search:
                    queryset = queryset.filter(
                        Q(username__icontains=search) |
                        Q(email__icontains=search) |
                        Q(first_name__icontains=search) |
                        Q(last_name__icontains=search)
                    )
                
                if is_active is not None:
                    is_active_bool = is_active.lower() == 'true'
                    queryset = queryset.filter(is_active=is_active_bool)
                
                if role:
                    queryset = queryset.filter(groups__name=role)
                
                # Pagination
                offset = (page - 1) * limit
                total_count = queryset.count()
                users = queryset.order_by('-date_joined')[offset:offset + limit]
                
                users_data = []
                for user in users:
                    users_data.append({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_active': user.is_active,
                        'is_staff': user.is_staff,
                        'date_joined': user.date_joined.isoformat(),
                        'last_login': user.last_login.isoformat() if user.last_login else None,
                        'roles_count': user.groups.count()
                    })
                
                data = {
                    'users': users_data,
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total_count': total_count,
                        'has_next': offset + limit < total_count
                    }
                }
            
            return Response({'status': 'success', 'data': data}, status=200)
            
        except ValueError:
            return Response({'error': 'Invalid pagination parameters', 'status': 'error'}, status=400)
        except Exception as e:
            return Response({'error': 'Failed to fetch users', 'status': 'error'}, status=500)
    
    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['username', 'email', 'password']
            for field in required_fields:
                if not data.get(field):
                    return Response({'error': f'{field} is required', 'status': 'error'}, status=400)
            
            # Validate username uniqueness
            if User.objects.filter(username=data['username']).exists():
                return Response({'error': 'Username already exists', 'status': 'error'}, status=400)
            
            # Validate email uniqueness
            if User.objects.filter(email=data['email']).exists():
                return Response({'error': 'Email already exists', 'status': 'error'}, status=400)
            
            # Validate email format
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data['email']):
                return Response({'error': 'Invalid email format', 'status': 'error'}, status=400)
            
            # Validate password strength
            password = data['password']
            if len(password) < 8:
                return Response({'error': 'Password must be at least 8 characters long', 'status': 'error'}, status=400)
            
            # Create user
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=password,
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                is_active=data.get('is_active', True),
                is_staff=data.get('is_staff', False)
            )
            
            # Assign roles if provided
            if data.get('role_ids'):
                roles = Group.objects.filter(id__in=data['role_ids'])
                user.groups.set(roles)
            
            return Response({
                'status': 'success',
                'data': {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_active': user.is_active,
                    'message': 'User created successfully'
                }
            }, status=201)
            
        except Exception as e:
            return Response({'error': 'Failed to create user', 'status': 'error'}, status=500)
    
    def put(self, request, pk):
        try:
            user = User.objects.filter(id=pk).first()
            if not user:
                return Response({'error': 'User not found', 'status': 'error'}, status=404)
            
            data = request.data
            
            # Update user fields
            updatable_fields = ['first_name', 'last_name', 'email', 'is_active', 'is_staff']
            for field in updatable_fields:
                if field in data:
                    setattr(user, field, data[field])
            
            # Update password if provided
            if data.get('password'):
                password = data['password']
                if len(password) < 8:
                    return Response({'error': 'Password must be at least 8 characters long', 'status': 'error'}, status=400)
                user.set_password(password)
            
            user.save()
            
            # Update roles if provided
            if 'role_ids' in data:
                roles = Group.objects.filter(id__in=data['role_ids'])
                user.groups.set(roles)
            
            return Response({
                'status': 'success',
                'data': {
                    'user_id': user.id,
                    'username': user.username,
                    'message': 'User updated successfully'
                }
            }, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to update user', 'status': 'error'}, status=500)
    
    def delete(self, request, pk):
        try:
            user = User.objects.filter(id=pk).first()
            if not user:
                return Response({'error': 'User not found', 'status': 'error'}, status=404)
            
            # Prevent deleting superuser or current user
            if user.is_superuser:
                return Response({'error': 'Cannot delete superuser', 'status': 'error'}, status=400)
            
            if user.id == request.user.id:
                return Response({'error': 'Cannot delete your own account', 'status': 'error'}, status=400)
            
            # Soft delete - deactivate user
            user.is_active = False
            user.save()
            
            return Response({
                'status': 'success',
                'data': {'message': 'User deactivated successfully'}
            }, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to delete user', 'status': 'error'}, status=500)

# Input POST: {
#   "username": "teacher_john",
#   "email": "john.doe@school.com",
#   "password": "SecurePass123",
#   "first_name": "John",
#   "last_name": "Doe",
#   "is_active": true,
#   "is_staff": true,
#   "role_ids": [1, 2]
# }

class RoleManagementAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk=None):
        try:
            if pk:
                # Get single role
                role = Group.objects.prefetch_related('permissions').filter(id=pk).first()
                if not role:
                    return Response({'error': 'Role not found', 'status': 'error'}, status=404)
                
                # Get users assigned to this role
                users_with_role = User.objects.filter(groups=role)
                
                data = {
                    'id': role.id,
                    'name': role.name,
                    'permissions': [
                        {
                            'id': perm.id,
                            'name': perm.name,
                            'codename': perm.codename,
                            'content_type': perm.content_type.model
                        }
                        for perm in role.permissions.all()
                    ],
                    'users_count': users_with_role.count(),
                    'users': [
                        {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'is_active': user.is_active
                        }
                        for user in users_with_role[:10]  # Limit to first 10 users
                    ]
                }
            else:
                # Get all roles
                search = request.GET.get('search')
                page = int(request.GET.get('page', 1))
                limit = int(request.GET.get('limit', 20))
                
                queryset = Group.objects.all()
                
                if search:
                    queryset = queryset.filter(name__icontains=search)
                
                # Pagination
                offset = (page - 1) * limit
                total_count = queryset.count()
                roles = queryset.order_by('name')[offset:offset + limit]
                
                roles_data = []
                for role in roles:
                    users_count = User.objects.filter(groups=role).count()
                    permissions_count = role.permissions.count()
                    
                    roles_data.append({
                        'id': role.id,
                        'name': role.name,
                        'users_count': users_count,
                        'permissions_count': permissions_count,
                        'created_at': getattr(role, 'created_at', None)
                    })
                
                data = {
                    'roles': roles_data,
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total_count': total_count,
                        'has_next': offset + limit < total_count
                    }
                }
            
            return Response({'status': 'success', 'data': data}, status=200)
            
        except ValueError:
            return Response({'error': 'Invalid pagination parameters', 'status': 'error'}, status=400)
        except Exception as e:
            return Response({'error': 'Failed to fetch roles', 'status': 'error'}, status=500)
    
    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            name = data.get('name')
            if not name:
                return Response({'error': 'Role name is required', 'status': 'error'}, status=400)
            
            # Check if role already exists
            if Group.objects.filter(name=name).exists():
                return Response({'error': 'Role with this name already exists', 'status': 'error'}, status=400)
            
            # Validate permissions
            permission_ids = data.get('permission_ids', [])
            if permission_ids:
                valid_permissions = Permission.objects.filter(id__in=permission_ids)
                if valid_permissions.count() != len(permission_ids):
                    return Response({'error': 'One or more permission IDs are invalid', 'status': 'error'}, status=400)
            
            # Create role
            role = Group.objects.create(name=name)
            
            # Assign permissions
            if permission_ids:
                permissions = Permission.objects.filter(id__in=permission_ids)
                role.permissions.set(permissions)
            
            return Response({
                'status': 'success',
                'data': {
                    'role_id': role.id,
                    'name': role.name,
                    'permissions_count': role.permissions.count(),
                    'message': 'Role created successfully'
                }
            }, status=201)
            
        except Exception as e:
            return Response({'error': 'Failed to create role', 'status': 'error'}, status=500)
    
    def put(self, request, pk):
        try:
            role = Group.objects.filter(id=pk).first()
            if not role:
                return Response({'error': 'Role not found', 'status': 'error'}, status=404)
            
            data = request.data
            
            # Update role name if provided
            if 'name' in data:
                new_name = data['name']
                if not new_name:
                    return Response({'error': 'Role name cannot be empty', 'status': 'error'}, status=400)
                
                # Check if new name already exists (excluding current role)
                if Group.objects.filter(name=new_name).exclude(id=pk).exists():
                    return Response({'error': 'Role with this name already exists', 'status': 'error'}, status=400)
                
                role.name = new_name
                role.save()
            
            # Update permissions if provided
            if 'permission_ids' in data:
                permission_ids = data['permission_ids']
                if permission_ids:
                    permissions = Permission.objects.filter(id__in=permission_ids)
                    role.permissions.set(permissions)
                else:
                    role.permissions.clear()
            
            return Response({
                'status': 'success',
                'data': {
                    'role_id': role.id,
                    'name': role.name,
                    'permissions_count': role.permissions.count(),
                    'message': 'Role updated successfully'
                }
            }, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to update role', 'status': 'error'}, status=500)
    
    def delete(self, request, pk):
        try:
            role = Group.objects.filter(id=pk).first()
            if not role:
                return Response({'error': 'Role not found', 'status': 'error'}, status=404)
            
            # Check if role is assigned to any users
            users_with_role = User.objects.filter(groups=role).count()
            if users_with_role > 0:
                return Response({
                    'error': f'Cannot delete role. {users_with_role} users are assigned to this role',
                    'status': 'error'
                }, status=400)
            
            role_name = role.name
            role.delete()
            
            return Response({
                'status': 'success',
                'data': {'message': f'Role "{role_name}" deleted successfully'}
            }, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to delete role', 'status': 'error'}, status=500)

# Input POST: {
#   "name": "Mathematics Teacher",
#   "permission_ids": [1, 2, 3, 4, 5]
# }

class AssignModulePermissionsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['user_id', 'module_permissions']
            for field in required_fields:
                if not data.get(field):
                    return Response({'error': f'{field} is required', 'status': 'error'}, status=400)
            
            # Validate user exists
            user = User.objects.filter(id=data['user_id']).first()
            if not user:
                return Response({'error': 'User not found', 'status': 'error'}, status=404)
            
            # Validate module permissions structure
            module_permissions = data['module_permissions']
            if not isinstance(module_permissions, dict):
                return Response({'error': 'module_permissions must be an object', 'status': 'error'}, status=400)
            
            # Valid modules
            valid_modules = [
                'students', 'teachers', 'classes', 'attendance', 'fees', 
                'examinations', 'assignments', 'reports', 'system', 'finance'
            ]
            
            # Clear existing module permissions
            UserModulePermission.objects.filter(user=user).delete()
            
            # Assign new module permissions
            assigned_modules = []
            for module_name, has_access in module_permissions.items():
                if module_name not in valid_modules:
                    return Response({'error': f'Invalid module: {module_name}', 'status': 'error'}, status=400)
                
                if has_access:  # Only create if permission is granted
                    UserModulePermission.objects.create(
                        user=user,
                        module_name=module_name,
                        has_access=True,
                        assigned_by=request.user
                    )
                    assigned_modules.append(module_name)
            
            return Response({
                'status': 'success',
                'data': {
                    'user_id': user.id,
                    'username': user.username,
                    'assigned_modules': assigned_modules,
                    'total_modules': len(assigned_modules),
                    'message': 'Module permissions assigned successfully'
                }
            }, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to assign module permissions', 'status': 'error'}, status=500)

class UserPermissionsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        try:
            # Validate user exists
            user = User.objects.filter(id=user_id).first()
            if not user:
                return Response({'error': 'User not found', 'status': 'error'}, status=404)
            
            # Get module permissions
            module_permissions = UserModulePermission.objects.filter(user=user)
            
            # Get role-based permissions
            role_permissions = []
            for group in user.groups.all():
                for permission in group.permissions.all():
                    role_permissions.append({
                        'permission_id': permission.id,
                        'permission_name': permission.name,
                        'codename': permission.codename,
                        'content_type': permission.content_type.model,
                        'role_name': group.name
                    })
            
            # Get direct user permissions
            direct_permissions = []
            for permission in user.user_permissions.all():
                direct_permissions.append({
                    'permission_id': permission.id,
                    'permission_name': permission.name,
                    'codename': permission.codename,
                    'content_type': permission.content_type.model
                })
            
            # Format module permissions
            modules_data = {}
            for module_perm in module_permissions:
                modules_data[module_perm.module_name] = {
                    'has_access': module_perm.has_access,
                    'assigned_by': module_perm.assigned_by.username if module_perm.assigned_by else None,
                    'assigned_at': module_perm.created_at.isoformat()
                }
            
            data = {
                'user_info': {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser
                },
                'module_permissions': modules_data,
                'role_based_permissions': role_permissions,
                'direct_permissions': direct_permissions,
                'roles': [{'id': group.id, 'name': group.name} for group in user.groups.all()],
                'summary': {
                    'total_modules_access': len(modules_data),
                    'total_role_permissions': len(role_permissions),
                    'total_direct_permissions': len(direct_permissions),
                    'total_roles': user.groups.count()
                }
            }
            
            return Response({'status': 'success', 'data': data}, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to fetch user permissions', 'status': 'error'}, status=500)

# Input POST: {
#   "user_id": 1,
#   "module_permissions": {
#     "students": true,
#     "teachers": true,
#     "classes": false,
#     "attendance": true,
#     "fees": false,
#     "examinations": true,
#     "assignments": true,
#     "reports": false,
#     "system": false,
#     "finance": false
#   }
# }

class TeacherModulePermissionAPIView(APIView):
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def post(self, request, teacher_id):
        try:
            # Validate teacher exists
            teacher = Teacher.objects.filter(id=teacher_id, is_active=True).first()
            if not teacher:
                return Response({'error': 'Teacher not found', 'status': 'error'}, status=404)
            
            # Get teacher's user account
            teacher_user = User.objects.filter(email=teacher.email).first()
            if not teacher_user:
                return Response({'error': 'Teacher user account not found', 'status': 'error'}, status=404)
            
            data = request.data
            
            # Validate required fields
            module_permissions = data.get('module_permissions', {})
            if not isinstance(module_permissions, dict):
                return Response({'error': 'module_permissions must be an object', 'status': 'error'}, status=400)
            
            # Teacher-specific modules (teachers typically don't get all modules)
            teacher_allowed_modules = [
                'students', 'classes', 'attendance', 'examinations', 'assignments'
            ]
            
            # Clear existing teacher module permissions
            TeacherModulePermission.objects.filter(teacher=teacher).delete()
            
            # Assign new module permissions
            assigned_modules = []
            for module_name, permissions_data in module_permissions.items():
                if module_name not in teacher_allowed_modules:
                    return Response({'error': f'Module {module_name} not allowed for teachers', 'status': 'error'}, status=400)
                
                # Validate permissions data structure
                if not isinstance(permissions_data, dict):
                    return Response({'error': f'Permissions for {module_name} must be an object', 'status': 'error'}, status=400)
                
                can_view = permissions_data.get('can_view', False)
                can_edit = permissions_data.get('can_edit', False)
                can_delete = permissions_data.get('can_delete', False)
                
                if can_view or can_edit or can_delete:  # Only create if at least one permission is granted
                    TeacherModulePermission.objects.create(
                        teacher=teacher,
                        module_name=module_name,
                        can_view=can_view,
                        can_edit=can_edit,
                        can_delete=can_delete,
                        assigned_by=request.user
                    )
                    assigned_modules.append({
                        'module': module_name,
                        'can_view': can_view,
                        'can_edit': can_edit,
                        'can_delete': can_delete
                    })
            
            # Also update user-level module permissions for consistency
            UserModulePermission.objects.filter(user=teacher_user).delete()
            for module_data in assigned_modules:
                UserModulePermission.objects.create(
                    user=teacher_user,
                    module_name=module_data['module'],
                    has_access=True,
                    assigned_by=request.user
                )
            
            return Response({
                'status': 'success',
                'data': {
                    'teacher_id': teacher.id,
                    'teacher_name': teacher.full_name,
                    'employee_id': teacher.employee_id,
                    'assigned_modules': assigned_modules,
                    'total_modules': len(assigned_modules),
                    'message': 'Teacher module permissions assigned successfully'
                }
            }, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to assign teacher module permissions', 'status': 'error'}, status=500)

class TeacherModulesAPIView(APIView):
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def get(self, request, teacher_id):
        try:
            # Validate teacher exists
            teacher = Teacher.objects.select_related().filter(id=teacher_id, is_active=True).first()
            if not teacher:
                return Response({'error': 'Teacher not found', 'status': 'error'}, status=404)
            
            # Get teacher's module permissions
            teacher_permissions = TeacherModulePermission.objects.filter(teacher=teacher)
            
            # Get teacher's assigned subjects and classes
            teacher_subjects = TeacherSubject.objects.filter(teacher=teacher).select_related('subject', 'class_assigned')
            
            # Get class teacher assignments
            class_teacher_assignments = ClassTeacher.objects.filter(teacher=teacher, is_active=True).select_related('class_assigned', 'section')
            
            # Format permissions data
            modules_permissions = {}
            for perm in teacher_permissions:
                modules_permissions[perm.module_name] = {
                    'can_view': perm.can_view,
                    'can_edit': perm.can_edit,
                    'can_delete': perm.can_delete,
                    'assigned_by': perm.assigned_by.username if perm.assigned_by else None,
                    'assigned_at': perm.created_at.isoformat()
                }
            
            # Format subjects data
            subjects_data = []
            for ts in teacher_subjects:
                subjects_data.append({
                    'subject_id': ts.subject.id,
                    'subject_name': ts.subject.name,
                    'class_id': ts.class_assigned.id,
                    'class_name': ts.class_assigned.name,
                    'section_name': ts.section.name if ts.section else None
                })
            
            # Format class teacher data
            class_teacher_data = []
            for ct in class_teacher_assignments:
                class_teacher_data.append({
                    'class_id': ct.class_assigned.id,
                    'class_name': ct.class_assigned.name,
                    'section_id': ct.section.id,
                    'section_name': ct.section.name,
                    'assigned_date': ct.assigned_date.isoformat()
                })
            
            data = {
                'teacher_info': {
                    'teacher_id': teacher.id,
                    'employee_id': teacher.employee_id,
                    'full_name': teacher.full_name,
                    'email': teacher.email,
                    'department': teacher.department,
                    'designation': teacher.designation
                },
                'module_permissions': modules_permissions,
                'assigned_subjects': subjects_data,
                'class_teacher_assignments': class_teacher_data,
                'summary': {
                    'total_modules_access': len(modules_permissions),
                    'total_subjects': len(subjects_data),
                    'total_class_assignments': len(class_teacher_data)
                }
            }
            
            return Response({'status': 'success', 'data': data}, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to fetch teacher modules', 'status': 'error'}, status=500)

# Input POST: {
#   "module_permissions": {
#     "students": {
#       "can_view": true,
#       "can_edit": false,
#       "can_delete": false
#     },
#     "attendance": {
#       "can_view": true,
#       "can_edit": true,
#       "can_delete": false
#     },
#     "examinations": {
#       "can_view": true,
#       "can_edit": true,
#       "can_delete": false
#     },
#     "assignments": {
#       "can_view": true,
#       "can_edit": true,
#       "can_delete": true
#     }
#   }
# }


class StudentPerformanceReportAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Query parameters
            student_id = request.GET.get('student_id')
            class_id = request.GET.get('class_id')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            report_type = request.GET.get('type', 'summary')  # summary, detailed, comparative
            
            # Base queryset
            if student_id:
                students = Student.objects.filter(id=student_id, is_active=True)
            elif class_id:
                students = Student.objects.filter(class_assigned_id=class_id, is_active=True)
            else:
                students = Student.objects.filter(is_active=True)[:50]  # Limit to 50 for performance
            
            if not students.exists():
                return Response({'error': 'No students found for the given criteria', 'status': 'error'}, status=404)
            
            # Date range for performance analysis
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            else:
                start_date = datetime.now().date() - timedelta(days=90)  # Last 3 months
            
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            else:
                end_date = datetime.now().date()
            
            performance_data = []
            
            for student in students:
                # Get exam results
                exam_results = ExamResult.objects.filter(
                    student=student,
                    exam__start_date__gte=start_date,
                    exam__end_date__lte=end_date
                ).select_related('exam', 'subject')
                
                # Get attendance data
                attendance_records = Attendance.objects.filter(
                    student=student,
                    date__gte=start_date,
                    date__lte=end_date
                )
                
                total_attendance_days = attendance_records.count()
                present_days = attendance_records.filter(status='present').count()
                attendance_percentage = round((present_days / total_attendance_days) * 100, 2) if total_attendance_days > 0 else 0
                
                # Get assignment submissions
                assignment_submissions = AssignmentSubmission.objects.filter(
                    student=student,
                    submitted_at__date__gte=start_date,
                    submitted_at__date__lte=end_date
                ).select_related('assignment')
                
                # Calculate exam performance
                if exam_results.exists():
                    total_marks = sum(result.marks_obtained for result in exam_results)
                    total_max_marks = sum(result.max_marks for result in exam_results)
                    average_percentage = round((total_marks / total_max_marks) * 100, 2) if total_max_marks > 0 else 0
                    
                    # Subject-wise performance
                    subject_performance = {}
                    for result in exam_results:
                        subject_name = result.subject.name
                        if subject_name not in subject_performance:
                            subject_performance[subject_name] = {
                                'total_marks': 0,
                                'total_max_marks': 0,
                                'exam_count': 0
                            }
                        
                        subject_performance[subject_name]['total_marks'] += result.marks_obtained
                        subject_performance[subject_name]['total_max_marks'] += result.max_marks
                        subject_performance[subject_name]['exam_count'] += 1
                    
                    # Calculate subject averages
                    for subject, data in subject_performance.items():
                        data['average_percentage'] = round((data['total_marks'] / data['total_max_marks']) * 100, 2) if data['total_max_marks'] > 0 else 0
                else:
                    average_percentage = 0
                    subject_performance = {}
                
                # Assignment performance
                assignment_stats = {
                    'total_assignments': assignment_submissions.count(),
                    'submitted_on_time': assignment_submissions.filter(
                        submitted_at__date__lte=F('assignment__due_date')
                    ).count() if assignment_submissions.exists() else 0,
                    'average_marks': assignment_submissions.aggregate(
                        avg_marks=Avg('marks_obtained')
                    )['avg_marks'] or 0
                }
                
                student_performance = {
                    'student_info': {
                        'student_id': student.id,
                        'student_name': student.full_name,
                        'admission_number': student.admission_number,
                        'class_name': student.class_assigned.name if student.class_assigned else None,
                        'section_name': student.section.name if student.section else None
                    },
                    'exam_performance': {
                        'average_percentage': average_percentage,
                        'total_exams': exam_results.count(),
                        'subject_wise_performance': [
                            {
                                'subject': subject,
                                'average_percentage': data['average_percentage'],
                                'exam_count': data['exam_count']
                            }
                            for subject, data in subject_performance.items()
                        ]
                    },
                    'attendance_performance': {
                        'attendance_percentage': attendance_percentage,
                        'total_days': total_attendance_days,
                        'present_days': present_days,
                        'absent_days': total_attendance_days - present_days
                    },
                    'assignment_performance': assignment_stats,
                    'overall_grade': self.calculate_overall_grade(average_percentage, attendance_percentage)
                }
                
                performance_data.append(student_performance)
            
            # Sort by overall performance if multiple students
            if len(performance_data) > 1:
                performance_data.sort(key=lambda x: x['exam_performance']['average_percentage'], reverse=True)
            
            return Response({
                'status': 'success',
                'data': {
                    'report_period': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat()
                    },
                    'student_performance': performance_data,
                    'summary_statistics': {
                        'total_students': len(performance_data),
                        'average_exam_performance': round(
                            sum(s['exam_performance']['average_percentage'] for s in performance_data) / len(performance_data), 2
                        ) if performance_data else 0,
                        'average_attendance': round(
                            sum(s['attendance_performance']['attendance_percentage'] for s in performance_data) / len(performance_data), 2
                        ) if performance_data else 0
                    }
                }
            }, status=200)
            
        except ValueError as e:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD', 'status': 'error'}, status=400)
        except Exception as e:
            return Response({'error': 'Failed to generate student performance report', 'status': 'error'}, status=500)
    
    def calculate_overall_grade(self, exam_percentage, attendance_percentage):
        """Calculate overall grade based on exam and attendance performance"""
        # Weighted average: 70% exam, 30% attendance
        overall_score = (exam_percentage * 0.7) + (attendance_percentage * 0.3)
        
        if overall_score >= 90:
            return 'Excellent'
        elif overall_score >= 80:
            return 'Very Good'
        elif overall_score >= 70:
            return 'Good'
        elif overall_score >= 60:
            return 'Satisfactory'
        elif overall_score >= 50:
            return 'Needs Improvement'
        else:
            return 'Poor'

class TeacherPerformanceReportAPIView(APIView):
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def get(self, request):
        try:
            # Query parameters
            teacher_id = request.GET.get('teacher_id')
            department = request.GET.get('department')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            # Base queryset
            if teacher_id:
                teachers = Teacher.objects.filter(id=teacher_id, is_active=True)
            elif department:
                teachers = Teacher.objects.filter(department=department, is_active=True)
            else:
                teachers = Teacher.objects.filter(is_active=True)[:20]  # Limit for performance
            
            if not teachers.exists():
                return Response({'error': 'No teachers found for the given criteria', 'status': 'error'}, status=404)
            
            # Date range
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            else:
                start_date = datetime.now().date() - timedelta(days=90)
            
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            else:
                end_date = datetime.now().date()
            
            teacher_performance_data = []
            
            for teacher in teachers:
                # Get assigned subjects and classes
                teacher_subjects = TeacherSubject.objects.filter(teacher=teacher).select_related('subject', 'class_assigned')
                
                # Get class teacher assignments
                class_assignments = ClassTeacher.objects.filter(teacher=teacher, is_active=True)
                
                # Get students under this teacher
                student_ids = []
                for ts in teacher_subjects:
                    class_students = Student.objects.filter(
                        class_assigned=ts.class_assigned,
                        is_active=True
                    ).values_list('id', flat=True)
                    student_ids.extend(class_students)
                
                # Remove duplicates
                student_ids = list(set(student_ids))
                
                # Calculate class performance for teacher's students
                if student_ids:
                    # Exam performance of teacher's students
                    exam_results = ExamResult.objects.filter(
                        student_id__in=student_ids,
                        subject__in=[ts.subject for ts in teacher_subjects],
                        exam__start_date__gte=start_date,
                        exam__end_date__lte=end_date
                    )
                    
                    if exam_results.exists():
                        total_marks = sum(result.marks_obtained for result in exam_results)
                        total_max_marks = sum(result.max_marks for result in exam_results)
                        class_average = round((total_marks / total_max_marks) * 100, 2) if total_max_marks > 0 else 0
                    else:
                        class_average = 0
                    
                    # Attendance rate for teacher's students
                    attendance_records = Attendance.objects.filter(
                        student_id__in=student_ids,
                        date__gte=start_date,
                        date__lte=end_date
                    )
                    
                    if attendance_records.exists():
                        total_attendance = attendance_records.count()
                        present_count = attendance_records.filter(status='present').count()
                        attendance_rate = round((present_count / total_attendance) * 100, 2)
                    else:
                        attendance_rate = 0
                else:
                    class_average = 0
                    attendance_rate = 0
                
                # Get assignments created by teacher
                teacher_assignments = Assignment.objects.filter(
                    created_by__email=teacher.email,
                    created_at__date__gte=start_date,
                    created_at__date__lte=end_date
                )
                
                # Calculate assignment submission rate
                assignment_stats = {
                    'total_assignments': teacher_assignments.count(),
                    'total_submissions': AssignmentSubmission.objects.filter(
                        assignment__in=teacher_assignments
                    ).count(),
                    'average_submission_rate': 0
                }
                
                if teacher_assignments.exists():
                    submission_rates = []
                    for assignment in teacher_assignments:
                        total_students = Student.objects.filter(
                            class_assigned=assignment.class_assigned,
                            is_active=True
                        ).count()
                        submissions = AssignmentSubmission.objects.filter(assignment=assignment).count()
                        rate = (submissions / total_students) * 100 if total_students > 0 else 0
                        submission_rates.append(rate)
                    
                    assignment_stats['average_submission_rate'] = round(
                        sum(submission_rates) / len(submission_rates), 2
                    ) if submission_rates else 0
                
                teacher_performance = {
                    'teacher_info': {
                        'teacher_id': teacher.id,
                        'employee_id': teacher.employee_id,
                        'full_name': teacher.full_name,
                        'email': teacher.email,
                        'department': teacher.department,
                        'designation': teacher.designation,
                        'experience_years': teacher.experience_years
                    },
                    'teaching_load': {
                        'subjects_count': teacher_subjects.count(),
                        'classes_count': len(set(ts.class_assigned.id for ts in teacher_subjects)),
                        'total_students': len(student_ids),
                        'class_teacher_assignments': class_assignments.count()
                    },
                    'student_performance': {
                        'class_average_percentage': class_average,
                        'attendance_rate': attendance_rate,
                        'total_students_evaluated': len(student_ids)
                    },
                    'assignment_management': assignment_stats,
                    'subjects_taught': [
                        {
                            'subject_name': ts.subject.name,
                            'class_name': ts.class_assigned.name
                        }
                        for ts in teacher_subjects
                    ],
                    'performance_rating': self.calculate_teacher_rating(class_average, attendance_rate, assignment_stats['average_submission_rate'])
                }
                
                teacher_performance_data.append(teacher_performance)
            
            # Sort by performance rating
            teacher_performance_data.sort(key=lambda x: x['student_performance']['class_average_percentage'], reverse=True)
            
            return Response({
                'status': 'success',
                'data': {
                    'report_period': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat()
                    },
                    'teacher_performance': teacher_performance_data,
                    'summary_statistics': {
                        'total_teachers': len(teacher_performance_data),
                        'average_class_performance': round(
                            sum(t['student_performance']['class_average_percentage'] for t in teacher_performance_data) / len(teacher_performance_data), 2
                        ) if teacher_performance_data else 0,
                        'average_attendance_rate': round(
                            sum(t['student_performance']['attendance_rate'] for t in teacher_performance_data) / len(teacher_performance_data), 2
                        ) if teacher_performance_data else 0
                    }
                }
            }, status=200)
            
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD', 'status': 'error'}, status=400)
        except Exception as e:
            return Response({'error': 'Failed to generate teacher performance report', 'status': 'error'}, status=500)
    
    def calculate_teacher_rating(self, class_average, attendance_rate, assignment_submission_rate):
        """Calculate teacher performance rating"""
        # Weighted average: 50% class performance, 30% attendance, 20% assignments
        overall_score = (class_average * 0.5) + (attendance_rate * 0.3) + (assignment_submission_rate * 0.2)
        
        if overall_score >= 90:
            return 'Excellent'
        elif overall_score >= 80:
            return 'Very Good'
        elif overall_score >= 70:
            return 'Good'
        elif overall_score >= 60:
            return 'Satisfactory'
        else:
            return 'Needs Improvement'

class FinancialReportsAPIView(APIView):
    permission_classes = [IsAuthenticated, FeesModulePermission]
    
    def get(self, request):
        try:
            # Query parameters
            report_type = request.GET.get('type', 'summary')  # summary, detailed, monthly
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            class_id = request.GET.get('class_id')
            fee_type = request.GET.get('fee_type')
            
            # Date range
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            else:
                start_date = datetime.now().date().replace(day=1)  # Start of current month
            
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            else:
                end_date = datetime.now().date()
            
            # Base queryset
            fee_collections = FeeCollection.objects.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            ).select_related('student', 'fee_structure')
            
            if class_id:
                fee_collections = fee_collections.filter(student__class_assigned_id=class_id)
            if fee_type:
                fee_collections = fee_collections.filter(fee_structure__fee_type=fee_type)
            
            if report_type == 'summary':
                # Financial summary
                total_amount_due = fee_collections.aggregate(total=Sum('amount'))['total'] or 0
                total_collected = fee_collections.filter(status='paid').aggregate(total=Sum('amount_paid'))['total'] or 0
                total_pending = fee_collections.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
                total_overdue = fee_collections.filter(
                    status='pending',
                    due_date__lt=datetime.now().date()
                ).aggregate(total=Sum('amount'))['total'] or 0
                
                # Monthly breakdown
                monthly_collections = fee_collections.filter(status='paid').extra(
                    select={'month': "DATE_FORMAT(payment_date, '%%Y-%%m')"}
                ).values('month').annotate(
                    total_collected=Sum('amount_paid'),
                    transaction_count=Count('id')
                ).order_by('month')
                
                # Fee type breakdown
                fee_type_breakdown = fee_collections.values('fee_structure__fee_type').annotate(
                    total_due=Sum('amount'),
                    total_collected=Sum('amount_paid', filter=Q(status='paid')),
                    total_pending=Sum('amount', filter=Q(status='pending'))
                )
                
                # Class-wise breakdown
                class_breakdown = fee_collections.values('student__class_assigned__name').annotate(
                    total_due=Sum('amount'),
                    total_collected=Sum('amount_paid', filter=Q(status='paid')),
                    total_pending=Sum('amount', filter=Q(status='pending')),
                    student_count=Count('student_id', distinct=True)
                )
                
                data = {
                    'summary': {
                        'total_amount_due': float(total_amount_due),
                        'total_collected': float(total_collected),
                        'total_pending': float(total_pending),
                        'total_overdue': float(total_overdue),
                        'collection_percentage': round((total_collected / total_amount_due) * 100, 2) if total_amount_due > 0 else 0,
                        'total_transactions': fee_collections.filter(status='paid').count()
                    },
                    'monthly_collections': [
                        {
                            'month': item['month'],
                            'total_collected': float(item['total_collected'] or 0),
                            'transaction_count': item['transaction_count']
                        }
                        for item in monthly_collections
                    ],
                    'fee_type_breakdown': [
                        {
                            'fee_type': item['fee_structure__fee_type'],
                            'total_due': float(item['total_due'] or 0),
                            'total_collected': float(item['total_collected'] or 0),
                            'total_pending': float(item['total_pending'] or 0),
                            'collection_rate': round((item['total_collected'] or 0) / (item['total_due'] or 1) * 100, 2)
                        }
                        for item in fee_type_breakdown
                    ],
                    'class_breakdown': [
                        {
                            'class_name': item['student__class_assigned__name'],
                            'total_due': float(item['total_due'] or 0),
                            'total_collected': float(item['total_collected'] or 0),
                            'total_pending': float(item['total_pending'] or 0),
                            'student_count': item['student_count']
                        }
                        for item in class_breakdown
                    ]
                }
                
            elif report_type == 'defaulters':
                # Defaulters report
                defaulters = fee_collections.filter(
                    status='pending',
                    due_date__lt=datetime.now().date()
                ).order_by('due_date')
                
                defaulters_data = []
                total_overdue_amount = 0
                
                for collection in defaulters[:100]:  # Limit to 100 records
                    overdue_days = (datetime.now().date() - collection.due_date).days
                    total_overdue_amount += collection.amount
                    
                    defaulters_data.append({
                        'student_id': collection.student.id,
                        'student_name': collection.student.full_name,
                        'admission_number': collection.student.admission_number,
                        'class_name': collection.student.class_assigned.name if collection.student.class_assigned else None,
                        'fee_type': collection.fee_structure.fee_type,
                        'amount_due': float(collection.amount),
                        'due_date': collection.due_date.isoformat(),
                        'overdue_days': overdue_days,
                        'parent_phone': collection.student.parent_phone,
                        'parent_email': collection.student.parent_email
                    })
                
                data = {
                    'defaulters': defaulters_data,
                    'summary': {
                        'total_defaulters': len(defaulters_data),
                        'total_overdue_amount': float(total_overdue_amount),
                        'average_overdue_days': round(
                            sum(item['overdue_days'] for item in defaulters_data) / len(defaulters_data), 1
                        ) if defaulters_data else 0
                    }
                }
                
            else:
                # Detailed transactions report
                transactions = fee_collections.filter(status='paid').order_by('-payment_date')[:200]
                
                transactions_data = []
                for transaction in transactions:
                    transactions_data.append({
                        'transaction_id': transaction.id,
                        'student_name': transaction.student.full_name,
                        'admission_number': transaction.student.admission_number,
                        'fee_type': transaction.fee_structure.fee_type,
                        'amount_paid': float(transaction.amount_paid or 0),
                        'payment_date': transaction.payment_date.isoformat() if transaction.payment_date else None,
                        'payment_method': transaction.payment_method,
                        'transaction_ref': transaction.transaction_id,
                        'collected_by': transaction.collected_by.username if transaction.collected_by else None
                    })
                
                data = {
                    'transactions': transactions_data,
                    'summary': {
                        'total_transactions': len(transactions_data),
                        'total_amount': sum(float(t['amount_paid']) for t in transactions_data)
                    }
                }
            
            return Response({
                'status': 'success',
                'data': {
                    'report_type': report_type,
                    'report_period': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat()
                    },
                    **data
                }
            }, status=200)
            
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD', 'status': 'error'}, status=400)
        except Exception as e:
            return Response({'error': 'Failed to generate financial report', 'status': 'error'}, status=500)

# Input: GET /api/v1/admin/reports/financial/?type=summary&start_date=2025-09-01&end_date=2025-09-06&class_id=1

class ExportStudentsAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def get(self, request):
        try:
            # Query parameters
            class_id = request.GET.get('class_id')
            section_id = request.GET.get('section_id')
            status = request.GET.get('status', 'active')
            format_type = request.GET.get('format', 'csv')  # csv, excel
            fields = request.GET.get('fields', 'basic')  # basic, detailed, all
            
            # Validate format
            if format_type not in ['csv', 'excel']:
                return Response({'error': 'Invalid format. Use csv or excel', 'status': 'error'}, status=400)
            
            # Base queryset
            queryset = Student.objects.select_related('class_assigned', 'section')
            
            if status == 'active':
                queryset = queryset.filter(is_active=True)
            elif status == 'inactive':
                queryset = queryset.filter(is_active=False)
            
            if class_id:
                queryset = queryset.filter(class_assigned_id=class_id)
            if section_id:
                queryset = queryset.filter(section_id=section_id)
            
            students = queryset.order_by('admission_number')
            
            if not students.exists():
                return Response({'error': 'No students found for export', 'status': 'error'}, status=404)
            
            # Define fields to export based on request
            if fields == 'basic':
                field_names = ['admission_number', 'full_name', 'class_name', 'section_name', 'phone', 'email']
            elif fields == 'detailed':
                field_names = [
                    'admission_number', 'full_name', 'date_of_birth', 'gender', 
                    'class_name', 'section_name', 'phone', 'email', 'address',
                    'parent_name', 'parent_phone', 'status'
                ]
            else:  # all
                field_names = [
                    'admission_number', 'full_name', 'date_of_birth', 'gender',
                    'class_name', 'section_name', 'phone', 'email', 'address',
                    'parent_name', 'parent_phone', 'parent_email', 'status',
                    'created_at', 'updated_at'
                ]
            
            # Prepare data
            export_data = []
            for student in students:
                row_data = {}
                
                for field in field_names:
                    if field == 'class_name':
                        row_data[field] = student.class_assigned.name if student.class_assigned else ''
                    elif field == 'section_name':
                        row_data[field] = student.section.name if student.section else ''
                    elif field == 'created_at':
                        row_data[field] = student.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    elif field == 'updated_at':
                        row_data[field] = student.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                    elif field == 'date_of_birth' and student.date_of_birth:
                        row_data[field] = student.date_of_birth.strftime('%Y-%m-%d')
                    else:
                        row_data[field] = getattr(student, field, '') or ''
                
                export_data.append(row_data)
            
            # Generate file
            import pandas as pd
            df = pd.DataFrame(export_data)
            
            if format_type == 'csv':
                # Generate CSV
                from io import StringIO
                csv_buffer = StringIO()
                df.to_csv(csv_buffer, index=False)
                csv_content = csv_buffer.getvalue()
                
                # In a real implementation, you would save this to a file or cloud storage
                # and return a download URL
                file_info = {
                    'filename': f'students_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                    'content_type': 'text/csv',
                    'size_bytes': len(csv_content.encode('utf-8')),
                    'download_url': f'/api/v1/downloads/students_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                }
            else:
                # Generate Excel
                from io import BytesIO
                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False, engine='openpyxl')
                excel_content = excel_buffer.getvalue()
                
                file_info = {
                    'filename': f'students_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                    'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'size_bytes': len(excel_content),
                    'download_url': f'/api/v1/downloads/students_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
                }
            
            # Log export activity
            ExportLog.objects.create(
                user=request.user,
                export_type='students',
                filename=file_info['filename'],
                record_count=len(export_data),
                filters_applied={
                    'class_id': class_id,
                    'section_id': section_id,
                    'status': status,
                    'fields': fields
                }
            )
            
            return Response({
                'status': 'success',
                'data': {
                    'export_info': file_info,
                    'record_count': len(export_data),
                    'exported_fields': field_names,
                    'filters_applied': {
                        'class_id': class_id,
                        'section_id': section_id,
                        'status': status
                    },
                    'message': f'Successfully exported {len(export_data)} student records'
                }
            }, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to export students data', 'status': 'error'}, status=500)

class ExportAttendanceAPIView(APIView):
    permission_classes = [IsAuthenticated, AttendanceModulePermission]
    
    def get(self, request):
        try:
            # Query parameters
            class_id = request.GET.get('class_id')
            student_id = request.GET.get('student_id')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            format_type = request.GET.get('format', 'csv')
            
            # Validate required parameters
            if not start_date or not end_date:
                return Response({'error': 'start_date and end_date are required', 'status': 'error'}, status=400)
            
            # Validate format
            if format_type not in ['csv', 'excel']:
                return Response({'error': 'Invalid format. Use csv or excel', 'status': 'error'}, status=400)
            
            # Parse dates
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD', 'status': 'error'}, status=400)
            
            # Validate date range
            if (end_date - start_date).days > 365:
                return Response({'error': 'Date range cannot exceed 365 days', 'status': 'error'}, status=400)
            
            # Base queryset
            queryset = Attendance.objects.select_related('student', 'student__class_assigned', 'student__section').filter(
                date__gte=start_date,
                date__lte=end_date
            )
            
            if class_id:
                queryset = queryset.filter(student__class_assigned_id=class_id)
            if student_id:
                queryset = queryset.filter(student_id=student_id)
            
            attendance_records = queryset.order_by('date', 'student__admission_number')
            
            if not attendance_records.exists():
                return Response({'error': 'No attendance records found for export', 'status': 'error'}, status=404)
            
            # Prepare export data
            export_data = []
            for record in attendance_records:
                export_data.append({
                    'date': record.date.strftime('%Y-%m-%d'),
                    'admission_number': record.student.admission_number,
                    'student_name': record.student.full_name,
                    'class_name': record.student.class_assigned.name if record.student.class_assigned else '',
                    'section_name': record.student.section.name if record.student.section else '',
                    'status': record.status,
                    'remarks': record.remarks or '',
                    'marked_by': record.updated_by.username if record.updated_by else '',
                    'marked_at': record.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # Generate summary statistics
            total_records = len(export_data)
            present_count = len([r for r in export_data if r['status'] == 'present'])
            absent_count = len([r for r in export_data if r['status'] == 'absent'])
            late_count = len([r for r in export_data if r['status'] == 'late'])
            
            # Create summary sheet data
            summary_data = [
                {'Metric': 'Total Records', 'Value': total_records},
                {'Metric': 'Present', 'Value': present_count},
                {'Metric': 'Absent', 'Value': absent_count},
                {'Metric': 'Late', 'Value': late_count},
                {'Metric': 'Attendance Rate', 'Value': f"{round((present_count / total_records) * 100, 2)}%" if total_records > 0 else "0%"},
                {'Metric': 'Export Date', 'Value': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                {'Metric': 'Date Range', 'Value': f"{start_date} to {end_date}"}
            ]
            
            # Generate file
            import pandas as pd
            
            if format_type == 'csv':
                # For CSV, combine attendance data with summary
                combined_data = export_data + [{}] + summary_data  # Empty row as separator
                df = pd.DataFrame(combined_data)
                
                from io import StringIO
                csv_buffer = StringIO()
                df.to_csv(csv_buffer, index=False)
                csv_content = csv_buffer.getvalue()
                
                file_info = {
                    'filename': f'attendance_export_{start_date}_{end_date}.csv',
                    'content_type': 'text/csv',
                    'size_bytes': len(csv_content.encode('utf-8')),
                    'download_url': f'/api/v1/downloads/attendance_export_{start_date}_{end_date}.csv'
                }
            else:
                # For Excel, create multiple sheets
                from io import BytesIO
                excel_buffer = BytesIO()
                
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    # Attendance data sheet
                    df_attendance = pd.DataFrame(export_data)
                    df_attendance.to_excel(writer, sheet_name='Attendance Records', index=False)
                    
                    # Summary sheet
                    df_summary = pd.DataFrame(summary_data)
                    df_summary.to_excel(writer, sheet_name='Summary', index=False)
                
                excel_content = excel_buffer.getvalue()
                
                file_info = {
                    'filename': f'attendance_export_{start_date}_{end_date}.xlsx',
                    'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'size_bytes': len(excel_content),
                    'download_url': f'/api/v1/downloads/attendance_export_{start_date}_{end_date}.xlsx'
                }
            
            # Log export activity
            ExportLog.objects.create(
                user=request.user,
                export_type='attendance',
                filename=file_info['filename'],
                record_count=total_records,
                filters_applied={
                    'class_id': class_id,
                    'student_id': student_id,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            )
            
            return Response({
                'status': 'success',
                'data': {
                    'export_info': file_info,
                    'record_count': total_records,
                    'summary_statistics': {
                        'total_records': total_records,
                        'present_count': present_count,
                        'absent_count': absent_count,
                        'late_count': late_count,
                        'attendance_rate': round((present_count / total_records) * 100, 2) if total_records > 0 else 0
                    },
                    'date_range': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat()
                    },
                    'message': f'Successfully exported {total_records} attendance records'
                }
            }, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to export attendance data', 'status': 'error'}, status=500)

# Input: GET /api/v1/admin/export/attendance/?start_date=2025-09-01&end_date=2025-09-06&class_id=1&format=excel
class SchoolConfigAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get or create school configuration
            config, created = SchoolConfiguration.objects.get_or_create(
                defaults={
                    'school_name': 'Default School',
                    'school_code': 'SCH001',
                    'address': '',
                    'phone': '',
                    'email': '',
                    'website': '',
                    'established_year': datetime.now().year,
                    'logo': None,
                    'timezone': 'UTC',
                    'academic_year_start_month': 4,  # April
                    'working_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
                    'school_timings': {
                        'start_time': '08:00',
                        'end_time': '15:00',
                        'break_time': '11:00',
                        'break_duration': 30
                    }
                }
            )
            
            data = {
                'id': config.id,
                'school_name': config.school_name,
                'school_code': config.school_code,
                'address': config.address,
                'phone': config.phone,
                'email': config.email,
                'website': config.website,
                'established_year': config.established_year,
                'logo_url': config.logo.url if config.logo else None,
                'timezone': config.timezone,
                'academic_year_start_month': config.academic_year_start_month,
                'working_days': config.working_days,
                'school_timings': config.school_timings,
                'attendance_settings': {
                    'late_arrival_threshold_minutes': getattr(config, 'late_arrival_threshold', 15),
                    'half_day_threshold_minutes': getattr(config, 'half_day_threshold', 240),
                    'allow_future_attendance': getattr(config, 'allow_future_attendance', False)
                },
                'fee_settings': {
                    'currency': getattr(config, 'currency', 'INR'),
                    'late_fee_grace_days': getattr(config, 'late_fee_grace_days', 7),
                    'discount_calculation_method': getattr(config, 'discount_calculation_method', 'percentage')
                },
                'notification_settings': {
                    'sms_enabled': getattr(config, 'sms_enabled', False),
                    'email_enabled': getattr(config, 'email_enabled', True),
                    'parent_notification_enabled': getattr(config, 'parent_notification_enabled', True)
                },
                'created_at': config.created_at.isoformat(),
                'updated_at': config.updated_at.isoformat()
            }
            
            return Response({'status': 'success', 'data': data}, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to fetch school configuration', 'status': 'error'}, status=500)
    
    def put(self, request):
        try:
            data = request.data
            
            # Get or create school configuration
            config, created = SchoolConfiguration.objects.get_or_create(defaults={})
            
            # Update basic school information
            basic_fields = [
                'school_name', 'school_code', 'address', 'phone', 'email', 
                'website', 'established_year', 'timezone'
            ]
            
            for field in basic_fields:
                if field in data:
                    setattr(config, field, data[field])
            
            # Update academic settings
            if 'academic_year_start_month' in data:
                month = data['academic_year_start_month']
                if 1 <= month <= 12:
                    config.academic_year_start_month = month
                else:
                    return Response({'error': 'Invalid academic year start month', 'status': 'error'}, status=400)
            
            # Update working days
            if 'working_days' in data:
                valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                working_days = data['working_days']
                
                if isinstance(working_days, list) and all(day.lower() in valid_days for day in working_days):
                    config.working_days = [day.lower() for day in working_days]
                else:
                    return Response({'error': 'Invalid working days format', 'status': 'error'}, status=400)
            
            # Update school timings
            if 'school_timings' in data:
                timings = data['school_timings']
                if isinstance(timings, dict):
                    # Validate time format
                    time_fields = ['start_time', 'end_time', 'break_time']
                    for time_field in time_fields:
                        if time_field in timings:
                            try:
                                datetime.strptime(timings[time_field], '%H:%M')
                            except ValueError:
                                return Response({'error': f'Invalid time format for {time_field}', 'status': 'error'}, status=400)
                    
                    # Update timings
                    current_timings = config.school_timings or {}
                    current_timings.update(timings)
                    config.school_timings = current_timings
            
            # Update attendance settings
            if 'attendance_settings' in data:
                attendance_settings = data['attendance_settings']
                if isinstance(attendance_settings, dict):
                    if 'late_arrival_threshold_minutes' in attendance_settings:
                        config.late_arrival_threshold = attendance_settings['late_arrival_threshold_minutes']
                    if 'half_day_threshold_minutes' in attendance_settings:
                        config.half_day_threshold = attendance_settings['half_day_threshold_minutes']
                    if 'allow_future_attendance' in attendance_settings:
                        config.allow_future_attendance = attendance_settings['allow_future_attendance']
            
            # Update fee settings
            if 'fee_settings' in data:
                fee_settings = data['fee_settings']
                if isinstance(fee_settings, dict):
                    if 'currency' in fee_settings:
                        config.currency = fee_settings['currency']
                    if 'late_fee_grace_days' in fee_settings:
                        config.late_fee_grace_days = fee_settings['late_fee_grace_days']
                    if 'discount_calculation_method' in fee_settings:
                        config.discount_calculation_method = fee_settings['discount_calculation_method']
            
            # Update notification settings
            if 'notification_settings' in data:
                notification_settings = data['notification_settings']
                if isinstance(notification_settings, dict):
                    if 'sms_enabled' in notification_settings:
                        config.sms_enabled = notification_settings['sms_enabled']
                    if 'email_enabled' in notification_settings:
                        config.email_enabled = notification_settings['email_enabled']
                    if 'parent_notification_enabled' in notification_settings:
                        config.parent_notification_enabled = notification_settings['parent_notification_enabled']
            
            config.updated_by = request.user
            config.save()
            
            # Handle logo upload
            if 'logo' in request.FILES:
                config.logo = request.FILES['logo']
                config.save()
            
            return Response({
                'status': 'success',
                'data': {
                    'school_name': config.school_name,
                    'school_code': config.school_code,
                    'message': 'School configuration updated successfully'
                }
            }, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to update school configuration', 'status': 'error'}, status=500)

class AcademicSettingsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get current academic year
            current_academic_year = AcademicYear.objects.filter(is_current=True).first()
            
            # Get all academic years
            academic_years = AcademicYear.objects.all().order_by('-start_date')
            
            # Get grading system
            grading_system = GradingSystem.objects.filter(is_active=True).first()
            
            # Get examination settings
            exam_settings = ExaminationSettings.objects.first()
            
            data = {
                'current_academic_year': {
                    'id': current_academic_year.id,
                    'name': current_academic_year.name,
                    'start_date': current_academic_year.start_date.isoformat(),
                    'end_date': current_academic_year.end_date.isoformat(),
                    'is_current': current_academic_year.is_current
                } if current_academic_year else None,
                
                'academic_years': [
                    {
                        'id': year.id,
                        'name': year.name,
                        'start_date': year.start_date.isoformat(),
                        'end_date': year.end_date.isoformat(),
                        'is_current': year.is_current,
                        'status': year.status
                    }
                    for year in academic_years
                ],
                
                'grading_system': {
                    'id': grading_system.id,
                    'name': grading_system.name,
                    'grade_ranges': grading_system.grade_ranges,
                    'passing_grade': grading_system.passing_grade,
                    'max_marks': grading_system.max_marks
                } if grading_system else None,
                
                'examination_settings': {
                    'min_passing_percentage': getattr(exam_settings, 'min_passing_percentage', 33),
                    'grace_marks_allowed': getattr(exam_settings, 'grace_marks_allowed', 5),
                    'result_publication_delay_days': getattr(exam_settings, 'result_publication_delay_days', 7),
                    'allow_reexamination': getattr(exam_settings, 'allow_reexamination', True),
                    'max_reexam_attempts': getattr(exam_settings, 'max_reexam_attempts', 2)
                } if exam_settings else {
                    'min_passing_percentage': 33,
                    'grace_marks_allowed': 5,
                    'result_publication_delay_days': 7,
                    'allow_reexamination': True,
                    'max_reexam_attempts': 2
                },
                
                'promotion_settings': {
                    'auto_promotion_enabled': getattr(exam_settings, 'auto_promotion_enabled', False),
                    'min_attendance_for_promotion': getattr(exam_settings, 'min_attendance_for_promotion', 75),
                    'min_marks_for_promotion': getattr(exam_settings, 'min_marks_for_promotion', 40)
                }
            }
            
            return Response({'status': 'success', 'data': data}, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to fetch academic settings', 'status': 'error'}, status=500)
    
    def put(self, request):
        try:
            data = request.data
            
            # Update examination settings
            if 'examination_settings' in data:
                exam_settings, created = ExaminationSettings.objects.get_or_create(defaults={})
                exam_data = data['examination_settings']
                
                updatable_fields = [
                    'min_passing_percentage', 'grace_marks_allowed', 'result_publication_delay_days',
                    'allow_reexamination', 'max_reexam_attempts', 'auto_promotion_enabled',
                    'min_attendance_for_promotion', 'min_marks_for_promotion'
                ]
                
                for field in updatable_fields:
                    if field in exam_data:
                        setattr(exam_settings, field, exam_data[field])
                
                exam_settings.updated_by = request.user
                exam_settings.save()
            
            # Update grading system
            if 'grading_system' in data:
                grading_data = data['grading_system']
                
                # Deactivate current grading system
                GradingSystem.objects.filter(is_active=True).update(is_active=False)
                
                # Create new grading system
                grading_system = GradingSystem.objects.create(
                    name=grading_data.get('name', 'Default Grading System'),
                    grade_ranges=grading_data.get('grade_ranges', {}),
                    passing_grade=grading_data.get('passing_grade', 'D'),
                    max_marks=grading_data.get('max_marks', 100),
                    is_active=True,
                    created_by=request.user
                )
            
            return Response({
                'status': 'success',
                'data': {'message': 'Academic settings updated successfully'}
            }, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to update academic settings', 'status': 'error'}, status=500)

class AcademicYearAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            academic_years = AcademicYear.objects.all().order_by('-start_date')
            
            years_data = []
            for year in academic_years:
                # Get statistics for the academic year
                students_count = Student.objects.filter(
                    created_at__gte=year.start_date,
                    created_at__lte=year.end_date
                ).count()
                
                exams_count = Exam.objects.filter(
                    start_date__gte=year.start_date,
                    end_date__lte=year.end_date
                ).count()
                
                years_data.append({
                    'id': year.id,
                    'name': year.name,
                    'start_date': year.start_date.isoformat(),
                    'end_date': year.end_date.isoformat(),
                    'is_current': year.is_current,
                    'status': year.status,
                    'description': year.description,
                    'statistics': {
                        'students_count': students_count,
                        'exams_count': exams_count
                    },
                    'created_at': year.created_at.isoformat()
                })
            
            return Response({'status': 'success', 'data': years_data}, status=200)
            
        except Exception as e:
            return Response({'error': 'Failed to fetch academic years', 'status': 'error'}, status=500)
    
    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['name', 'start_date', 'end_date']
            for field in required_fields:
                if not data.get(field):
                    return Response({'error': f'{field} is required', 'status': 'error'}, status=400)
            
            # Parse and validate dates
            try:
                start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD', 'status': 'error'}, status=400)
            
            # Validate date range
            if start_date >= end_date:
                return Response({'error': 'Start date must be before end date', 'status': 'error'}, status=400)
            
            # Check for overlapping academic years
            overlapping = AcademicYear.objects.filter(
                Q(start_date__lte=start_date, end_date__gte=start_date) |
                Q(start_date__lte=end_date, end_date__gte=end_date) |
                Q(start_date__gte=start_date, end_date__lte=end_date)
            )
            
            if overlapping.exists():
                return Response({'error': 'Academic year dates overlap with existing academic year', 'status': 'error'}, status=400)
            
            # Check if this should be the current academic year
            is_current = data.get('is_current', False)
            if is_current:
                # Set all other academic years as not current
                AcademicYear.objects.update(is_current=False)
            
            # Create academic year
            academic_year = AcademicYear.objects.create(
                name=data['name'],
                start_date=start_date,
                end_date=end_date,
                is_current=is_current,
                status=data.get('status', 'active'),
                description=data.get('description', ''),
                created_by=request.user
            )
            
            return Response({
                'status': 'success',
                'data': {
                    'id': academic_year.id,
                    'name': academic_year.name,
                    'start_date': academic_year.start_date.isoformat(),
                    'end_date': academic_year.end_date.isoformat(),
                    'is_current': academic_year.is_current,
                    'message': 'Academic year created successfully'
                }
            }, status=201)
            
        except Exception as e:
            return Response({'error': 'Failed to create academic year', 'status': 'error'}, status=500)

# Input POST: {
#   "name": "Academic Year 2025-26",
#   "start_date": "2025-04-01",
#   "end_date": "2026-03-31",
#   "is_current": true,
#   "status": "active",
#   "description": "Academic year from April 2025 to March 2026"
# }


class AcademicYearListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            academic_years = AcademicYear.objects.all().order_by('-start_date')
            serializer = AcademicYearSerializer(academic_years, many=True)
            return Response({'academic_years': serializer.data})
            
        except Exception as e:
            return Response(
                {'error': f'Failed to fetch academic years: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        try:
            serializer = AcademicYearSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {'academic_year': serializer.data},
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return Response(
                {'error': f'Failed to create academic year: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AcademicYearDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            academic_year = get_object_or_404(AcademicYear, pk=pk)
            serializer = AcademicYearSerializer(academic_year)
            return Response({'academic_year': serializer.data})
            
        except AcademicYear.DoesNotExist:
            return Response(
                {'error': 'Academic year not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to fetch academic year: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, pk):
        try:
            academic_year = get_object_or_404(AcademicYear, pk=pk)
            serializer = AcademicYearSerializer(academic_year, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'academic_year': serializer.data})
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except AcademicYear.DoesNotExist:
            return Response(
                {'error': 'Academic year not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to update academic year: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SetCurrentAcademicYearAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            academic_year = get_object_or_404(AcademicYear, pk=pk)
            academic_year.is_current = True
            academic_year.save()
            
            return Response(
                {'message': f'Academic year {academic_year.name} set as current'},
                status=status.HTTP_200_OK
            )
            
        except AcademicYear.DoesNotExist:
            return Response(
                {'error': 'Academic year not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to set current academic year: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )