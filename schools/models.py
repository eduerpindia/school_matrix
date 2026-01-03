from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class School(TenantMixin):
    name = models.CharField(max_length=200)
    school_code = models.CharField(max_length=20, unique=True)
    schema_name = models.CharField(max_length=100, unique=True)  # ✅ यह line ADD करें
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, default='State')
    country = models.CharField(max_length=100, default='India')
    postal_code = models.CharField(max_length=20, default='000000')

    establishment_date = models.DateField(null=True, blank=True)
    board = models.CharField(max_length=50, default='CBSE')

    subscription_type = models.CharField(max_length=20, default='basic')
    subscription_start = models.DateField(null=True, blank=True)
    subscription_end = models.DateField(null=True, blank=True)

    student_capacity = models.IntegerField(default=1000)
    academic_year_start_month = models.IntegerField(default=4)

    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=True)

    auto_create_schema = True

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.school_code})"


class Domain(DomainMixin):
    pass



class SchoolSession(models.Model):
    """
    academic year/session.
    Example: "2025-26"
    """
    school = models.ForeignKey(
        School,
        related_name='sessions',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)  # Example: "2025-26"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        unique_together = ('school', 'name')

    def __str__(self):
        return f"{self.school.name} - {self.name}"

    def save(self, *args, **kwargs):
        if self.is_current:
            SchoolSession.objects.filter(
                school=self.school,
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_current_for_school(cls, school):
        try:
            return cls.objects.get(school=school, is_current=True)
        except cls.DoesNotExist:
            return None