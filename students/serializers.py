from rest_framework import serializers
from .models import *
from classes.models import Class, Section, TimeTable, ClassSubject
from attendance.models import*
from classes.models import *

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import Student
import os
from datetime import datetime
from datetime import date
from .id_card_config import *
User = get_user_model()
class StudentCreateSerializer(serializers.ModelSerializer):
    """Simple serializer - admission_number auto-generated"""
    
    # User fields (write_only)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = Student
        fields = [
            # User fields
            'first_name', 'last_name', 'phone',
            # Student fields (❌ NO admission_number - auto-generated)
            'admission_date', 'date_of_birth', 'gender',
            'blood_group', 'nationality', 'religion', 'category', 'aadhaar_number',
            'address', 'city', 'state', 'pincode', 'emergency_contact',
            'current_class', 'section', 'roll_number', 
            'father_name', 'father_occupation', 'father_phone', 'father_email',
            'mother_name', 'mother_occupation', 'mother_phone', 'mother_email',
            'guardian_name', 'guardian_relation', 'guardian_phone', 'guardian_email',
            'medical_conditions', 'allergies', 'regular_medications',
            'photo', 'birth_certificate', 'aadhaar_card'
        ]


class StudentSerializer(serializers.ModelSerializer):
    """Response serializer"""
    
    user_details = serializers.SerializerMethodField()
    class_name = serializers.CharField(source='current_class.display_name', read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True)
    
    class Meta:
        model = Student
        fields = [
            'id', 'user_details', 'college_email', 'admission_number',  # ✅ admission_number in response
            'admission_date', 'date_of_birth', 'gender',
            'blood_group', 'nationality', 'religion', 'category', 'aadhaar_number',
            'address', 'city', 'state', 'pincode', 'emergency_contact',
            'current_class', 'class_name', 'section', 'section_name', 'roll_number',
            'father_name', 'father_occupation', 'father_phone', 'father_email',
            'mother_name', 'mother_occupation', 'mother_phone', 'mother_email',
            'guardian_name', 'guardian_relation', 'guardian_phone', 'guardian_email',
            'medical_conditions', 'allergies', 'regular_medications',
            'photo', 'birth_certificate', 'aadhaar_card',
            'is_active', 'created_at', 'updated_at'
        ]
    
    def get_user_details(self, obj):
        return {
            'id': obj.user.id,
            'email': obj.user.email,
            'college_email': obj.college_email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'full_name': obj.user.get_full_name(),
            'phone': obj.user.phone,
            'is_verified': obj.user.is_verified
        }
        
class StudentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list view"""
    
    # User fields
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    # Class & Section names
    class_name = serializers.CharField(source='current_class.display_name', read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True)
    
    # Photo URL
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id',
            'admission_number',
            'college_email',
            'first_name',
            'last_name',
            'full_name',
            'photo_url',
            'current_class',
            'class_name',
            'section',
            'section_name',
            'roll_number',
            'gender',
            'blood_group',
            'date_of_birth',
            'admission_date',
            'is_active',
            'created_at'
        ]
    
    def get_photo_url(self, obj):
        """Return photo URL if exists"""
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None        
        
        
class StudentAcademicRecordSerializer(serializers.ModelSerializer):
    """Serializer for academic records"""
    
    session_name = serializers.CharField(source='session.name', read_only=True)
    session_year = serializers.CharField(source='session.year', read_only=True)
    class_name = serializers.CharField(source='class_enrolled.display_name', read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = StudentAcademicRecord
        fields = [
            'id',
            'session',
            'session_name',
            'session_year',
            'class_enrolled',
            'class_name',
            'section',
            'section_name',
            'roll_number',
            'percentage',
            'grade',
            'rank',
            'remarks',
            'status',
            'status_display'
        ]


class StudentDetailSerializer(serializers.ModelSerializer):
    """Complete student profile serializer"""
    
    # User details
    user_details = serializers.SerializerMethodField()
    
    # Class & Section
    class_details = serializers.SerializerMethodField()
    section_details = serializers.SerializerMethodField()
    
    # Files URLs
    photo_url = serializers.SerializerMethodField()
    birth_certificate_url = serializers.SerializerMethodField()
    aadhaar_card_url = serializers.SerializerMethodField()
    
    # Display values
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    blood_group_display = serializers.CharField(source='blood_group', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Student
        fields = [
            'id',
            'user_details',
            
            # Admission Info
            'admission_number',
            'college_email',
            'admission_date',
            
            # Personal Details
            'date_of_birth',
            'gender',
            'gender_display',
            'blood_group',
            'blood_group_display',
            'nationality',
            'religion',
            'category',
            'category_display',
            'aadhaar_number',
            
            # Contact Information
            'address',
            'city',
            'state',
            'pincode',
            'emergency_contact',
            
            # Academic Information
            'class_details',
            'section_details',
            'roll_number',
            
            # Parent/Guardian Information
            'father_name',
            'father_occupation',
            'father_phone',
            'father_email',
            'mother_name',
            'mother_occupation',
            'mother_phone',
            'mother_email',
            'guardian_name',
            'guardian_relation',
            'guardian_phone',
            'guardian_email',
            
            # Medical Information
            'medical_conditions',
            'allergies',
            'regular_medications',
            
            # Documents
            'photo_url',
            'birth_certificate_url',
            'aadhaar_card_url',
            
            # Status
            'is_active',
            'created_at',
            'updated_at'
        ]
    
    def get_user_details(self, obj):
        """User account information"""
        return {
            'id': obj.user.id,
            'email': obj.user.email,
            'username': obj.user.username,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'full_name': obj.user.get_full_name(),
            'phone': obj.user.phone,
            'is_verified': obj.user.is_verified,
            'is_active': obj.user.is_active
        }
    
    def get_class_details(self, obj):
        """Class information"""
        if obj.current_class:
            return {
                'id': obj.current_class.id,
                'name': obj.current_class.name,
                'display_name': obj.current_class.display_name,
                'capacity': obj.current_class.capacity,
                'room_number': obj.current_class.room_number
            }
        return None
    
    def get_section_details(self, obj):
        """Section information"""
        if obj.section:
            return {
                'id': obj.section.id,
                'name': obj.section.name,
                'capacity': obj.section.capacity,
                'room_number': obj.section.room_number
            }
        return None
    
    def get_photo_url(self, obj):
        """Photo URL"""
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None
    
    def get_birth_certificate_url(self, obj):
        """Birth certificate URL"""
        if obj.birth_certificate:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.birth_certificate.url)
            return obj.birth_certificate.url
        return None
    
    def get_aadhaar_card_url(self, obj):
        """Aadhaar card URL"""
        if obj.aadhaar_card:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.aadhaar_card.url)
            return obj.aadhaar_card.url
        return None        
        
        
        
        
        
class StudentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating student details"""
    
    # User fields (optional for update)
    first_name = serializers.CharField(required=False, write_only=True)
    last_name = serializers.CharField(required=False, write_only=True)
    phone = serializers.CharField(required=False, allow_blank=True, write_only=True)
    
    class Meta:
        model = Student
        fields = [
            # User fields
            'first_name', 'last_name', 'phone',
            
            # Personal Details (can be updated)
            'date_of_birth',
            'gender',
            'blood_group',
            'nationality',
            'religion',
            'category',
            'aadhaar_number',
            
            # Contact Information
            'address',
            'city',
            'state',
            'pincode',
            'emergency_contact',
            
            # Academic Information (limited update)
            'current_class',
            'section',
            'roll_number',
            
            # Parent/Guardian Information
            'father_name',
            'father_occupation',
            'father_phone',
            'father_email',
            'mother_name',
            'mother_occupation',
            'mother_phone',
            'mother_email',
            'guardian_name',
            'guardian_relation',
            'guardian_phone',
            'guardian_email',
            
            # Medical Information
            'medical_conditions',
            'allergies',
            'regular_medications'
        ]
        
        # Fields that should not be updated via this API
        read_only_fields = []
    
    def validate_aadhaar_number(self, value):
        """Validate aadhaar number"""
        if value:
            value = value.strip()
            
            # Check length
            if len(value) != 12:
                raise serializers.ValidationError("Aadhaar number must be exactly 12 digits")
            
            # Check if digits only
            if not value.isdigit():
                raise serializers.ValidationError("Aadhaar number must contain only digits")
            
            # Check if already exists (exclude current student)
            student_id = self.instance.id if self.instance else None
            if Student.objects.filter(aadhaar_number=value).exclude(id=student_id).exists():
                raise serializers.ValidationError("This Aadhaar number is already registered")
        
        return value
    
    def validate_gender(self, value):
        """Validate gender"""
        if value:
            value = value.strip().upper()
            if value not in ['M', 'F', 'O']:
                raise serializers.ValidationError("Gender must be M, F, or O")
        return value
    
    def validate_blood_group(self, value):
        """Validate blood group"""
        if value:
            value = value.strip()
            valid_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
            if value not in valid_groups:
                raise serializers.ValidationError(
                    f"Blood group must be one of: {', '.join(valid_groups)}"
                )
        return value
    
    def validate_category(self, value):
        """Validate category"""
        if value:
            value = value.strip().upper()
            valid_categories = ['GEN', 'OBC', 'SC', 'ST', 'OTHER']
            if value not in valid_categories:
                raise serializers.ValidationError(
                    f"Category must be one of: {', '.join(valid_categories)}"
                )
        return value        
        
        

class ParentDetailSerializer(serializers.ModelSerializer):
    """Detailed parent/guardian information serializer"""
    
    student_name = serializers.CharField(source='user.get_full_name', read_only=True)
    student_admission_number = serializers.CharField(source='admission_number', read_only=True)
    student_class = serializers.CharField(source='current_class.display_name', read_only=True)
    student_section = serializers.CharField(source='section.name', read_only=True)
    
    class Meta:
        model = Student
        fields = [
            # Student basic info
            'id',
            'student_name',
            'student_admission_number',
            'student_class',
            'student_section',
            
            # Father details
            'father_name',
            'father_occupation',
            'father_phone',
            'father_email',
            
            # Mother details
            'mother_name',
            'mother_occupation',
            'mother_phone',
            'mother_email',
            
            # Guardian details (if different from parents)
            'guardian_name',
            'guardian_relation',
            'guardian_phone',
            'guardian_email',
            
            # Emergency contact
            'emergency_contact'
        ]


class ParentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating parent information"""
    
    class Meta:
        model = Student
        fields = [
            'father_name',
            'father_occupation',
            'father_phone',
            'father_email',
            'mother_name',
            'mother_occupation',
            'mother_phone',
            'mother_email',
            'guardian_name',
            'guardian_relation',
            'guardian_phone',
            'guardian_email',
            'emergency_contact'
        ]
    
    def validate_father_phone(self, value):
        """Validate father's phone number"""
        if value:
            value = value.strip()
            if not value.isdigit():
                raise serializers.ValidationError("Phone number must contain only digits")
            if len(value) != 10:
                raise serializers.ValidationError("Phone number must be exactly 10 digits")
        return value
    
    def validate_mother_phone(self, value):
        """Validate mother's phone number"""
        if value:
            value = value.strip()
            if not value.isdigit():
                raise serializers.ValidationError("Phone number must contain only digits")
            if len(value) != 10:
                raise serializers.ValidationError("Phone number must be exactly 10 digits")
        return value
    
    def validate_guardian_phone(self, value):
        """Validate guardian's phone number"""
        if value:
            value = value.strip()
            if not value.isdigit():
                raise serializers.ValidationError("Phone number must contain only digits")
            if len(value) != 10:
                raise serializers.ValidationError("Phone number must be exactly 10 digits")
        return value
    
    def validate_emergency_contact(self, value):
        """Validate emergency contact number"""
        if value:
            value = value.strip()
            if not value.isdigit():
                raise serializers.ValidationError("Phone number must contain only digits")
            if len(value) != 10:
                raise serializers.ValidationError("Phone number must be exactly 10 digits")
        return value
    
    def validate_father_email(self, value):
        """Validate father's email"""
        if value:
            value = value.strip().lower()
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError as DjangoValidationError
            try:
                validate_email(value)
            except DjangoValidationError:
                raise serializers.ValidationError("Invalid email format")
        return value
    
    def validate_mother_email(self, value):
        """Validate mother's email"""
        if value:
            value = value.strip().lower()
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError as DjangoValidationError
            try:
                validate_email(value)
            except DjangoValidationError:
                raise serializers.ValidationError("Invalid email format")
        return value
    
    def validate_guardian_email(self, value):
        """Validate guardian's email"""
        if value:
            value = value.strip().lower()
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError as DjangoValidationError
            try:
                validate_email(value)
            except DjangoValidationError:
                raise serializers.ValidationError("Invalid email format")
        return value
        

class StudentDocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading student documents"""
    
    class Meta:
        model = StudentDocument
        fields = [
            'student',
            'document_type',
            'title',
            'file',
            'description'
        ]
    
    def validate_file(self, value):
        """Validate uploaded file"""
        if not value:
            raise serializers.ValidationError("No file uploaded")
        
        # Get file extension
        file_extension = os.path.splitext(value.name)[1].lower()
        
        # Allowed extensions
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"File must be one of: {', '.join(allowed_extensions)}"
            )
        
        # Check file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size must not exceed 5MB. Current size: {value.size / (1024*1024):.2f}MB"
            )
        
        return value
    
    def validate_document_type(self, value):
        """Validate document type"""
        valid_types = [choice[0] for choice in StudentDocument.DOCUMENT_TYPES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Invalid document type. Valid types: {', '.join(valid_types)}"
            )
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        student = data.get('student')
        document_type = data.get('document_type')
        
        # Check if student exists and is active
        if not student.is_active:
            raise serializers.ValidationError({
                'student': 'Cannot upload documents for inactive student'
            })
        
        # For single-document types, check if already exists
        single_document_types = ['BIRTH', 'AADHAAR']
        if document_type in single_document_types:
            existing = StudentDocument.objects.filter(
                student=student,
                document_type=document_type,
                is_active=True
            ).exists()
            
            if existing:
                raise serializers.ValidationError({
                    'document_type': f'{dict(StudentDocument.DOCUMENT_TYPES)[document_type]} already exists for this student'
                })
        
        return data        
        
class StudentDocumentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating document metadata (title, description)"""
    
    class Meta:
        model = StudentDocument
        fields = ['title', 'description']
    
    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()


class StudentDocumentReplaceSerializer(serializers.Serializer):
    """Serializer for replacing document file"""
    
    file = serializers.FileField(required=True)
    
    def validate_file(self, value):
        """Validate uploaded file"""
        if not value:
            raise serializers.ValidationError("No file uploaded")
        
        # Get file extension
        file_extension = os.path.splitext(value.name)[1].lower()
        
        # Allowed extensions
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"File must be one of: {', '.join(allowed_extensions)}"
            )
        
        # Check file size (max 5MB)
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size must not exceed 5MB. Current: {value.size / (1024*1024):.2f}MB"
            )
        
        return value


class StudentDocumentBulkUploadSerializer(serializers.Serializer):
    """Serializer for bulk document upload"""
    
    documents = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=False,
        max_length=10  # Max 10 files at once
    )
    document_types = serializers.ListField(
        child=serializers.CharField(max_length=10),
        allow_empty=False
    )
    titles = serializers.ListField(
        child=serializers.CharField(max_length=200),
        required=False,
        allow_empty=True
    )
    descriptions = serializers.ListField(
        child=serializers.CharField(allow_blank=True),
        required=False,
        allow_empty=True
    )
    
    def validate(self, data):
        documents = data.get('documents', [])
        document_types = data.get('document_types', [])
        
        # Check if lengths match
        if len(documents) != len(document_types):
            raise serializers.ValidationError(
                "Number of documents must match number of document types"
            )
        
        # Validate document types
        valid_types = [choice[0] for choice in StudentDocument.DOCUMENT_TYPES]
        for doc_type in document_types:
            if doc_type.upper() not in valid_types:
                raise serializers.ValidationError(
                    f"Invalid document type: {doc_type}. Valid types: {', '.join(valid_types)}"
                )
        
        return data
        
class AdminMarkAttendanceSerializer(serializers.Serializer):
    """
    Serializer for admin to mark attendance
    Admin can mark for any class/section/subject
    """
    date = serializers.DateField()
    class_id = serializers.IntegerField()
    section_id = serializers.IntegerField()
    subject_id = serializers.IntegerField()
    period_number = serializers.IntegerField(min_value=1, max_value=10)
    timetable_id = serializers.IntegerField(required=False, allow_null=True)
    
    attendance = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )
    def validate_date(self, value):
        if value > datetime.now().date():
            raise serializers.ValidationError("Cannot mark attendance for future dates")
        return value
    
    def validate_attendance(self, value):
        """Validate attendance data structure"""
        valid_statuses = ['P', 'A', 'L', 'H', 'E']
        
        for item in value:
            if 'student_id' not in item:
                raise serializers.ValidationError("Each attendance record must have student_id")
            
            if 'status' not in item:
                raise serializers.ValidationError("Each attendance record must have status")
            
            if item['status'] not in valid_statuses:
                raise serializers.ValidationError(
                    f"Invalid status '{item['status']}'. Must be one of: {', '.join(valid_statuses)}"
                )
        
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        from classes.models import Class, Section, Subject
        from students.models import Student
        
        # Validate class exists
        try:
            class_obj = Class.objects.get(id=data['class_id'], is_active=True)
        except Class.DoesNotExist:
            raise serializers.ValidationError({'class_id': 'Invalid or inactive class'})
        
        # Validate section exists and belongs to class
        try:
            section = Section.objects.get(id=data['section_id'], class_obj=class_obj, is_active=True)
        except Section.DoesNotExist:
            raise serializers.ValidationError({'section_id': 'Invalid section or does not belong to this class'})
        
        # Validate subject exists
        try:
            subject = Subject.objects.get(id=data['subject_id'], is_active=True)
        except Subject.DoesNotExist:
            raise serializers.ValidationError({'subject_id': 'Invalid or inactive subject'})
        
        # Validate all students belong to this class/section
        student_ids = [item['student_id'] for item in data['attendance']]
        students = Student.objects.filter(
            id__in=student_ids,
            current_class=class_obj,
            section=section,
            is_active=True
        )
        
        if students.count() != len(student_ids):
            invalid_ids = set(student_ids) - set(students.values_list('id', flat=True))
            raise serializers.ValidationError({
                'attendance': f'Invalid student IDs or students not in this class/section: {invalid_ids}'
            })
        
        # Store validated objects for use in view
        data['class_obj'] = class_obj
        data['section'] = section
        data['subject'] = subject
        data['students'] = students
        
        return data



class AdminMarkAttendanceSerializer(serializers.Serializer):
    """
    Serializer for admin to mark attendance
    Admin can mark for any class/section/subject
    """
    date = serializers.DateField()
    class_id = serializers.IntegerField()
    section_id = serializers.IntegerField()
    subject_id = serializers.IntegerField()
    period_number = serializers.IntegerField(min_value=1, max_value=10)
    timetable_id = serializers.IntegerField(required=False, allow_null=True)
    
    attendance = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )
    
    def validate_date(self, value):
        """Validate date is not in future"""
        if value > date.today():
            raise serializers.ValidationError("Cannot mark attendance for future dates")
        return value
    
    def validate_attendance(self, value):
        """Validate attendance data structure"""
        valid_statuses = ['P', 'A', 'L', 'H', 'E']
        
        for item in value:
            if 'student_id' not in item:
                raise serializers.ValidationError("Each attendance record must have student_id")
            
            if 'status' not in item:
                raise serializers.ValidationError("Each attendance record must have status")
            
            if item['status'] not in valid_statuses:
                raise serializers.ValidationError(
                    f"Invalid status '{item['status']}'. Must be one of: {', '.join(valid_statuses)}"
                )
        
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        # Validate class exists
        try:
            class_obj = Class.objects.get(id=data['class_id'], is_active=True)
        except Class.DoesNotExist:
            raise serializers.ValidationError({'class_id': 'Invalid or inactive class'})
        
        # Validate section exists and belongs to class
        try:
            section = Section.objects.get(id=data['section_id'], class_obj=class_obj, is_active=True)
        except Section.DoesNotExist:
            raise serializers.ValidationError({'section_id': 'Invalid section or does not belong to this class'})
        
        # Validate subject exists
        try:
            subject = Subject.objects.get(id=data['subject_id'], is_active=True)
        except Subject.DoesNotExist:
            raise serializers.ValidationError({'subject_id': 'Invalid or inactive subject'})
        
        # Validate all students belong to this class/section
        student_ids = [item['student_id'] for item in data['attendance']]
        students = Student.objects.filter(
            id__in=student_ids,
            current_class=class_obj,
            section=section,
            is_active=True
        )
        
        if students.count() != len(student_ids):
            invalid_ids = set(student_ids) - set(students.values_list('id', flat=True))
            raise serializers.ValidationError({
                'attendance': f'Invalid student IDs or students not in this class/section: {invalid_ids}'
            })
        
        # Store validated objects
        data['class_obj'] = class_obj
        data['section'] = section
        data['subject'] = subject
        data['students'] = students
        
        return data


class StudentAttendanceDetailSerializer(serializers.ModelSerializer):
    """Detailed attendance record serializer"""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    admission_number = serializers.CharField(source='student.admission_number', read_only=True)
    class_name = serializers.CharField(source='class_obj.display_name', read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    marked_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentAttendance
        fields = [
            'id',
            'student',
            'student_name',
            'admission_number',
            'date',
            'class_obj',
            'class_name',
            'section',
            'section_name',
            'subject',
            'subject_name',
            'period_number',
            'status',
            'status_display',
            'remarks',
            'marked_by',
            'marked_by_name',
            'marked_at',
            'session'
        ]
        read_only_fields = ['id', 'marked_at']
    
    def get_marked_by_name(self, obj):
        if obj.marked_by:
            return obj.marked_by.get_full_name()
        return None


class BulkAttendanceSerializer(serializers.Serializer):
    """For marking entire class attendance at once"""
    date = serializers.DateField()
    class_id = serializers.IntegerField()
    section_id = serializers.IntegerField()
    subject_id = serializers.IntegerField()
    period_number = serializers.IntegerField()
    
    # Mark all as present/absent
    mark_all_as = serializers.ChoiceField(
        choices=['P', 'A'],
        required=False,
        help_text="Mark all students as Present or Absent"
    )
    
    # Or provide specific list
    attendance = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    
    def validate(self, data):
        if not data.get('mark_all_as') and not data.get('attendance'):
            raise serializers.ValidationError(
                "Either provide 'mark_all_as' or 'attendance' list"
            )
        return data

class BulkAttendanceSerializer(serializers.Serializer):
    """For marking entire class attendance at once"""
    date = serializers.DateField()
    class_id = serializers.IntegerField()
    section_id = serializers.IntegerField()
    subject_id = serializers.IntegerField()
    period_number = serializers.IntegerField()
    
    # Mark all as present/absent
    mark_all_as = serializers.ChoiceField(
        choices=['P', 'A'],
        required=False,
        help_text="Mark all students as Present or Absent"
    )
    
    # Or provide specific list
    attendance = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    
    def validate(self, data):
        if not data.get('mark_all_as') and not data.get('attendance'):
            raise serializers.ValidationError(
                "Either provide 'mark_all_as' or 'attendance' list"
            )
        return data
    
    

class GenerateIDCardRequestSerializer(serializers.Serializer):
    """
    Request serializer for ID card generation
    """
    template_name = serializers.ChoiceField(
        choices=['template_1', 'template_2', 'template_3', 'template_4', 'template_5'],
        help_text="Template to use"
    )
    
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of student IDs"
    )
    
    # Optional dates
    issue_date = serializers.DateField(required=False)
    valid_till = serializers.DateField(required=False)
    
    def validate_student_ids(self, value):
        if len(value) > 100:
            raise serializers.ValidationError("Maximum 100 students at once")
        return value
            
        
        
# Not Use        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        

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
    
    
