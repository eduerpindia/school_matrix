# teachers/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from datetime import date

from .models import Teacher, TeacherSubject, TeacherAttendance, TeacherSalary
from classes.models import Class, Section, Subject, ClassSubject, TimeTable
from schools.models import SchoolSession
from core.models import *
User = get_user_model()


# ========== USER SERIALIZER ==========

class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for teacher"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'phone', 'user_type']
        read_only_fields = ['id']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


# ========== TEACHER LIST SERIALIZER ==========

class TeacherListSerializer(serializers.ModelSerializer):
    """Minimal serializer for teacher list with summary"""
    user = UserSerializer(read_only=True)
    total_subjects = serializers.SerializerMethodField()
    total_classes = serializers.SerializerMethodField()
    employment_type_display = serializers.CharField(source='get_employment_type_display', read_only=True)
    
    class Meta:
        model = Teacher
        fields = [
            'id',
            'user',
            'employee_id',
            'date_of_birth',
            'gender',
            'qualification',
            'specialization',
            'employment_type',
            'employment_type_display',
            'experience_years',
            'date_of_joining',
            'is_class_teacher',
            'is_active',
            'total_subjects',
            'total_classes',
            'created_at',
        ]
    
    def get_total_subjects(self, obj):
        """Count unique subjects assigned to teacher"""
        return obj.subjects.filter(
            subject__is_active=True
        ).values('subject').distinct().count()
    
    def get_total_classes(self, obj):
        """Count unique class-section combinations"""
        try:
            current_session = SchoolSession.objects.get(is_current=True)
            return obj.taught_subjects.filter(
                class_obj__is_active=True,
                session=current_session
            ).values('class_obj', 'section').distinct().count()
        except SchoolSession.DoesNotExist:
            return 0


# ========== TEACHER DETAIL SERIALIZER ==========

class TeacherDetailSerializer(serializers.ModelSerializer):
    """Detailed teacher serializer with all information"""
    user = UserSerializer(read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    blood_group_display = serializers.CharField(source='get_blood_group_display', read_only=True)
    employment_type_display = serializers.CharField(source='get_employment_type_display', read_only=True)
    
    assigned_subjects = serializers.SerializerMethodField()
    assigned_classes = serializers.SerializerMethodField()
    class_teacher_of = serializers.SerializerMethodField()
    
    class Meta:
        model = Teacher
        fields = [
            'id',
            'user',
            'employee_id',
            
            # Personal Information
            'date_of_birth',
            'gender',
            'gender_display',
            'blood_group',
            'blood_group_display',
            
            # Contact Information
            'address',
            'city',
            'state',
            'pincode',
            'emergency_contact',
            
            # Professional Information
            'qualification',
            'specialization',
            'experience_years',
            'date_of_joining',
            'employment_type',
            'employment_type_display',
            
            # Bank Details
            'bank_name',
            'account_number',
            'ifsc_code',
            
            # Government Documents
            'pan_number',
            'aadhaar_number',
            
            # Status
            'is_class_teacher',
            'is_active',
            
            # Related Data
            'assigned_subjects',
            'assigned_classes',
            'class_teacher_of',
            
            # Timestamps
            'created_at',
            'updated_at',
        ]
    
    def get_assigned_subjects(self, obj):
        """Get all subjects assigned to teacher"""
        subjects = obj.subjects.filter(
            subject__is_active=True
        ).select_related('subject').values(
            'id',
            'subject__id',
            'subject__name',
            'subject__code',
            'academic_year'
        ).distinct()
        return list(subjects)
    
    def get_assigned_classes(self, obj):
        """Get all class-section-subject combinations"""
        try:
            current_session = SchoolSession.objects.get(is_current=True)
            classes = obj.taught_subjects.filter(
                class_obj__is_active=True,
                session=current_session
            ).select_related('class_obj', 'section', 'subject').values(
                'id',
                'class_obj__id',
                'class_obj__display_name',
                'section__id',
                'section__name',
                'subject__id',
                'subject__name',
                'periods_per_week',
                'is_optional'
            )
            return list(classes)
        except SchoolSession.DoesNotExist:
            return []
    
    def get_class_teacher_of(self, obj):
        """Get classes where this teacher is class teacher"""
        try:
            current_session = SchoolSession.objects.get(is_current=True)
            classes = obj.classes_as_class_teacher.filter(
                is_active=True,
                session=current_session
            ).values(
                'id',
                'display_name',
                'room_number'
            )
            return list(classes)
        except SchoolSession.DoesNotExist:
            return []


# ========== TEACHER CREATE SERIALIZER ==========

class TeacherCreateSerializer(serializers.Serializer):
    """Create teacher with user account"""
    
    # ========== USER INFORMATION ==========
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True, required=False, help_text="If not provided, default password will be: Teacher@<employee_id>")
    
    # ========== TEACHER PERSONAL INFORMATION ==========
    employee_id = serializers.CharField(max_length=20)
    date_of_birth = serializers.DateField()
    gender = serializers.ChoiceField(choices=Teacher.GENDER_CHOICES)
    blood_group = serializers.ChoiceField(choices=Teacher.BLOOD_GROUP_CHOICES, required=False, allow_blank=True)
    
    # ========== CONTACT INFORMATION ==========
    address = serializers.CharField()
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100)
    pincode = serializers.CharField(max_length=10)
    emergency_contact = serializers.CharField(max_length=15)
    
    # ========== PROFESSIONAL INFORMATION ==========
    qualification = serializers.CharField(max_length=100)
    specialization = serializers.CharField(max_length=100)
    experience_years = serializers.IntegerField(default=0, min_value=0)
    date_of_joining = serializers.DateField()
    employment_type = serializers.ChoiceField(choices=Teacher.EMPLOYMENT_TYPE_CHOICES, default='PERMANENT')
    
    # ========== BANK DETAILS (OPTIONAL) ==========
    bank_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    account_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    ifsc_code = serializers.CharField(max_length=11, required=False, allow_blank=True)
    
    # ========== GOVERNMENT DOCUMENTS (OPTIONAL) ==========
    pan_number = serializers.CharField(max_length=10, required=False, allow_blank=True)
    aadhaar_number = serializers.CharField(max_length=12, required=False, allow_blank=True)
    
    # ========== STATUS ==========
    is_class_teacher = serializers.BooleanField(default=False)
    is_active = serializers.BooleanField(default=True)
    
    # ========== ROLE & MODULE ASSIGNMENT ==========
    assign_teacher_role = serializers.BooleanField(default=True, help_text="Auto-assign 'teacher' role")
    modules = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of module names to assign: ['students', 'attendance', 'teachers']"
    )
    
    def validate_email(self, value):
        """Check if email already exists"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists")
        return value
    
    def validate_employee_id(self, value):
        """Check if employee ID already exists"""
        if Teacher.objects.filter(employee_id=value).exists():
            raise serializers.ValidationError("Teacher with this employee ID already exists")
        return value
    
    def validate_date_of_birth(self, value):
        """Validate date of birth"""
        if value >= date.today():
            raise serializers.ValidationError("Date of birth must be in the past")
        
        age = (date.today() - value).days // 365
        if age < 18:
            raise serializers.ValidationError("Teacher must be at least 18 years old")
        
        if age > 100:
            raise serializers.ValidationError("Invalid date of birth")
        
        return value
    
    def validate_date_of_joining(self, value):
        """Validate joining date"""
        if value > date.today():
            raise serializers.ValidationError("Joining date cannot be in the future")
        return value
    
    def validate_phone(self, value):
        """Validate phone number"""
        if not value.isdigit() or len(value) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value
    
    def validate_pincode(self, value):
        """Validate pincode"""
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("Pincode must be exactly 6 digits")
        return value
    
    def validate_pan_number(self, value):
        """Validate PAN number format"""
        if value and len(value) != 10:
            raise serializers.ValidationError("PAN number must be exactly 10 characters")
        return value.upper() if value else ''
    
    def validate_aadhaar_number(self, value):
        """Validate Aadhaar number"""
        if value and (not value.isdigit() or len(value) != 12):
            raise serializers.ValidationError("Aadhaar number must be exactly 12 digits")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        # Validate date_of_birth < date_of_joining
        if data['date_of_birth'] >= data['date_of_joining']:
            raise serializers.ValidationError({
                'date_of_joining': 'Joining date must be after date of birth'
            })
        
        return data
    
    def create(self, validated_data):
        """Create teacher with user account"""
        # Extract module assignment data
        assign_role = validated_data.pop('assign_teacher_role', True)
        modules = validated_data.pop('modules', [])
        
        # Extract user data
        user_data = {
            'email': validated_data.pop('email'),
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'phone': validated_data.pop('phone'),
            'user_type': 'teacher',
            'is_active': validated_data.get('is_active', True),
        }
        
        password = validated_data.pop('password', None)
        
        with transaction.atomic():
            # Create user
            user = User.objects.create(**user_data)
            
            # Set password
            if password:
                user.set_password(password)
            else:
                # Generate default password: Teacher@<employee_id>
                default_password = f"Teacher@{validated_data['employee_id']}"
                user.set_password(default_password)
            
            user.save()
            
            # Create teacher
            teacher = Teacher.objects.create(
                user=user,
                **validated_data
            )
            
            # ✅ Assign teacher role using existing function
            if assign_role:
                from core.permission_utils import assign_role_to_user
                user_role, error = assign_role_to_user(user, 'teacher')
                
                if error:
                    print(f"Warning: Could not assign teacher role: {error}")
            
            # ✅ Assign modules using existing function
            if modules:
                from core.permission_utils import assign_modules_to_user
                result = assign_modules_to_user(user, modules)
                
                if result['failed']:
                    print(f"Warning: Failed modules: {result['errors']}")
            
            return teacher


# ========== TEACHER UPDATE SERIALIZER ==========

class TeacherUpdateSerializer(serializers.ModelSerializer):
    """Update teacher information"""
    
    # User fields
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    phone = serializers.CharField(max_length=15, required=False)
    
    class Meta:
        model = Teacher
        fields = [
            # User fields
            'email', 'first_name', 'last_name', 'phone',
            
            # Teacher fields
            'date_of_birth', 'gender', 'blood_group',
            'address', 'city', 'state', 'pincode', 'emergency_contact',
            'qualification', 'specialization', 'experience_years',
            'employment_type',
            'bank_name', 'account_number', 'ifsc_code',
            'pan_number', 'aadhaar_number',
            'is_class_teacher', 'is_active',
        ]
    
    def validate_email(self, value):
        """Check if email already exists (excluding current user)"""
        if User.objects.filter(email=value).exclude(id=self.instance.user.id).exists():
            raise serializers.ValidationError("User with this email already exists")
        return value
    
    def validate_date_of_birth(self, value):
        """Validate date of birth"""
        if value >= date.today():
            raise serializers.ValidationError("Date of birth must be in the past")
        
        age = (date.today() - value).days // 365
        if age < 18:
            raise serializers.ValidationError("Teacher must be at least 18 years old")
        
        return value
    
    def update(self, instance, validated_data):
        """Update teacher and user information"""
        # Extract user data
        user_data = {}
        for field in ['email', 'first_name', 'last_name', 'phone']:
            if field in validated_data:
                user_data[field] = validated_data.pop(field)
        
        with transaction.atomic():
            # Update user
            if user_data:
                for key, value in user_data.items():
                    setattr(instance.user, key, value)
                instance.user.save()
            
            # Update teacher
            for key, value in validated_data.items():
                setattr(instance, key, value)
            instance.save()
            
            return instance


# ========== SUBJECT ASSIGNMENT SERIALIZER ==========

class TeacherSubjectSerializer(serializers.ModelSerializer):
    """Teacher subject assignment serializer"""
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    
    class Meta:
        model = TeacherSubject
        fields = ['id', 'teacher', 'teacher_name', 'subject', 'subject_name', 'subject_code', 'academic_year']
        read_only_fields = ['id']


class SubjectAssignmentSerializer(serializers.Serializer):
    """Assign subjects to teacher"""
    teacher_id = serializers.IntegerField()
    subject_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    class_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Optional: Restrict to specific classes"
    )
    academic_year = serializers.CharField(
        max_length=9,
        required=False,
        help_text="Format: 2024-2025. Defaults to current session"
    )
    
    def validate_teacher_id(self, value):
        """Validate teacher exists and is active"""
        try:
            teacher = Teacher.objects.get(id=value, is_active=True)
            return value
        except Teacher.DoesNotExist:
            raise serializers.ValidationError("Teacher not found or inactive")
    
    def validate_subject_ids(self, value):
        """Validate all subjects exist and are active"""
        subjects = Subject.objects.filter(id__in=value, is_active=True)
        if subjects.count() != len(value):
            invalid_ids = set(value) - set(subjects.values_list('id', flat=True))
            raise serializers.ValidationError(f"Invalid subject IDs: {invalid_ids}")
        return value
    
    def validate_class_ids(self, value):
        """Validate all classes exist and are active"""
        if value:
            classes = Class.objects.filter(id__in=value, is_active=True)
            if classes.count() != len(value):
                invalid_ids = set(value) - set(classes.values_list('id', flat=True))
                raise serializers.ValidationError(f"Invalid class IDs: {invalid_ids}")
        return value
    
    def create(self, validated_data):
        """Assign subjects to teacher"""
        teacher = Teacher.objects.get(id=validated_data['teacher_id'])
        subject_ids = validated_data['subject_ids']
        class_ids = validated_data.get('class_ids', [])
        
        # Get academic year
        academic_year = validated_data.get('academic_year')
        if not academic_year:
            current_session = SchoolSession.objects.filter(is_current=True).first()
            if current_session:
                academic_year = current_session.name
            else:
                raise serializers.ValidationError("No current academic session found")
        
        assignments = []
        
        with transaction.atomic():
            for subject_id in subject_ids:
                # Check if already exists
                teacher_subject, created = TeacherSubject.objects.get_or_create(
                    teacher=teacher,
                    subject_id=subject_id,
                    academic_year=academic_year
                )
                
                # Add classes if provided
                if class_ids:
                    teacher_subject.classes.set(class_ids)
                
                assignments.append(teacher_subject)
        
        return assignments


# ========== TIMETABLE ASSIGNMENT SERIALIZER ==========

class TimeTableSerializer(serializers.ModelSerializer):
    """TimeTable serializer"""
    class_name = serializers.CharField(source='class_obj.display_name', read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    day_display = serializers.CharField(source='get_day_display', read_only=True)
    
    class Meta:
        model = TimeTable
        fields = [
            'id',
            'class_obj',
            'class_name',
            'section',
            'section_name',
            'day',
            'day_display',
            'period',
            'subject',
            'subject_name',
            'teacher',
            'teacher_name',
            'start_time',
            'end_time',
            'room_number',
            'session',
            'is_active'
        ]
        read_only_fields = ['id']


class TimetableAssignmentSerializer(serializers.Serializer):
    """Assign timetable periods to teacher"""
    class_id = serializers.IntegerField()
    section_id = serializers.IntegerField()
    subject_id = serializers.IntegerField()
    teacher_id = serializers.IntegerField()
    day = serializers.ChoiceField(choices=TimeTable.DAY_CHOICES)
    period = serializers.IntegerField(min_value=1, max_value=10)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    room_number = serializers.CharField(max_length=10, required=False, allow_blank=True)
    
    def validate(self, data):
        """Cross-field validation"""
        # Validate start_time < end_time
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError({
                'end_time': 'End time must be after start time'
            })
        
        # Validate all IDs exist
        try:
            class_obj = Class.objects.get(id=data['class_id'], is_active=True)
        except Class.DoesNotExist:
            raise serializers.ValidationError({'class_id': 'Class not found or inactive'})
        
        try:
            section = Section.objects.get(id=data['section_id'], class_obj=class_obj, is_active=True)
        except Section.DoesNotExist:
            raise serializers.ValidationError({'section_id': 'Section not found or does not belong to this class'})
        
        try:
            subject = Subject.objects.get(id=data['subject_id'], is_active=True)
        except Subject.DoesNotExist:
            raise serializers.ValidationError({'subject_id': 'Subject not found or inactive'})
        
        try:
            teacher = Teacher.objects.get(id=data['teacher_id'], is_active=True)
        except Teacher.DoesNotExist:
            raise serializers.ValidationError({'teacher_id': 'Teacher not found or inactive'})
        
        # Get current session
        current_session = class_obj.session
        if not current_session.is_current:
            raise serializers.ValidationError({'class_id': 'Class does not belong to current session'})
        
        # Store validated objects
        data['class_obj'] = class_obj
        data['section'] = section
        data['subject'] = subject
        data['teacher'] = teacher
        data['session'] = current_session
        
        return data
    
    def create(self, validated_data):
        """Create timetable entry"""
        # Check if slot already exists
        existing = TimeTable.objects.filter(
            class_obj=validated_data['class_obj'],
            section=validated_data['section'],
            day=validated_data['day'],
            period=validated_data['period'],
            session=validated_data['session']
        ).first()
        
        if existing:
            raise serializers.ValidationError(
                f"Period {validated_data['period']} on {validated_data['day']} "
                f"is already assigned for this class/section"
            )
        
        # Create timetable entry
        timetable = TimeTable.objects.create(
            class_obj=validated_data['class_obj'],
            section=validated_data['section'],
            day=validated_data['day'],
            period=validated_data['period'],
            subject=validated_data['subject'],
            teacher=validated_data['teacher'],
            start_time=validated_data['start_time'],
            end_time=validated_data['end_time'],
            room_number=validated_data.get('room_number', ''),
            session=validated_data['session'],
            is_active=True
        )
        
        return timetable


# ========== TEACHER ATTENDANCE SERIALIZER ==========

class TeacherAttendanceSerializer(serializers.ModelSerializer):
    """Teacher attendance serializer"""
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    employee_id = serializers.CharField(source='teacher.employee_id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = TeacherAttendance
        fields = [
            'id',
            'teacher',
            'teacher_name',
            'employee_id',
            'date',
            'status',
            'status_display',
            'check_in',
            'check_out',
            'remarks'
        ]
        read_only_fields = ['id']


# ========== TEACHER SALARY SERIALIZER ==========

class TeacherSalarySerializer(serializers.ModelSerializer):
    """Teacher salary serializer"""
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    employee_id = serializers.CharField(source='teacher.employee_id', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    
    class Meta:
        model = TeacherSalary
        fields = [
            'id',
            'teacher',
            'teacher_name',
            'employee_id',
            'month',
            'basic_salary',
            'allowances',
            'deductions',
            'net_salary',
            'payment_date',
            'payment_status',
            'payment_status_display',
            'remarks'
        ]
        read_only_fields = ['id', 'net_salary']
    
    def validate(self, data):
        """Calculate net salary"""
        basic = data.get('basic_salary', 0)
        allowances = data.get('allowances', 0)
        deductions = data.get('deductions', 0)
        
        data['net_salary'] = basic + allowances - deductions
        
        return data




# teachers/serializers.py

class TeacherDashboardSerializer(serializers.Serializer):
    teacher_id = serializers.IntegerField()
    name = serializers.CharField()
    employee_id = serializers.CharField()
    today = serializers.DateField()
    day = serializers.CharField()
    total_classes_today = serializers.IntegerField()
    upcoming_class = serializers.DictField(allow_null=True)
    attendance_summary = serializers.DictField()
    timetable = TimeTableSerializer(many=True)
    
# ========== PERMISSION MANAGEMENT SERIALIZERS ==========

class ModuleSerializer(serializers.ModelSerializer):
    """Module list with permissions"""
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = ['id', 'name', 'display_name', 'icon', 'is_core', 'is_active', 'permissions']
        read_only_fields = ['id']
    
    def get_permissions(self, obj):
        """Get all permissions for this module"""
        permissions = obj.permissions.all()
        return [{
            'id': p.id,
            'action': p.action,
            'codename': p.codename,
            'description': p.description
        } for p in permissions]


class TeacherPermissionDetailSerializer(serializers.Serializer):
    """Teacher with assigned permissions"""
    teacher_id = serializers.IntegerField(source='id', read_only=True)
    employee_id = serializers.CharField(read_only=True)
    name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', read_only=True)
    assigned_permissions = serializers.SerializerMethodField()
    
    def get_name(self, obj):
        return obj.user.get_full_name()
    
    def get_assigned_permissions(self, obj):
        """Get all permissions with module grouping"""
        user_permissions = UserPermission.objects.filter(
            user=obj.user,
            granted=True
        ).select_related('permission', 'permission__module', 'assigned_by')
        
        # Group by module
        modules_dict = {}
        for up in user_permissions:
            module_name = up.permission.module.name if up.permission.module else 'other'
            
            if module_name not in modules_dict:
                modules_dict[module_name] = {
                    'module_id': up.permission.module.id if up.permission.module else None,
                    'module_name': up.permission.module.display_name if up.permission.module else 'Other',
                    'permissions': []
                }
            
            modules_dict[module_name]['permissions'].append({
                'id': up.id,
                'permission_id': up.permission.id,
                'codename': up.permission.codename,
                'action': up.permission.action,
                'granted': up.granted,
                'assigned_by': up.assigned_by.get_full_name() if up.assigned_by else None,
                'assigned_at': up.assigned_at,
                'reason': up.reason
            })
        
        return list(modules_dict.values())


class AssignPermissionSerializer(serializers.Serializer):
    """Assign permissions to teacher"""
    teacher_id = serializers.IntegerField()
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of permission IDs to assign"
    )
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    def validate_teacher_id(self, value):
        """Validate teacher exists"""
        if not Teacher.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Teacher not found or inactive")
        return value
    
    def validate_permission_ids(self, value):
        """Validate permissions exist"""
        if not value:
            raise serializers.ValidationError("At least one permission required")
        
        permissions = Permission.objects.filter(id__in=value)
        if permissions.count() != len(value):
            invalid_ids = set(value) - set(permissions.values_list('id', flat=True))
            raise serializers.ValidationError(f"Invalid permission IDs: {invalid_ids}")
        
        return value
    
    def create(self, validated_data):
        """Assign permissions"""
        teacher = Teacher.objects.get(id=validated_data['teacher_id'])
        permission_ids = validated_data['permission_ids']
        reason = validated_data.get('reason', 'Assigned by admin')
        request = self.context.get('request')
        
        assigned = []
        
        with transaction.atomic():
            for perm_id in permission_ids:
                permission = Permission.objects.get(id=perm_id)
                
                user_perm, created = UserPermission.objects.update_or_create(
                    user=teacher.user,
                    permission=permission,
                    defaults={
                        'granted': True,
                        'assigned_by': request.user if request else None,
                        'reason': reason
                    }
                )
                assigned.append(user_perm)
        
        return {
            'teacher_id': teacher.id,
            'teacher_name': teacher.user.get_full_name(),
            'assigned_count': len(assigned),
            'permissions': [{
                'permission_id': up.permission.id,
                'codename': up.permission.codename,
                'module': up.permission.module.display_name if up.permission.module else None
            } for up in assigned]
        }


class EditPermissionSerializer(serializers.Serializer):
    """Edit teacher permissions (add/remove)"""
    teacher_id = serializers.IntegerField()
    add_permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="Permission IDs to add"
    )
    remove_permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="Permission IDs to remove"
    )
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    def validate(self, data):
        """Ensure at least one action"""
        if not data.get('add_permission_ids') and not data.get('remove_permission_ids'):
            raise serializers.ValidationError(
                "Specify either add_permission_ids or remove_permission_ids"
            )
        return data
    
    def validate_teacher_id(self, value):
        if not Teacher.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Teacher not found")
        return value
    
    def create(self, validated_data):
        """Update permissions"""
        teacher = Teacher.objects.get(id=validated_data['teacher_id'])
        add_ids = validated_data.get('add_permission_ids', [])
        remove_ids = validated_data.get('remove_permission_ids', [])
        reason = validated_data.get('reason', 'Updated by admin')
        request = self.context.get('request')
        
        added_count = 0
        removed_count = 0
        
        with transaction.atomic():
            # Add permissions
            if add_ids:
                for perm_id in add_ids:
                    permission = Permission.objects.get(id=perm_id)
                    UserPermission.objects.update_or_create(
                        user=teacher.user,
                        permission=permission,
                        defaults={
                            'granted': True,
                            'assigned_by': request.user if request else None,
                            'reason': reason
                        }
                    )
                    added_count += 1
            
            # Remove permissions
            if remove_ids:
                removed_count = UserPermission.objects.filter(
                    user=teacher.user,
                    permission_id__in=remove_ids
                ).update(
                    granted=False,
                    assigned_by=request.user if request else None,
                    reason=reason
                )
        
        return {
            'teacher_id': teacher.id,
            'teacher_name': teacher.user.get_full_name(),
            'added': added_count,
            'removed': removed_count
        }