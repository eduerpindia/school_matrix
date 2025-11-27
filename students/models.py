from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

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
    photo = models.ImageField(upload_to='students/photos/', blank=True)
    birth_certificate = models.FileField(upload_to='students/documents/', blank=True)
    aadhaar_card = models.FileField(upload_to='students/documents/', blank=True)
    
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
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='academic_records')
    academic_year = models.CharField(max_length=9)  # Format: 2024-2025
    class_enrolled = models.ForeignKey('classes.Class', on_delete=models.CASCADE)
    section = models.ForeignKey('classes.Section', on_delete=models.CASCADE)
    roll_number = models.IntegerField()
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=2, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['student', 'academic_year']
        ordering = ['-academic_year']


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
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='students/documents/')
    upload_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.get_document_type_display()}"


class StudentAttendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    status = models.CharField(max_length=1, choices=[
        ('P', 'Present'),
        ('A', 'Absent'),
        ('L', 'Late'),
        ('H', 'Half Day'),
    ])
    remarks = models.CharField(max_length=100, blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.date} - {self.get_status_display()}"