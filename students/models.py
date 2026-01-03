from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import AcademicYear
import os
from datetime import datetime
User = get_user_model()

class Student(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    CATEGORY_CHOICES = [
        ('GEN', 'General'),
        ('OBC', 'OBC'),
        ('SC', 'SC'),
        ('ST', 'ST'),
        ('OTHER', 'Other'),
    ]
    
    # Personal Information
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    admission_number = models.CharField(max_length=20, unique=True)
    admission_date = models.DateField()
    college_email = models.EmailField(unique=True, null=True , blank=True,  help_text="Auto-generated college email for login")
    # Personal Details
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    nationality = models.CharField(max_length=50, default='Indian')
    religion = models.CharField(max_length=50, blank=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='GEN')
    aadhaar_number = models.CharField(max_length=12, blank=True, unique=True)
    
    # Contact Information
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    emergency_contact = models.CharField(max_length=15)
    
    # Academic Information
    current_class = models.ForeignKey('classes.Class', on_delete=models.SET_NULL, null=True, related_name='students')
    section = models.ForeignKey('classes.Section', on_delete=models.SET_NULL, null=True, related_name='students')
    roll_number = models.IntegerField()
    
    # Parent/Guardian Information
    father_name = models.CharField(max_length=100)
    father_occupation = models.CharField(max_length=100, blank=True)
    father_phone = models.CharField(max_length=15, blank=True)
    father_email = models.EmailField(blank=True)
    
    mother_name = models.CharField(max_length=100)
    mother_occupation = models.CharField(max_length=100, blank=True)
    mother_phone = models.CharField(max_length=15, blank=True)
    mother_email = models.EmailField(blank=True)
    
    guardian_name = models.CharField(max_length=100, blank=True)
    guardian_relation = models.CharField(max_length=50, blank=True)
    guardian_phone = models.CharField(max_length=15, blank=True)
    guardian_email = models.EmailField(blank=True)
    
    # Medical Information
    medical_conditions = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    regular_medications = models.TextField(blank=True)
    
    # Documents
    photo = models.ImageField(upload_to='students/photos/',null=True, blank=True)
    birth_certificate = models.FileField(upload_to='students/documents/',null=True, blank=True)
    aadhaar_card = models.FileField(upload_to='students/documents/', null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['current_class', 'section', 'roll_number']
        indexes = [
            models.Index(fields=['admission_number']),
            models.Index(fields=['current_class', 'section', 'roll_number']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.admission_number})"



class StudentAcademicRecord(models.Model):
    STATUS_CHOICES = [
        ('NEW_ADMISSION', 'New Admission'),
        ('PROMOTED', 'Promoted'),
        ('DETAINED', 'Detained'),
        ('PASSED_OUT', 'Passed Out'),
        ('TRANSFERRED', 'Transferred'),
        ('LEFT_SCHOOL', 'Left School'),
    ]
    
    student = models.ForeignKey(
        'Student',
        on_delete=models.CASCADE,
        related_name='academic_records'
    )
    
    # ✅ MUST HAVE THIS FIELD
    session = models.ForeignKey(
        'schools.SchoolSession',
        on_delete=models.CASCADE,
        related_name='student_records'
    )
    
    class_enrolled = models.ForeignKey(
        'classes.Class',
        on_delete=models.CASCADE
    )
    
    section = models.ForeignKey(
        'classes.Section',
        on_delete=models.CASCADE
    )
    
    roll_number = models.IntegerField()
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=2, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    status = models.CharField(max_length=35, choices=STATUS_CHOICES)
    
    class Meta:
        unique_together = ['student', 'session']
        ordering = ['-id']
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.session.name}"


from django.conf import settings

class StudentDocument(models.Model):
    DOCUMENT_TYPES = [
        ('BIRTH', 'Birth Certificate'),
        ('AADHAAR', 'Aadhaar Card'),
        ('TRANSFER', 'Transfer Certificate'),
        ('MEDICAL', 'Medical Certificate'),
        ('CAST', 'Caste Certificate'),
        ('INCOME', 'Income Certificate'),
        ('PHOTO', 'Photograph'),
        ('OTHER', 'Other'),
    ]
    
    def upload_to_path(instance, filename):
        """
        Dynamic file upload path using school_code from tenant
        Format: students/documents/{school_code}/{school_name}/{document_type}/{admission_number}/{filename}_{timestamp}.ext
        Example: students/documents/BFA01/BFA_School/Birth_Certificate/BFA01_ADM_0001/Birth_Certificate_20251207_223045.pdf
        """
        _, extension = os.path.splitext(filename)
        
        # Get tenant (school) info from request (set by middleware)
        from schools.models import School
        
        # Get school from student (already in database context)
        try:
            # Access through student's related school (if you have this relation)
            # Or get from current tenant context
            from django.db import connection
            
            # Get school using connection schema
            tenant_schema = connection.schema_name
            school = School.objects.get(schema_name=tenant_schema)
            
            school_code = school.school_code  # e.g., BFA01
            school_name = school.name.replace(' ', '_')
        except:
            school_code = 'DEFAULT'
            school_name = 'School'
        
        # Get document type display name
        document_type_display = dict(StudentDocument.DOCUMENT_TYPES).get(
            instance.document_type, 
            'Other'
        ).replace(' ', '_')
        
        # Get student admission number (clean it)
        admission_number = instance.student.admission_number.replace('-', '_')
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = filename.rsplit('.', 1)[0].replace(' ', '_')
        
        # Final path: students/documents/{school_code}/{school_name}/{document_type}/{admission_number}/{filename}_{timestamp}.ext
        path = (
            f'{settings.STUDENT_DOCUMENT_FILE_LOCATION}'
            f'{school_code}/'
            f'{school_name}/'
            f'{document_type_display}/'
            f'{admission_number}/'
            f'{safe_filename}_{timestamp}{extension}'
        )
        
        return path.replace(' ', '_')
    
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to=upload_to_path, max_length=500)
    upload_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_documents')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-upload_date']
        verbose_name = 'Student Document'
        verbose_name_plural = 'Student Documents'
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.get_document_type_display()}"
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class StudentAttendance(models.Model):
    """
    Period-wise (Subject-wise) attendance tracking
    All dates/times in IST - No timezone
    """
    
    ATTENDANCE_STATUS = [
        ('P', 'Present'),
        ('A', 'Absent'),
        ('L', 'Late'),
        ('H', 'Half Day'),
        ('E', 'Excused'),
    ]
    
    # Student Info
    student = models.ForeignKey(
        'Student', 
        on_delete=models.CASCADE, 
        related_name='attendance_records'
    )
    
    # Date
    date = models.DateField()
    
    # Period/Subject Info
    timetable = models.ForeignKey(
        'classes.TimeTable',
        on_delete=models.CASCADE,
        related_name='attendance_records',
        null=True,
        blank=True
    )
    
    class_obj = models.ForeignKey(
        'classes.Class',
        on_delete=models.CASCADE,
        related_name='student_attendances',
        null=True,
        blank=True
    )
    section = models.ForeignKey(
        'classes.Section',
        on_delete=models.CASCADE,
        related_name='student_attendances',
        null=True,
        blank=True
    )
    subject = models.ForeignKey(
        'classes.Subject',
        on_delete=models.CASCADE,
        related_name='student_attendances',
        null=True,
        blank=True
    )
    period_number = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    
    # Attendance Status
    status = models.CharField(
        max_length=1, 
        choices=ATTENDANCE_STATUS,
        default='P'
    )
    
    # Additional Info
    remarks = models.TextField(
        blank=True,
        null=True
    )
    
    # Tracking Info
    marked_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='marked_attendances'
    )
    
    # Simple datetime - No timezone
    marked_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Session
    session = models.ForeignKey(
        'schools.SchoolSession',
        on_delete=models.PROTECT,
        related_name='student_attendances',
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['-date', 'period_number']
        verbose_name = "Student Attendance"
        verbose_name_plural = "Student Attendances"
        
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'date', 'timetable'],
                name='unique_student_period_attendance',
                condition=models.Q(timetable__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['student', 'date', 'subject', 'period_number'],
                name='unique_student_subject_period_attendance',
                condition=models.Q(timetable__isnull=True) & 
                         models.Q(subject__isnull=False) & 
                         models.Q(period_number__isnull=False)
            ),
        ]
        
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['date', 'class_obj', 'section']),
            models.Index(fields=['subject', 'date']),
            models.Index(fields=['status', 'date']),
        ]
    
    def clean(self):
        """Model-level validation"""
        if self.class_obj and self.student.current_class and self.student.current_class != self.class_obj:
            raise ValidationError({'student': _('Student does not belong to this class')})
        
        if self.section and self.student.section and self.student.section != self.section:
            raise ValidationError({'student': _('Student does not belong to this section')})
        
        if self.session and self.class_obj and self.class_obj.session and self.session != self.class_obj.session:
            raise ValidationError({'session': _('Session must match the class session')})
        
        if self.timetable:
            if self.subject and self.timetable.subject != self.subject:
                raise ValidationError({'subject': _('Subject does not match timetable')})
            
            if self.period_number and self.timetable.period != self.period_number:
                raise ValidationError({'period_number': _('Period number does not match timetable')})
    
    def save(self, *args, **kwargs):
        # Auto-set marked_at if not provided
        if not self.marked_at:
            self.marked_at = datetime.now()
        
        # Auto-populate from timetable
        if self.timetable and not self.subject:
            self.subject = self.timetable.subject
            self.period_number = self.timetable.period
            self.class_obj = self.timetable.class_obj
            self.section = self.timetable.section
        
        # Auto-populate session
        if not self.session and self.class_obj and self.class_obj.session:
            self.session = self.class_obj.session
        
        # Auto-populate class/section from student
        if not self.class_obj and self.student.current_class:
            self.class_obj = self.student.current_class
        
        if not self.section and self.student.section:
            self.section = self.student.section
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        parts = [self.student.admission_number]
        if self.subject:
            parts.append(self.subject.name)
        if self.period_number:
            parts.append(f"Period {self.period_number}")
        parts.append(str(self.date))
        parts.append(self.get_status_display())
        return " - ".join(parts)
    
    
class IDCardTemplate(models.Model):
    """
    ID Card Templates - Admin can create multiple templates
    Each template has different design and fields
    """
    ORIENTATION_CHOICES = [
        ('PORTRAIT', 'Portrait (Vertical)'),
        ('LANDSCAPE', 'Landscape (Horizontal)'),
    ]
    
    CARD_SIZE_CHOICES = [
        ('CR80', 'Standard (85.6mm x 54mm)'),  # Credit card size
        ('A6', 'A6 (105mm x 148mm)'),
        ('CUSTOM', 'Custom Size'),
    ]
    
    # Template Info
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Template name (e.g., 'Blue Modern', 'Classic Red')"
    )
    
    description = models.TextField(blank=True)
    
    # Design Settings
    orientation = models.CharField(
        max_length=10,
        choices=ORIENTATION_CHOICES,
        default='PORTRAIT'
    )
    
    card_size = models.CharField(
        max_length=10,
        choices=CARD_SIZE_CHOICES,
        default='CR80'
    )
    
    # Custom dimensions (if CUSTOM size)
    width_mm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    height_mm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Preview
    preview_image = models.ImageField(
        upload_to='id_cards/templates/previews/',
        null=True,
        blank=True
    )
    
    # ========== DYNAMIC FIELDS CONFIGURATION ==========
    # This JSON stores which fields to show on card
    front_fields = models.JSONField(
        default=list,
        help_text="Fields to show on front side"
    )
    """
    Example front_fields:
    [
        {
            "field_name": "photo",
            "show": true,
            "position": {"x": 20, "y": 30},
            "size": {"width": 100, "height": 120}
        },
        {
            "field_name": "name",
            "show": true,
            "position": {"x": 140, "y": 40},
            "font_size": 16,
            "font_weight": "bold",
            "color": "#000000"
        },
        {
            "field_name": "admission_number",
            "show": true,
            "position": {"x": 140, "y": 65},
            "font_size": 14
        },
        {
            "field_name": "class_section",
            "show": true,
            "position": {"x": 140, "y": 85}
        },
        {
            "field_name": "dob",
            "show": true,
            "position": {"x": 140, "y": 105},
            "format": "DD/MM/YYYY"
        },
        {
            "field_name": "qr_code",
            "show": true,
            "position": {"x": 240, "y": 140},
            "size": {"width": 70, "height": 70}
        }
    ]
    """
    
    back_fields = models.JSONField(
        default=list,
        help_text="Fields to show on back side"
    )
    """
    Example back_fields:
    [
        {
            "field_name": "address",
            "show": true,
            "position": {"x": 20, "y": 30},
            "max_lines": 3
        },
        {
            "field_name": "father_name",
            "show": true,
            "position": {"x": 20, "y": 80}
        },
        {
            "field_name": "emergency_contact",
            "show": true,
            "position": {"x": 20, "y": 100}
        },
        {
            "field_name": "blood_group",
            "show": true,
            "position": {"x": 20, "y": 120}
        }
    ]
    """
    
    # ========== STYLING CONFIGURATION ==========
    style_config = models.JSONField(
        default=dict,
        help_text="CSS and design styling"
    )
    """
    Example style_config:
    {
        "background_color": "#ffffff",
        "primary_color": "#0066cc",
        "secondary_color": "#f0f0f0",
        "border_color": "#0066cc",
        "border_width": "2px",
        "border_radius": "10px",
        "font_family": "Arial, sans-serif",
        "header_bg_color": "#0066cc",
        "footer_text": "Property of School"
    }
    """
    
    # School branding
    show_school_logo = models.BooleanField(default=True)
    logo_position = models.JSONField(
        default=dict,
        help_text="Logo position and size"
    )
    
    show_school_name = models.BooleanField(default=True)
    
    background_image = models.ImageField(
        upload_to='id_cards/templates/backgrounds/',
        null=True,
        blank=True
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_id_templates'
    )
    
    class Meta:
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        # Only one default template
        if self.is_default:
            existing = IDCardTemplate.objects.filter(
                is_default=True
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError('Only one template can be default')


class StudentIDCard(models.Model):
    """
    Generated ID Cards for students
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('GENERATED', 'Generated'),
        ('APPROVED', 'Approved'),
        ('PRINTED', 'Printed'),
        ('ISSUED', 'Issued'),
    ]
    
    student = models.ForeignKey(
        'Student',
        on_delete=models.CASCADE,
        related_name='id_cards'
    )
    
    template = models.ForeignKey(
        IDCardTemplate,
        on_delete=models.PROTECT,
        related_name='generated_cards'
    )
    
    # Generated Files
    front_image = models.FileField(
        upload_to='id_cards/generated/front/%Y/%m/',
        null=True,
        blank=True
    )
    
    back_image = models.FileField(
        upload_to='id_cards/generated/back/%Y/%m/',
        null=True,
        blank=True
    )
    
    combined_pdf = models.FileField(
        upload_to='id_cards/generated/pdf/%Y/%m/',
        null=True,
        blank=True,
        help_text="Combined front + back PDF"
    )
    
    # Card Details
    card_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique card number"
    )
    
    qr_code_data = models.TextField(
        blank=True,
        help_text="Data encoded in QR code"
    )
    
    # Validity
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    
    # Tracking
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_id_cards'
    )
    
    session = models.ForeignKey(
        'schools.SchoolSession',
        on_delete=models.PROTECT,
        related_name='id_cards'
    )
    
    class Meta:
        ordering = ['-generated_at']
        unique_together = ['student', 'session', 'template']
    
    def __str__(self):
        return f"{self.card_number} - {self.student.admission_number}"