from rest_framework import serializers
from .models import Class, Section, Subject, ClassSubject, TimeTable


class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = '__all__'
        read_only_fields = ['id']


class SectionSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='class_obj.display_name', read_only=True)
    
    class Meta:
        model = Section
        fields = '__all__'
        read_only_fields = ['id']


class SubjectSerializer(serializers.ModelSerializer):
    total_marks = serializers.SerializerMethodField()
    
    class Meta:
        model = Subject
        fields = '__all__'
        read_only_fields = ['id']
    
    # def get_total_marks(self, obj):
    #     return obj.theory_marks + obj.practical_marks


class ClassSubjectSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='class_obj.display_name', read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True, allow_null=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = ClassSubject
        fields = '__all__'
        read_only_fields = ['id']


class TimeTableSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='class_obj.display_name', read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True)
    day_display = serializers.CharField(source='get_day_display', read_only=True)
    
    class Meta:
        model = TimeTable
        fields = '__all__'
        read_only_fields = ['id']