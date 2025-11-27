from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class Assignment(models.Model):
    ASSIGNMENT_TYPES = [
        ('HOMEWORK', 'Homework'),
        ('PROJECT', 'Project'),
        ('QUIZ', 'Quiz'),
        ('ESSAY', 'Essay'),
        ('PRESENTATION', 'Presentation'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('CLOSED', 'Closed'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPES, default='HOMEWORK')
    subject = models.ForeignKey('classes.Subject', on_delete=models.CASCADE, related_name='assignments')
    
    # Class Information
    class_name = models.ForeignKey('classes.Class', on_delete=models.CASCADE, related_name='assignments')
    section = models.ForeignKey('classes.Section', on_delete=models.CASCADE, related_name='assignments')
    
    # Teacher Information
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='assignments_created')
    
    # Dates
    assigned_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    last_submission_date = models.DateField(blank=True, null=True)
    
    # Marks and Grading
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    passing_marks = models.DecimalField(max_digits=5, decimal_places=2, default=40)
    weightage = models.DecimalField(max_digits=5, decimal_places=2, default=0, 
                                  help_text="Weightage in overall grade (percentage)")
    
    # Instructions and Resources
    instructions = models.TextField(blank=True)
    attachment = models.FileField(upload_to='assignments/attachments/', blank=True, null=True)
    external_link = models.URLField(blank=True)
    
    # Status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    is_active = models.BooleanField(default=True)
    allow_late_submission = models.BooleanField(default=False)
    allow_resubmission = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    academic_year = models.CharField(max_length=9)  # Format: 2024-2025
    
    class Meta:
        ordering = ['-due_date', '-created_at']
        indexes = [
            models.Index(fields=['class_name', 'section']),
            models.Index(fields=['due_date']),
            models.Index(fields=['teacher']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.class_name.display_name} {self.section.name}"
    
    def is_past_due(self):
        from django.utils import timezone
        return timezone.now().date() > self.due_date
    
    def get_submission_stats(self):
        total_students = self.section.students.filter(is_active=True).count()
        submitted_count = self.submissions.filter(submitted_at__isnull=False).count()
        graded_count = self.submissions.filter(marks_obtained__isnull=False).count()
        
        return {
            'total_students': total_students,
            'submitted_count': submitted_count,
            'graded_count': graded_count,
            'submission_rate': (submitted_count / total_students * 100) if total_students > 0 else 0
        }


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='assignment_submissions')
    
    # Submission Content
    submission_text = models.TextField(blank=True)
    submission_file = models.FileField(upload_to='assignments/submissions/', blank=True, null=True)
    submission_link = models.URLField(blank=True)
    
    # Grading
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    grade = models.CharField(max_length=2, blank=True)
    teacher_feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_assignments')
    graded_at = models.DateTimeField(blank=True, null=True)
    
    # Status and Dates
    submitted_at = models.DateTimeField(blank=True, null=True)
    is_late = models.BooleanField(default=False)
    resubmission_count = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['assignment', 'student']
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['assignment', 'student']),
            models.Index(fields=['submitted_at']),
        ]
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.assignment.title}"
    
    def save(self, *args, **kwargs):
        # Check if submission is late
        if self.submitted_at and self.assignment.due_date:
            from django.utils import timezone
            if self.submitted_at.date() > self.assignment.due_date:
                self.is_late = True
        
        # Auto-calculate grade based on marks
        if self.marks_obtained is not None and self.assignment.total_marks > 0:
            percentage = (self.marks_obtained / self.assignment.total_marks) * 100
            if percentage >= 90:
                self.grade = 'A+'
            elif percentage >= 80:
                self.grade = 'A'
            elif percentage >= 70:
                self.grade = 'B+'
            elif percentage >= 60:
                self.grade = 'B'
            elif percentage >= 50:
                self.grade = 'C'
            elif percentage >= 40:
                self.grade = 'D'
            else:
                self.grade = 'F'
        
        super().save(*args, **kwargs)
    
    def get_percentage(self):
        if self.marks_obtained is not None and self.assignment.total_marks > 0:
            return (self.marks_obtained / self.assignment.total_marks) * 100
        return None


class AssignmentGrade(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='assignment_grades')
    subject = models.ForeignKey('classes.Subject', on_delete=models.CASCADE, related_name='assignment_grades')
    academic_year = models.CharField(max_length=9)
    
    total_assignments = models.IntegerField(default=0)
    assignments_submitted = models.IntegerField(default=0)
    assignments_graded = models.IntegerField(default=0)
    
    total_marks = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    obtained_marks = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    average_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overall_grade = models.CharField(max_length=2, blank=True)
    
    class Meta:
        unique_together = ['student', 'subject', 'academic_year']
        ordering = ['subject', 'academic_year']
    
    def __str__(self):
        return f"{self.student} - {self.subject} - {self.academic_year}"
    
    def update_stats(self):
        from django.db.models import Sum, Count
        from .models import AssignmentSubmission
        
        submissions = AssignmentSubmission.objects.filter(
            student=self.student,
            assignment__subject=self.subject,
            assignment__academic_year=self.academic_year
        )
        
        self.total_assignments = submissions.count()
        self.assignments_submitted = submissions.filter(submitted_at__isnull=False).count()
        self.assignments_graded = submissions.filter(marks_obtained__isnull=False).count()
        
        # Calculate total and obtained marks
        graded_submissions = submissions.filter(marks_obtained__isnull=False)
        if graded_submissions.exists():
            self.total_marks = sum(sub.assignment.total_marks for sub in graded_submissions)
            self.obtained_marks = sum(sub.marks_obtained for sub in graded_submissions)
            if self.total_marks > 0:
                self.average_percentage = (self.obtained_marks / self.total_marks) * 100
                
                # Calculate overall grade
                if self.average_percentage >= 90:
                    self.overall_grade = 'A+'
                elif self.average_percentage >= 80:
                    self.overall_grade = 'A'
                elif self.average_percentage >= 70:
                    self.overall_grade = 'B+'
                elif self.average_percentage >= 60:
                    self.overall_grade = 'B'
                elif self.average_percentage >= 50:
                    self.overall_grade = 'C'
                elif self.average_percentage >= 40:
                    self.overall_grade = 'D'
                else:
                    self.overall_grade = 'F'
        
        self.save()