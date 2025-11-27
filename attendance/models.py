from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Attendance(models.Model):
    ATTENDANCE_STATUS = [
        ('P', 'Present'),
        ('A', 'Absent'),
        ('L', 'Late'),
        ('H', 'Half Day'),
    ]
    
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=1, choices=ATTENDANCE_STATUS)
    period = models.IntegerField(null=True, blank=True)  # For period-wise attendance
    subject = models.ForeignKey('classes.Subject', on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.CharField(max_length=100, blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    marked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'date', 'period', 'subject']
        ordering = ['-date', 'student']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['student', 'date']),
        ]
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.date} - {self.get_status_display()}"


class AttendanceReport(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='attendance_reports')
    month = models.CharField(max_length=7)  # Format: 2024-03
    total_days = models.IntegerField()
    present_days = models.IntegerField()
    absent_days = models.IntegerField()
    late_days = models.IntegerField(default=0)
    half_days = models.IntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    generated_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'month']
        ordering = ['-month']
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.month} - {self.percentage}%"


class Holiday(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()
    type = models.CharField(max_length=20, choices=[
        ('NATIONAL', 'National Holiday'),
        ('STATE', 'State Holiday'),
        ('SCHOOL', 'School Holiday'),
        ('OTHER', 'Other'),
    ])
    description = models.TextField(blank=True)
    academic_year = models.CharField(max_length=9)  # Format: 2024-2025
    
    class Meta:
        unique_together = ['date', 'academic_year']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.name} - {self.date}"


class LeaveApplication(models.Model):
    LEAVE_TYPES = [
        ('CASUAL', 'Casual Leave'),
        ('SICK', 'Sick Leave'),
        ('EARNED', 'Earned Leave'),
        ('MATERNITY', 'Maternity Leave'),
        ('PATERNITY', 'Paternity Leave'),
        ('OTHER', 'Other Leave'),
    ]
    
    LEAVE_STATUS = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_applications')
    leave_type = models.CharField(max_length=10, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.IntegerField()
    reason = models.TextField()
    supporting_document = models.FileField(upload_to='leaves/documents/', blank=True)
    status = models.CharField(max_length=10, choices=LEAVE_STATUS, default='PENDING')
    applied_on = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='approved_leaves')
    approved_on = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-applied_on']
    
    def __str__(self):
        return f"{self.applicant.get_full_name()} - {self.leave_type} - {self.status}"