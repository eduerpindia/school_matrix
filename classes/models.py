from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Class(models.Model):
    CLASS_CHOICES = [
        ('1', 'Class 1'),
        ('2', 'Class 2'),
        ('3', 'Class 3'),
        ('4', 'Class 4'),
        ('5', 'Class 5'),
        ('6', 'Class 6'),
        ('7', 'Class 7'),
        ('8', 'Class 8'),
        ('9', 'Class 9'),
        ('10', 'Class 10'),
        ('11', 'Class 11'),
        ('12', 'Class 12'),
    ]
    
    name = models.CharField(max_length=10, choices=CLASS_CHOICES, unique=True)
    display_name = models.CharField(max_length=20)
    capacity = models.IntegerField(default=40)
    class_teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, 
                                    null=True, blank=True, related_name='class_teacher_of')
    room_number = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Classes"
    
    def __str__(self):
        return self.display_name


class Section(models.Model):
    SECTION_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E'),
    ]
    
    class_name = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=1, choices=SECTION_CHOICES)
    capacity = models.IntegerField(default=40)
    section_incharge = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, 
                                       null=True, blank=True, related_name='section_incharge_of')
    room_number = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['class_name', 'name']
        ordering = ['class_name', 'name']
    
    def __str__(self):
        return f"{self.class_name.display_name} - Section {self.name}"


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    theory_marks = models.IntegerField(default=100)
    practical_marks = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class ClassSubject(models.Model):
    class_name = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, 
                              null=True, blank=True)
    periods_per_week = models.IntegerField(default=5)
    is_optional = models.BooleanField(default=False)
    academic_year = models.CharField(max_length=9)  # Format: 2024-2025
    
    class Meta:
        unique_together = ['class_name', 'subject', 'academic_year']
    
    def __str__(self):
        return f"{self.class_name.display_name} - {self.subject.name}"


class TimeTable(models.Model):
    DAY_CHOICES = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
    ]
    
    class_name = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='timetables')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='timetables')
    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    period = models.IntegerField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room_number = models.CharField(max_length=10, blank=True)
    academic_year = models.CharField(max_length=9)  # Format: 2024-2025
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['class_name', 'section', 'day', 'period', 'academic_year']
        ordering = ['day', 'period']
    
    def __str__(self):
        return f"{self.class_name.display_name} {self.section.name} - {self.day} P{self.period}"