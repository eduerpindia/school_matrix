from rest_framework import serializers
from .models import Teacher, TeacherSubject, TeacherAttendance, TeacherSalary
from classes.models import Subject, Class

class TeacherSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    
    class Meta:
        model = Teacher
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class TeacherSubjectSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    class_names = serializers.SerializerMethodField()
    
    class Meta:
        model = TeacherSubject
        fields = '__all__'
        read_only_fields = ['id']
    
    def get_class_names(self, obj):
        return [{'id': cls.id, 'name': cls.display_name} for cls in obj.classes.all()]

class TeacherAttendanceSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    employee_id = serializers.CharField(source='teacher.employee_id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = TeacherAttendance
        fields = '__all__'
        read_only_fields = ['id']

class TeacherSalarySerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    employee_id = serializers.CharField(source='teacher.employee_id', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    
    class Meta:
        model = TeacherSalary
        fields = '__all__'
        read_only_fields = ['id']

# For creating teacher with user
class TeacherCreateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    phone = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = Teacher
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
            'username': validated_data.pop('email'),  # Use email as username
            'user_type': 'teacher'
        }
        password = validated_data.pop('password')
        
        # Create user
        user = User.objects.create_user(**user_data)
        user.set_password(password)
        user.save()
        
        # Create teacher profile
        teacher = Teacher.objects.create(user=user, **validated_data)
        return teacher

class TeacherDetailSerializer(TeacherSerializer):
    subjects = TeacherSubjectSerializer(many=True, read_only=True, source='teacher_subjects')
    attendance = serializers.SerializerMethodField()
    salary_history = serializers.SerializerMethodField()
    
    def get_attendance(self, obj):
        # Get last 30 days attendance
        from django.utils import timezone
        from datetime import timedelta
        start_date = timezone.now().date() - timedelta(days=30)
        attendance = TeacherAttendance.objects.filter(
            teacher=obj, 
            date__gte=start_date
        ).order_by('-date')[:30]
        return TeacherAttendanceSerializer(attendance, many=True).data
    
    def get_salary_history(self, obj):
        # Get last 6 months salary
        salaries = TeacherSalary.objects.filter(
            teacher=obj
        ).order_by('-month')[:6]
        return TeacherSalarySerializer(salaries, many=True).data