from rest_framework import serializers
from .models import Student, StudentAcademicRecord, StudentDocument, StudentAttendance
from classes.models import Class, Section, TimeTable, ClassSubject
from attendance.models import*

class StudentSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    class_name = serializers.CharField(source='current_class.display_name', read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True)
    
    class Meta:
        model = Student
        fields = '__all__'
        read_only_fields = ['id', 'admission_number', 'created_at', 'updated_at']

class StudentCreateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    phone = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = Student
        exclude = ['user']
    
    def create(self, validated_data):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Extract user data
        user_data = {
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'email': validated_data.pop('email'),
            'phone': validated_data.pop('phone', ''),
            'username': validated_data.pop('email'),
            'user_type': 'student'
        }
        password = validated_data.pop('password')
        
        # Create user
        user = User.objects.create_user(**user_data)
        user.set_password(password)
        user.save()
        
        # Generate admission number
        from datetime import datetime
        admission_number = f"ST{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create student profile
        student = Student.objects.create(user=user, admission_number=admission_number, **validated_data)
        return student

class StudentDetailSerializer(StudentSerializer):
    academic_records = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    attendance_summary = serializers.SerializerMethodField()
    
    def get_academic_records(self, obj):
        records = StudentAcademicRecord.objects.filter(student=obj).order_by('-academic_year')[:5]
        from .serializers import StudentAcademicRecordSerializer
        return StudentAcademicRecordSerializer(records, many=True).data
    
    def get_documents(self, obj):
        documents = StudentDocument.objects.filter(student=obj).order_by('-upload_date')[:10]
        from .serializers import StudentDocumentSerializer
        return StudentDocumentSerializer(documents, many=True).data
    
    def get_attendance_summary(self, obj):
        from django.utils import timezone
        from datetime import timedelta
        start_date = timezone.now().date() - timedelta(days=30)
        attendance = StudentAttendance.objects.filter(
            student=obj, 
            date__gte=start_date
        )
        present = attendance.filter(status='P').count()
        absent = attendance.filter(status='A').count()
        return {'present': present, 'absent': absent, 'total': attendance.count()}

class StudentAcademicRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    admission_number = serializers.CharField(source='student.admission_number', read_only=True)
    class_name = serializers.CharField(source='class_enrolled.display_name', read_only=True)
    
    class Meta:
        model = StudentAcademicRecord
        fields = '__all__'
        read_only_fields = ['id']

class StudentDocumentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    admission_number = serializers.CharField(source='student.admission_number', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    
    class Meta:
        model = StudentDocument
        fields = '__all__'
        read_only_fields = ['id', 'upload_date']

class StudentAttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    admission_number = serializers.CharField(source='student.admission_number', read_only=True)
    class_name = serializers.CharField(source='student.current_class.display_name', read_only=True)
    section_name = serializers.CharField(source='student.section.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    marked_by_name = serializers.CharField(source='marked_by.get_full_name', read_only=True)
    
    class Meta:
        model = StudentAttendance
        fields = '__all__'
        read_only_fields = ['id']

class StudentPromotionSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    new_class_id = serializers.IntegerField()
    new_section_id = serializers.IntegerField()
    new_roll_number = serializers.IntegerField()
    academic_year = serializers.CharField(max_length=9)

class BulkPromotionSerializer(serializers.Serializer):
    class_id = serializers.IntegerField()
    section_id = serializers.IntegerField(required=False)
    new_class_id = serializers.IntegerField()
    new_section_id = serializers.IntegerField(required=False)
    academic_year = serializers.CharField(max_length=9)

class ParentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            'father_name', 'father_occupation', 'father_phone', 'father_email',
            'mother_name', 'mother_occupation', 'mother_phone', 'mother_email',
            'guardian_name', 'guardian_relation', 'guardian_phone', 'guardian_email'
        ]

class FeePaymentSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = serializers.CharField(max_length=20)
    transaction_id = serializers.CharField(max_length=100, required=False)
    remarks = serializers.CharField(max_length=200, required=False)
    
class StudentProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    class_name = serializers.CharField(source='current_class.display_name', read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True)
    
    class Meta:
        model = Student
        fields = [
            'id', 'admission_number', 'full_name', 'email', 'phone',
            'date_of_birth', 'gender', 'blood_group', 'address', 'city',
            'state', 'pincode', 'emergency_contact', 'current_class',
            'section', 'class_name', 'section_name', 'roll_number',
            'father_name', 'father_phone', 'mother_name', 'mother_phone',
            'photo'
        ]

class ParentInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            'father_name', 'father_occupation', 'father_phone', 'father_email',
            'mother_name', 'mother_occupation', 'mother_phone', 'mother_email',
            'guardian_name', 'guardian_relation', 'guardian_phone', 'guardian_email'
        ]

class TimetableSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    day_display = serializers.CharField(source='get_day_display', read_only=True)
    
    class Meta:
        model = TimeTable
        fields = ['day', 'day_display', 'period', 'subject', 'subject_name', 
                 'teacher', 'teacher_name', 'start_time', 'end_time', 'room_number']

class SubjectTeacherSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    teacher_email = serializers.EmailField(source='teacher.user.email', read_only=True)
    
    class Meta:
        model = ClassSubject
        fields = ['subject', 'subject_name', 'teacher', 'teacher_name', 'teacher_email']

class AssignmentSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    status = serializers.SerializerMethodField()
    
    # class Meta:
    #     model = Assignment
    #     fields = ['id', 'title', 'subject', 'subject_name', 'teacher', 'teacher_name',
    #              'description', 'due_date', 'total_marks', 'status']
    
    # def get_status(self, obj):
    #     request = self.context.get('request')
    #     if request and request.user.is_authenticated:
    #         student = getattr(request.user, 'student_profile', None)
    #         if student:
    #             submission = AssignmentSubmission.objects.filter(
    #                 assignment=obj, student=student
    #             ).first()
    #             return 'submitted' if submission else 'pending'
    #     return 'pending'

class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    
    # class Meta:
    #     model = AssignmentSubmission
    #     fields = ['id', 'assignment', 'assignment_title', 'student', 'student_name',
    #              'submission_file', 'submission_text', 'submitted_at', 'marks_obtained',
    #              'teacher_feedback']

class ExamScheduleSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    
    # class Meta:
    #     model = Exam
    #     fields = ['id', 'name', 'subject', 'subject_name', 'exam_date', 'start_time',
    #              'end_time', 'total_marks', 'passing_marks', 'exam_room']

class ExamResultSerializer(serializers.ModelSerializer):
    exam_name = serializers.CharField(source='exam.name', read_only=True)
    subject_name = serializers.CharField(source='exam.subject.name', read_only=True)
    total_marks = serializers.IntegerField(source='exam.total_marks', read_only=True)
    
    # class Meta:
    #     model = ExamResult
    #     fields = ['id', 'exam', 'exam_name', 'subject_name', 'marks_obtained',
    #              'total_marks', 'grade', 'rank', 'remarks']

class AttendanceSummarySerializer(serializers.Serializer):
    month = serializers.CharField()
    year = serializers.IntegerField()
    total_days = serializers.IntegerField()
    present_days = serializers.IntegerField()
    absent_days = serializers.IntegerField()
    late_days = serializers.IntegerField()
    percentage = serializers.FloatField()

class DailyAttendanceSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Attendance
        fields = ['date', 'status', 'status_display', 'remarks']

class FeeDetailSerializer(serializers.ModelSerializer):
    fee_type_display = serializers.CharField(source='get_fee_type_display', read_only=True)
    due_date = serializers.DateField(source='get_due_date', read_only=True)
    is_paid = serializers.SerializerMethodField()
    
    # class Meta:
    #     model = FeeStructure
    #     fields = ['id', 'fee_type', 'fee_type_display', 'amount', 'due_date', 'is_paid']
    
    # def get_is_paid(self, obj):
    #     request = self.context.get('request')
    #     if request and request.user.is_authenticated:
    #         student = getattr(request.user, 'student_profile', None)
    #         if student:
    #             return FeePayment.objects.filter(
    #                 student=student, fee_structure=obj, payment_status='PAID'
    #             ).exists()
    #     return False

class FeePaymentSerializer(serializers.ModelSerializer):
    fee_type = serializers.CharField(source='fee_structure.fee_type', read_only=True)
    
    # class Meta:
    #     model = Fees
    #     fields = ['id', 'fee_structure', 'fee_type', 'amount_paid', 'payment_date',
    #              'payment_mode', 'transaction_id', 'payment_status']

class ReportCardSerializer(serializers.Serializer):
    academic_year = serializers.CharField()
    class_name = serializers.CharField()
    section_name = serializers.CharField()
    student_name = serializers.CharField()
    roll_number = serializers.IntegerField()
    total_marks = serializers.IntegerField()
    obtained_marks = serializers.IntegerField()
    percentage = serializers.FloatField()
    grade = serializers.CharField()
    rank = serializers.IntegerField()
    subjects = serializers.ListField()