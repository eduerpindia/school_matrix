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