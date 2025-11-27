from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class ExamType(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    total_marks = models.IntegerField(default=100)
    passing_marks = models.IntegerField(default=33)
    weightage = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # For final calculation
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class ExamSchedule(models.Model):
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE, related_name='schedules')
    class_name = models.ForeignKey('classes.Class', on_delete=models.CASCADE, related_name='exam_schedules')
    subject = models.ForeignKey('classes.Subject', on_delete=models.CASCADE)
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.IntegerField(help_text="Duration in minutes")
    maximum_marks = models.IntegerField(default=100)
    passing_marks = models.IntegerField(default=33)
    room_number = models.CharField(max_length=10, blank=True)
    academic_year = models.CharField(max_length=9)  # Format: 2024-2025
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['exam_type', 'class_name', 'subject', 'academic_year']
        ordering = ['exam_date', 'start_time']
    
    def __str__(self):
        return f"{self.exam_type.name} - {self.class_name.display_name} - {self.subject.name}"


class ExamResult(models.Model):
    GRADE_CHOICES = [
        ('A+', 'A+ (Outstanding)'),
        ('A', 'A (Excellent)'),
        ('B+', 'B+ (Very Good)'),
        ('B', 'B (Good)'),
        ('C+', 'C+ (Average)'),
        ('C', 'C (Below Average)'),
        ('D', 'D (Marginal)'),
        ('E', 'E (Unsatisfactory)'),
        ('F', 'F (Fail)'),
    ]
    
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='exam_results')
    exam_schedule = models.ForeignKey(ExamSchedule, on_delete=models.CASCADE, related_name='results')
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    practical_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_marks = models.DecimalField(max_digits=6, decimal_places=2)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True)
    remarks = models.TextField(blank=True)
    entered_by = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True)
    entered_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'exam_schedule']
        ordering = ['exam_schedule', 'student']
        indexes = [
            models.Index(fields=['student', 'exam_schedule']),
        ]
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.exam_schedule} - {self.marks_obtained}"


class FinalResult(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='final_results')
    class_name = models.ForeignKey('classes.Class', on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=9)  # Format: 2024-2025
    total_marks = models.DecimalField(max_digits=7, decimal_places=2)
    marks_obtained = models.DecimalField(max_digits=7, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=2, choices=ExamResult.GRADE_CHOICES)
    rank = models.IntegerField(null=True, blank=True)
    result_status = models.CharField(max_length=15, choices=[
    ('PASS', 'Pass'),
    ('FAIL', 'Fail'),
    ('COMPARTMENT', 'Compartment'),
])
    generated_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'academic_year']
        ordering = ['-academic_year', 'rank']
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.academic_year} - {self.percentage}%"


class MarkSheet(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='mark_sheets')
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=9)  # Format: 2024-2025
    total_marks = models.DecimalField(max_digits=7, decimal_places=2)
    marks_obtained = models.DecimalField(max_digits=7, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=2, choices=ExamResult.GRADE_CHOICES)
    rank = models.IntegerField(null=True, blank=True)
    generated_on = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False)
    published_on = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'exam_type', 'academic_year']
        ordering = ['-academic_year', 'exam_type']
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.exam_type.name} - {self.academic_year}"