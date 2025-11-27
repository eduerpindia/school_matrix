from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import Student, StudentAcademicRecord, StudentDocument, StudentAttendance
from .serializers import*
from core.custom_permission import StudentsModulePermission
from classes.models import Class, Section

# Student Management APIs
class StudentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def get(self, request):
        search = request.query_params.get('search', '')
        class_id = request.query_params.get('class_id')
        section_id = request.query_params.get('section_id')
        admission_year = request.query_params.get('admission_year')
        is_active = request.query_params.get('is_active', 'true')
        
        queryset = Student.objects.all()
        
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(admission_number__icontains=search) |
                Q(user__email__icontains=search) |
                Q(father_name__icontains=search) |
                Q(mother_name__icontains=search)
            )
        
        if class_id:
            queryset = queryset.filter(current_class_id=class_id)
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        if admission_year:
            queryset = queryset.filter(admission_date__year=admission_year)
        
        if is_active.lower() == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active.lower() == 'false':
            queryset = queryset.filter(is_active=False)
        
        serializer = StudentSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = StudentCreateSerializer(data=request.data)
        if serializer.is_valid():
            student = serializer.save()
            response_serializer = StudentSerializer(student)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StudentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def get_object(self, pk):
        return get_object_or_404(Student, pk=pk)
    
    def get(self, request, pk):
        student = self.get_object(pk)
        serializer = StudentDetailSerializer(student)
        return Response(serializer.data)
    
    def put(self, request, pk):
        student = self.get_object(pk)
        serializer = StudentSerializer(student, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        student = self.get_object(pk)
        student.is_active = False
        student.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Student Search API
class StudentSearchAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def get(self, request):
        query = request.query_params.get('q', '')
        
        if not query:
            return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)
        
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
        return Response(serializer.data)

# Student Attendance APIs
class StudentAttendanceListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def get(self, request):
        date = request.query_params.get('date')
        class_id = request.query_params.get('class_id')
        section_id = request.query_params.get('section_id')
        student_id = request.query_params.get('student_id')
        
        queryset = StudentAttendance.objects.all()
        
        if date:
            queryset = queryset.filter(date=date)
        if class_id:
            queryset = queryset.filter(student__current_class_id=class_id)
        if section_id:
            queryset = queryset.filter(student__section_id=section_id)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        serializer = StudentAttendanceSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = StudentAttendanceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(marked_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StudentAttendanceDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def get_object(self, pk):
        return get_object_or_404(StudentAttendance, pk=pk)
    
    def get(self, request, pk):
        attendance = self.get_object(pk)
        serializer = StudentAttendanceSerializer(attendance)
        return Response(serializer.data)
    
    def put(self, request, pk):
        attendance = self.get_object(pk)
        serializer = StudentAttendanceSerializer(attendance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        attendance = self.get_object(pk)
        attendance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class BulkAttendanceAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def post(self, request):
        date = request.data.get('date')
        class_id = request.data.get('class_id')
        section_id = request.data.get('section_id')
        attendance_data = request.data.get('attendance', [])
        
        if not date or not class_id:
            return Response({'error': 'Date and class_id are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        created_count = 0
        updated_count = 0
        errors = []
        
        for item in attendance_data:
            student_id = item.get('student_id')
            status = item.get('status')
            remarks = item.get('remarks', '')
            
            if not student_id or not status:
                errors.append(f"Missing required fields for student: {student_id}")
                continue
            
            try:
                student = Student.objects.get(id=student_id)
                attendance, created = StudentAttendance.objects.update_or_create(
                    student=student,
                    date=date,
                    defaults={
                        'status': status,
                        'remarks': remarks,
                        'marked_by': request.user
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                    
            except Student.DoesNotExist:
                errors.append(f"Student with ID {student_id} not found")
            except Exception as e:
                errors.append(f"Error processing student {student_id}: {str(e)}")
        
        return Response({
            'message': f'Bulk attendance processed: {created_count} created, {updated_count} updated',
            'errors': errors if errors else None
        }, status=status.HTTP_200_OK if not errors else status.HTTP_207_MULTI_STATUS)

# Class & Promotion APIs
class StudentPromotionAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def post(self, request):
        serializer = StudentPromotionSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            student = get_object_or_404(Student, id=data['student_id'])
            
            # Create academic record for current year
            current_year = f"{datetime.now().year}-{datetime.now().year + 1}"
            StudentAcademicRecord.objects.create(
                student=student,
                academic_year=current_year,
                class_enrolled=student.current_class,
                section=student.section,
                roll_number=student.roll_number
            )
            
            # Update student to new class/section
            student.current_class_id = data['new_class_id']
            student.section_id = data['new_section_id']
            student.roll_number = data['new_roll_number']
            student.save()
            
            return Response({'message': 'Student promoted successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BulkPromotionAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def post(self, request):
        serializer = BulkPromotionSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            current_year = f"{datetime.now().year}-{datetime.now().year + 1}"
            
            # Get students to promote
            students = Student.objects.filter(current_class_id=data['class_id'], is_active=True)
            if data.get('section_id'):
                students = students.filter(section_id=data['section_id'])
            
            promoted_count = 0
            errors = []
            
            for student in students:
                try:
                    # Create academic record
                    StudentAcademicRecord.objects.create(
                        student=student,
                        academic_year=current_year,
                        class_enrolled=student.current_class,
                        section=student.section,
                        roll_number=student.roll_number
                    )
                    
                    # Update student
                    student.current_class_id = data['new_class_id']
                    if data.get('new_section_id'):
                        student.section_id = data['new_section_id']
                    # Keep same roll number or implement logic for new roll numbers
                    student.save()
                    
                    promoted_count += 1
                    
                except Exception as e:
                    errors.append(f"Error promoting student {student.admission_number}: {str(e)}")
            
            return Response({
                'message': f'Bulk promotion completed: {promoted_count} students promoted',
                'errors': errors if errors else None
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AssignSectionAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def post(self, request, student_id):
        section_id = request.data.get('section_id')
        roll_number = request.data.get('roll_number')
        
        if not section_id:
            return Response({'error': 'section_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        student = get_object_or_404(Student, id=student_id)
        section = get_object_or_404(Section, id=section_id)
        
        student.section = section
        if roll_number:
            student.roll_number = roll_number
        student.save()
        
        return Response({'message': 'Section assigned successfully'})

# Parent/Guardian APIs
class ParentDetailAPIView(APIView):
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
            'guardian_email': student.guardian_email
        }
        return Response(parent_data)
    
    def put(self, request, student_id):
        student = get_object_or_404(Student, id=student_id)
        serializer = ParentUpdateSerializer(student, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Parent details updated successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Document APIs
class StudentDocumentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def get(self, request):
        student_id = request.query_params.get('student_id')
        document_type = request.query_params.get('document_type')
        
        queryset = StudentDocument.objects.all()
        
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        
        serializer = StudentDocumentSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = StudentDocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StudentDocumentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def get_object(self, pk):
        return get_object_or_404(StudentDocument, pk=pk)
    
    def get(self, request, pk):
        document = self.get_object(pk)
        serializer = StudentDocumentSerializer(document)
        return Response(serializer.data)
    
    def delete(self, request, pk):
        document = self.get_object(pk)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Academic Records APIs
class StudentAcademicRecordListAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def get(self, request):
        student_id = request.query_params.get('student_id')
        academic_year = request.query_params.get('academic_year')
        
        queryset = StudentAcademicRecord.objects.all()
        
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
        
        serializer = StudentAcademicRecordSerializer(queryset, many=True)
        return Response(serializer.data)

# Dashboard APIs
class StudentDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def get(self, request):
        total_students = Student.objects.filter(is_active=True).count()
        new_admissions = Student.objects.filter(
            admission_date__month=datetime.now().month,
            admission_date__year=datetime.now().year
        ).count()
        
        # Class-wise count
        class_stats = []
        classes = Class.objects.filter(is_active=True)
        for cls in classes:
            count = Student.objects.filter(current_class=cls, is_active=True).count()
            class_stats.append({
                'class_id': cls.id,
                'class_name': cls.display_name,
                'student_count': count
            })
        
        return Response({
            'total_students': total_students,
            'new_admissions': new_admissions,
            'class_wise_stats': class_stats
        })

# Fee APIs (Basic implementation)
class StudentFeePaymentAPIView(APIView):
    permission_classes = [IsAuthenticated, StudentsModulePermission]
    
    def post(self, request):
        serializer = FeePaymentSerializer(data=request.data)
        if serializer.is_valid():
            # Implement fee payment logic here
            # This would integrate with your fees module
            return Response({'message': 'Fee payment processed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class StudentProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            student = request.user.student_profile
            serializer = StudentProfileSerializer(student)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

class UpdateProfilePictureAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        try:
            student = request.user.student_profile
            if 'photo' not in request.FILES:
                return Response({'error': 'Photo file is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            student.photo = request.FILES['photo']
            student.save()
            return Response({'message': 'Profile picture updated successfully'})
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

class ParentInfoAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            student = request.user.student_profile
            serializer = ParentInfoSerializer(student)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

class ClassTimetableAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            student = request.user.student_profile
            if not student.current_class or not student.section:
                return Response({'error': 'Student not assigned to any class/section'}, status=status.HTTP_400_BAD_REQUEST)
            
            timetable = TimeTable.objects.filter(
                class_name=student.current_class,
                section=student.section,
                is_active=True
            ).order_by('day', 'period')
            
            serializer = TimetableSerializer(timetable, many=True)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

class AssignedSubjectsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            student = request.user.student_profile
            if not student.current_class:
                return Response({'error': 'Student not assigned to any class'}, status=status.HTTP_400_BAD_REQUEST)
            
            current_year = f"{datetime.now().year}-{datetime.now().year + 1}"
            subjects = ClassSubject.objects.filter(
                class_name=student.current_class,
                academic_year=current_year
            )
            
            serializer = SubjectTeacherSerializer(subjects, many=True)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

class TeachersListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            student = request.user.student_profile
            if not student.current_class:
                return Response({'error': 'Student not assigned to any class'}, status=status.HTTP_400_BAD_REQUEST)
            
            current_year = f"{datetime.now().year}-{datetime.now().year + 1}"
            class_subjects = ClassSubject.objects.filter(
                class_name=student.current_class,
                academic_year=current_year
            ).select_related('teacher')
            
            teachers = {cs.teacher for cs in class_subjects if cs.teacher}
            teacher_data = []
            
            for teacher in teachers:
                teacher_data.append({
                    'id': teacher.id,
                    'name': teacher.user.get_full_name(),
                    'email': teacher.user.email,
                    'phone': teacher.user.phone,
                    'subjects': [cs.subject.name for cs in class_subjects if cs.teacher == teacher]
                })
            
            return Response(teacher_data)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

class AssignmentsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            student = request.user.student_profile
            if not student.current_class:
                return Response({'error': 'Student not assigned to any class'}, status=status.HTTP_400_BAD_REQUEST)
            
            assignments = Assignment.objects.filter(
                class_name=student.current_class,
                section=student.section,
                is_active=True
            ).order_by('-due_date')
            
            serializer = AssignmentSerializer(assignments, many=True, context={'request': request})
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

class AssignmentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, assignment_id):
        try:
            student = request.user.student_profile
            assignment = get_object_or_404(Assignment, id=assignment_id)
            
            submission = AssignmentSubmission.objects.filter(
                assignment=assignment, student=student
            ).first()
            
            assignment_data = AssignmentSerializer(assignment, context={'request': request}).data
            submission_data = AssignmentSubmissionSerializer(submission).data if submission else None
            
            return Response({
                'assignment': assignment_data,
                'submission': submission_data
            })
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

class SubmitAssignmentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, assignment_id):
        try:
            student = request.user.student_profile
            assignment = get_object_or_404(Assignment, id=assignment_id)
            
            # Check if assignment is still open
            if assignment.due_date < timezone.now().date():
                return Response({'error': 'Assignment submission deadline has passed'}, status=status.HTTP_400_BAD_REQUEST)
            
            submission, created = AssignmentSubmission.objects.update_or_create(
                assignment=assignment,
                student=student,
                defaults={
                    'submission_file': request.FILES.get('submission_file'),
                    'submission_text': request.data.get('submission_text', ''),
                    'submitted_at': timezone.now()
                }
            )
            
            serializer = AssignmentSubmissionSerializer(submission)
            return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

class ExamScheduleAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            student = request.user.student_profile
            if not student.current_class:
                return Response({'error': 'Student not assigned to any class'}, status=status.HTTP_400_BAD_REQUEST)
            
            exams = Exam.objects.filter(
                class_name=student.current_class,
                is_active=True
            ).order_by('exam_date', 'start_time')
            
            serializer = ExamScheduleSerializer(exams, many=True)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

class ExamResultsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            student = request.user.student_profile
            results = ExamResult.objects.filter(
                student=student
            ).select_related('exam').order_by('-exam__exam_date')
            
            serializer = ExamResultSerializer(results, many=True)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

class AttendanceSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            student = request.user.student_profile
            month = request.query_params.get('month', datetime.now().month)
            year = request.query_params.get('year', datetime.now().year)
            
            # Get all dates in the month
            _, num_days = calendar.monthrange(year, month)
            start_date = datetime(year, month, 1)
            end_date = datetime(year, month, num_days)
            
            attendance = StudentAttendance.objects.filter(
                student=student,
                date__range=[start_date, end_date]
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
                'percentage': round(percentage, 2)
            }
            
            serializer = AttendanceSummarySerializer(summary)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

class DailyAttendanceAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            student = request.user.student_profile
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            if not start_date or not end_date:
                # Default to current month
                today = timezone.now().date()
                start_date = today.replace(day=1)
                end_date = today
            
            attendance = StudentAttendance.objects.filter(
                student=student,
                date__range=[start_date, end_date]
            ).order_by('-date')
            
            serializer = DailyAttendanceSerializer(attendance, many=True)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

class FeeDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            student = request.user.student_profile
            if not student.current_class:
                return Response({'error': 'Student not assigned to any class'}, status=status.HTTP_400_BAD_REQUEST)
            
            current_year = f"{datetime.now().year}-{datetime.now().year + 1}"
            fee_structures = FeeStructure.objects.filter(
                class_name=student.current_class,
                academic_year=current_year
            )
            
            serializer = FeeDetailSerializer(fee_structures, many=True, context={'request': request})
            
            # Calculate totals
            total_amount = sum(fs.amount for fs in fee_structures)
            paid_amount = sum(fs.amount for fs in fee_structures if FeePayment.objects.filter(
                student=student, fee_structure=fs, payment_status='PAID'
            ).exists())
            
            return Response({
                'fee_details': serializer.data,
                'summary': {
                    'total_amount': total_amount,
                    'paid_amount': paid_amount,
                    'pending_amount': total_amount - paid_amount
                }
            })
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

class FeePaymentHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            student = request.user.student_profile
            payments = FeePayment.objects.filter(
                student=student
            ).select_related('fee_structure').order_by('-payment_date')
            
            serializer = FeePaymentSerializer(payments, many=True)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

class PayFeeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, fee_structure_id):
        try:
            student = request.user.student_profile
            fee_structure = get_object_or_404(FeeStructure, id=fee_structure_id)
            
            # Check if already paid
            if FeePayment.objects.filter(
                student=student, fee_structure=fee_structure, payment_status='PAID'
            ).exists():
                return Response({'error': 'Fee already paid'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Process payment (integrate with payment gateway in real implementation)
            payment = FeePayment.objects.create(
                student=student,
                fee_structure=fee_structure,
                amount_paid=fee_structure.amount,
                payment_mode=request.data.get('payment_mode', 'ONLINE'),
                transaction_id=request.data.get('transaction_id', ''),
                payment_status='PAID',
                payment_date=timezone.now().date()
            )
            
            serializer = FeePaymentSerializer(payment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

class DownloadFeeReceiptAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, payment_id):
        try:
            student = request.user.student_profile
            payment = get_object_or_404(FeePayment, id=payment_id, student=student)
            
            # Generate PDF receipt (simplified version)
            # In real implementation, use a PDF generation library
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
                'transaction_id': payment.transaction_id
            }
            
            return Response(receipt_data)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)

class ReportCardAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, academic_year=None):
        try:
            student = request.user.student_profile
            if not academic_year:
                academic_year = f"{datetime.now().year}-{datetime.now().year + 1}"
            
            results = ExamResult.objects.filter(
                student=student,
                exam__academic_year=academic_year
            ).select_related('exam')
            
            if not results.exists():
                return Response({'error': 'No results found for this academic year'}, status=status.HTTP_404_NOT_FOUND)
            
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
                    'remarks': result.remarks
                })
            
            report_card = {
                'academic_year': academic_year,
                'class_name': student.current_class.display_name if student.current_class else '',
                'section_name': student.section.name if student.section else '',
                'student_name': student.user.get_full_name(),
                'roll_number': student.roll_number,
                'total_marks': total_marks,
                'obtained_marks': obtained_marks,
                'percentage': round(percentage, 2),
                'grade': 'A' if percentage >= 90 else 'B' if percentage >= 75 else 'C' if percentage >= 60 else 'D',
                'rank': 1,  # This would be calculated based on class performance
                'subjects': subjects_data
            }
            
            serializer = ReportCardSerializer(report_card)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)