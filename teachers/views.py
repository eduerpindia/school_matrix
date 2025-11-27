from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Teacher, TeacherSubject, TeacherAttendance, TeacherSalary
from .serializers import (
    TeacherSerializer, TeacherCreateSerializer, TeacherDetailSerializer,
    TeacherSubjectSerializer, TeacherAttendanceSerializer, TeacherSalarySerializer
)
from core.custom_permission import TeachersModulePermission

# Teacher Views
class TeacherListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def get(self, request):
        search = request.query_params.get('search', '')
        employment_type = request.query_params.get('employment_type', '')
        is_active = request.query_params.get('is_active', 'true')
        
        queryset = Teacher.objects.all()
        
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(employee_id__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        if employment_type:
            queryset = queryset.filter(employment_type=employment_type)
        
        if is_active.lower() == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active.lower() == 'false':
            queryset = queryset.filter(is_active=False)
        
        serializer = TeacherSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = TeacherCreateSerializer(data=request.data)
        if serializer.is_valid():
            teacher = serializer.save()
            response_serializer = TeacherSerializer(teacher)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TeacherDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def get_object(self, pk):
        return get_object_or_404(Teacher, pk=pk)
    
    def get(self, request, pk):
        teacher = self.get_object(pk)
        serializer = TeacherDetailSerializer(teacher)
        return Response(serializer.data)
    
    def put(self, request, pk):
        teacher = self.get_object(pk)
        serializer = TeacherSerializer(teacher, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        teacher = self.get_object(pk)
        teacher.is_active = False
        teacher.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Teacher Subject Views
class TeacherSubjectListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def get(self, request):
        teacher_id = request.query_params.get('teacher_id')
        subject_id = request.query_params.get('subject_id')
        academic_year = request.query_params.get('academic_year')
        
        queryset = TeacherSubject.objects.all()
        
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
        
        serializer = TeacherSubjectSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = TeacherSubjectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TeacherSubjectDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def get_object(self, pk):
        return get_object_or_404(TeacherSubject, pk=pk)
    
    def get(self, request, pk):
        teacher_subject = self.get_object(pk)
        serializer = TeacherSubjectSerializer(teacher_subject)
        return Response(serializer.data)
    
    def put(self, request, pk):
        teacher_subject = self.get_object(pk)
        serializer = TeacherSubjectSerializer(teacher_subject, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        teacher_subject = self.get_object(pk)
        teacher_subject.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Teacher Attendance Views
class TeacherAttendanceListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def get(self, request):
        teacher_id = request.query_params.get('teacher_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        month = request.query_params.get('month')  # Format: 2024-03
        
        queryset = TeacherAttendance.objects.all()
        
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        
        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])
        elif month:
            year, month_num = map(int, month.split('-'))
            import calendar
            last_day = calendar.monthrange(year, month_num)[1]
            start_date = f"{year}-{month_num:02d}-01"
            end_date = f"{year}-{month_num:02d}-{last_day}"
            queryset = queryset.filter(date__range=[start_date, end_date])
        
        serializer = TeacherAttendanceSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        # Handle bulk attendance
        if isinstance(request.data, list):
            serializer = TeacherAttendanceSerializer(data=request.data, many=True)
        else:
            serializer = TeacherAttendanceSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TeacherAttendanceDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def get_object(self, pk):
        return get_object_or_404(TeacherAttendance, pk=pk)
    
    def get(self, request, pk):
        attendance = self.get_object(pk)
        serializer = TeacherAttendanceSerializer(attendance)
        return Response(serializer.data)
    
    def put(self, request, pk):
        attendance = self.get_object(pk)
        serializer = TeacherAttendanceSerializer(attendance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        attendance = self.get_object(pk)
        attendance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Teacher Salary Views
class TeacherSalaryListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def get(self, request):
        teacher_id = request.query_params.get('teacher_id')
        month = request.query_params.get('month')
        payment_status = request.query_params.get('payment_status')
        
        queryset = TeacherSalary.objects.all()
        
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if month:
            queryset = queryset.filter(month=month)
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        
        serializer = TeacherSalarySerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = TeacherSalarySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TeacherSalaryDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def get_object(self, pk):
        return get_object_or_404(TeacherSalary, pk=pk)
    
    def get(self, request, pk):
        salary = self.get_object(pk)
        serializer = TeacherSalarySerializer(salary)
        return Response(serializer.data)
    
    def put(self, request, pk):
        salary = self.get_object(pk)
        serializer = TeacherSalarySerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        salary = self.get_object(pk)
        salary.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Dashboard Views
class TeacherDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def get(self, request):
        total_teachers = Teacher.objects.filter(is_active=True).count()
        present_today = TeacherAttendance.objects.filter(
            date=timezone.now().date(), 
            status='P'
        ).count()
        
        # Monthly attendance summary
        current_month = timezone.now().strftime('%Y-%m')
        year, month = map(int, current_month.split('-'))
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{last_day}"
        
        monthly_data = TeacherAttendance.objects.filter(
            date__range=[start_date, end_date]
        ).values('teacher').annotate(
            present_count=models.Count('id', filter=models.Q(status='P')),
            absent_count=models.Count('id', filter=models.Q(status='A'))
        )
        
        return Response({
            'total_teachers': total_teachers,
            'present_today': present_today,
            'monthly_summary': {
                'month': current_month,
                'total_working_days': (timezone.now().date() - datetime(year, month, 1).date()).days + 1,
                'attendance_data': list(monthly_data)
            }
        })

class TeacherBulkAttendanceAPIView(APIView):
    permission_classes = [IsAuthenticated, TeachersModulePermission]
    
    def post(self, request):
        date = request.data.get('date')
        attendance_data = request.data.get('attendance', [])
        
        if not date:
            return Response({'error': 'Date is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        created_count = 0
        updated_count = 0
        errors = []
        
        for item in attendance_data:
            teacher_id = item.get('teacher_id')
            status = item.get('status')
            check_in = item.get('check_in')
            check_out = item.get('check_out')
            remarks = item.get('remarks', '')
            
            if not teacher_id or not status:
                errors.append(f"Missing required fields for teacher: {teacher_id}")
                continue
            
            try:
                teacher = Teacher.objects.get(id=teacher_id)
                attendance, created = TeacherAttendance.objects.update_or_create(
                    teacher=teacher,
                    date=date,
                    defaults={
                        'status': status,
                        'check_in': check_in,
                        'check_out': check_out,
                        'remarks': remarks
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                    
            except Teacher.DoesNotExist:
                errors.append(f"Teacher with ID {teacher_id} not found")
            except Exception as e:
                errors.append(f"Error processing teacher {teacher_id}: {str(e)}")
        
        return Response({
            'message': f'Bulk attendance processed: {created_count} created, {updated_count} updated',
            'errors': errors if errors else None
        }, status=status.HTTP_200_OK if not errors else status.HTTP_207_MULTI_STATUS)