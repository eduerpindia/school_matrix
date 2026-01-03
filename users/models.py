from django.contrib.auth.models import AbstractUser
from django.db import models
class User(AbstractUser):
    USER_TYPES = [
        ('school_admin', 'School Admin'),
        ('principal', 'Principal'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
        ('staff', 'Staff'),
        ('accountant', 'Accountant'),
    ]
    
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='student')
 
    school_id = models.IntegerField(null=True, blank=True, help_text="ID of the school in public schema")
    school_code = models.CharField(max_length=20, blank=True, null=True, help_text="School code for reference")
    
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, blank=True, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        ordering = ['email']

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"