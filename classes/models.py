# classes/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum


User = get_user_model()


class Class(models.Model):
    CLASS_CHOICES = [
        ('LKG', 'LKG'),
        ('UKG', 'UKG'),
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

    name = models.CharField(
        max_length=10,
        choices=CLASS_CHOICES,
        unique=True,
        help_text="Internal class code, e.g. 1, 2, 10, 12.",
    )
    display_name = models.CharField(
        max_length=20,
        help_text="Human readable name, e.g. Class 1, Class 10 Science.",
    )
    session = models.ForeignKey(
        'schools.SchoolSession',
        on_delete=models.PROTECT,
        related_name='classes',
        help_text="Academic session for this class"
    )
    capacity = models.PositiveIntegerField(default=40)
    class_teacher = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classes_as_class_teacher',
    )
    room_number = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Class"
        verbose_name_plural = "Classes"
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'session'],
                name='unique_class_per_session',
            ),
        ]

    def clean(self):
        """Model-level validation"""
        if self.capacity < 1:
            raise ValidationError({
                'capacity': _('Capacity must be at least 1.')
            })
        
        if self.class_teacher and not self.class_teacher.is_active:
            raise ValidationError({
                'class_teacher': _('Selected teacher is not active.')
            })
        
        if self.session and not self.session.is_current:
            raise ValidationError({
                'session': _('Cannot create class for inactive session.')
            })
        
        # ✅ FIX 1: Validate total section capacity doesn't exceed class capacity
        if self.pk:  # Only for updates
            total_section_capacity = self.sections.filter(is_active=True).aggregate(
                total=Sum('capacity')
            )['total'] or 0
            
            if total_section_capacity > self.capacity:
                raise ValidationError({
                    'capacity': _(
                        f'Class capacity ({self.capacity}) cannot be less than '
                        f'total section capacity ({total_section_capacity}). '
                        f'Please increase class capacity or reduce section capacities.'
                    )
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.display_name} ({self.session.name})"


class Section(models.Model):
    SECTION_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E'),
    ]

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='sections',
    )
    name = models.CharField(
        max_length=1,
        choices=SECTION_CHOICES,
        help_text="Section letter, e.g. A, B, C.",
    )
    capacity = models.PositiveIntegerField(default=40)
    section_incharge = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sections_incharge_of',
    )
    room_number = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['class_obj__name', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['class_obj', 'name'],
                name='unique_class_section',
            ),
        ]

    @property
    def session(self):
        return self.class_obj.session

    def clean(self):
        """Model-level validation"""
        if self.capacity < 1:
            raise ValidationError({
                'capacity': _('Capacity must be at least 1.')
            })

        if not self.class_obj.is_active:
            raise ValidationError({
                'class_obj': _('Cannot create section for inactive class.')
            })
        
        if self.section_incharge and not self.section_incharge.is_active:
            raise ValidationError({
                'section_incharge': _('Selected teacher is not active.')
            })
        
        # ✅ FIX 1: Validate section capacity against class capacity
        # Get total capacity of other sections in same class
        other_sections_capacity = Section.objects.filter(
            class_obj=self.class_obj,
            is_active=True
        ).exclude(pk=self.pk).aggregate(
            total=Sum('capacity')
        )['total'] or 0
        
        total_capacity = other_sections_capacity + self.capacity
        
        if total_capacity > self.class_obj.capacity:
            raise ValidationError({
                'capacity': _(
                    f'Section capacity ({self.capacity}) + other sections capacity '
                    f'({other_sections_capacity}) = {total_capacity} exceeds class '
                    f'capacity ({self.class_obj.capacity}). Maximum allowed: '
                    f'{self.class_obj.capacity - other_sections_capacity}'
                )
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.class_obj.display_name} - Section {self.name} ({self.session.name})"


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    
    # ✅ FIX 2: Add field to mark core subjects
    is_core = models.BooleanField(
        default=True,
        help_text="Core subjects (like Math, Science) must have a teacher assigned"
    )
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class ClassSubject(models.Model):
    """
    Mapping of (Class, optional Section) to Subject with assigned teacher
    for a specific academic session.
    """

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='class_subjects',
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='section_subjects',
        help_text="Keep null if subject is common for entire class.",
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taught_subjects',
    )
    session = models.ForeignKey(
        'schools.SchoolSession',
        on_delete=models.PROTECT,
        related_name='class_subjects',
        help_text="Academic session for this subject assignment"
    )
    periods_per_week = models.PositiveIntegerField(default=5)
    is_optional = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Class Subject"
        verbose_name_plural = "Class Subjects"
        constraints = [
            models.UniqueConstraint(
                fields=['class_obj', 'section', 'subject', 'session'],
                name='unique_class_section_subject_session',
            ),
        ]

    def clean(self):
        """Model-level validation"""
        if not self.class_obj.is_active:
            raise ValidationError({
                'class_obj': _('Cannot assign subject to inactive class.')
            })

        if not self.subject.is_active:
            raise ValidationError({
                'subject': _('Cannot assign inactive subject.')
            })

        if self.section:
            if self.section.class_obj != self.class_obj:
                raise ValidationError({
                    'section': _('Section does not belong to the selected class.')
                })
            if not self.section.is_active:
                raise ValidationError({
                    'section': _('Cannot assign subject to inactive section.')
                })

        if self.teacher and not self.teacher.is_active:
            raise ValidationError({
                'teacher': _('Cannot assign inactive teacher.')
            })

        if self.periods_per_week < 1 or self.periods_per_week > 20:
            raise ValidationError({
                'periods_per_week': _('Periods per week must be between 1 and 20.')
            })
        
        if self.session != self.class_obj.session:
            raise ValidationError({
                'session': _('Session must match the class session.')
            })
        
        if not self.session.is_current:
            raise ValidationError({
                'session': _('Cannot assign subject to inactive session.')
            })
        
        # ✅ FIX 2: Core subjects must have teacher assigned
        if self.subject.is_core and not self.is_optional and not self.teacher:
            raise ValidationError({
                'teacher': _(
                    f'{self.subject.name} is a core subject and must have a teacher assigned. '
                    f'Either assign a teacher or mark this subject as optional.'
                )
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.section:
            return f"{self.class_obj.display_name} - {self.section.name} - {self.subject.name} ({self.session.name})"
        return f"{self.class_obj.display_name} - {self.subject.name} ({self.session.name})"


class TimeTable(models.Model):
    DAY_CHOICES = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
    ]

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='timetables',
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='timetables',
    )
    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    period = models.PositiveIntegerField(help_text="Period number in the day.")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room_number = models.CharField(max_length=10, blank=True)
    session = models.ForeignKey(
        'schools.SchoolSession',
        on_delete=models.PROTECT,
        related_name='timetables',
        help_text="Academic session for this timetable"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['day', 'period']
        constraints = [
            models.UniqueConstraint(
                fields=['class_obj', 'section', 'day', 'period', 'session'],
                name='unique_timetable_slot',
            ),
        ]

    def clean(self):
        """Model-level validation"""
        if self.start_time >= self.end_time:
            raise ValidationError({
                'end_time': _('End time must be after start time.')
            })

        if self.section.class_obj != self.class_obj:
            raise ValidationError({
                'section': _('Section does not belong to the selected class.')
            })

        if not self.teacher.is_active:
            raise ValidationError({
                'teacher': _('Cannot assign inactive teacher.')
            })

        if not self.subject.is_active:
            raise ValidationError({
                'subject': _('Cannot assign inactive subject.')
            })
        
        if self.session != self.class_obj.session:
            raise ValidationError({
                'session': _('Session must match the class session.')
            })

        # ✅ FIX 3: Check teacher availability (no double booking)
        teacher_conflicts = TimeTable.objects.filter(
            teacher=self.teacher,
            day=self.day,
            session=self.session,
            is_active=True
        ).exclude(pk=self.pk)

        for slot in teacher_conflicts:
            if not (self.end_time <= slot.start_time or self.start_time >= slot.end_time):
                raise ValidationError({
                    'teacher': _(
                        f'Teacher {self.teacher.get_full_name()} is already assigned to '
                        f'{slot.class_obj.display_name} {slot.section.name} from '
                        f'{slot.start_time.strftime("%H:%M")} to {slot.end_time.strftime("%H:%M")} '
                        f'on {slot.get_day_display()}.'
                    )
                })
        
        # ✅ FIX 3: Check room availability (no double booking)
        if self.room_number:
            room_conflicts = TimeTable.objects.filter(
                room_number=self.room_number,
                day=self.day,
                session=self.session,
                is_active=True
            ).exclude(pk=self.pk)
            
            for slot in room_conflicts:
                if not (self.end_time <= slot.start_time or self.start_time >= slot.end_time):
                    raise ValidationError({
                        'room_number': _(
                            f'Room {self.room_number} is already occupied by '
                            f'{slot.class_obj.display_name} {slot.section.name} from '
                            f'{slot.start_time.strftime("%H:%M")} to {slot.end_time.strftime("%H:%M")} '
                            f'on {slot.get_day_display()}.'
                        )
                    })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.class_obj.display_name} {self.section.name} - {self.day} P{self.period} ({self.session.name})"
