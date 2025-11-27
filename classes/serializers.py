from rest_framework import serializers
from .models import Class, Section, Subject, ClassSubject, TimeTable

class SectionSerializer(serializers.ModelSerializer):
    class_name_display = serializers.CharField(source='class_name.display_name', read_only=True)
    section_incharge_name = serializers.CharField(source='section_incharge.user.get_full_name', read_only=True)
    
    class Meta:
        model = Section
        fields = '__all__'
        read_only_fields = ['id']

class ClassSerializer(serializers.ModelSerializer):
    sections = SectionSerializer(many=True, read_only=True)
    class_teacher_name = serializers.CharField(source='class_teacher.user.get_full_name', read_only=True)
    current_strength = serializers.SerializerMethodField()
    
    class Meta:
        model = Class
        fields = '__all__'
        read_only_fields = ['id']
    
    def get_current_strength(self, obj):
        from students.models import Student
        return Student.objects.filter(current_class=obj, is_active=True).count()

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'
        read_only_fields = ['id']

class ClassSubjectSerializer(serializers.ModelSerializer):
    class_name_display = serializers.CharField(source='class_name.display_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    
    class Meta:
        model = ClassSubject
        fields = '__all__'
        read_only_fields = ['id']

class TimeTableSerializer(serializers.ModelSerializer):
    class_name_display = serializers.CharField(source='class_name.display_name', read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    day_display = serializers.CharField(source='get_day_display', read_only=True)
    
    class Meta:
        model = TimeTable
        fields = '__all__'
        read_only_fields = ['id']