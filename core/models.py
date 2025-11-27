from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Module(models.Model):
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True)
    is_core = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by_system = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.display_name


class Permission(models.Model):
    module = models.ForeignKey(Module, null=True, blank=True, on_delete=models.CASCADE, related_name='permissions')
    action = models.CharField(max_length=20, default='module')
    codename = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['codename']
    
    def __str__(self):
        return self.codename


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    is_system_role = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_roles')
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'role']
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.role.name}"


class UserPermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_permissions_custom')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    granted = models.BooleanField(default=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, blank=True)
    
    class Meta:
        unique_together = ['user', 'permission']
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.permission.codename} ({'Granted' if self.granted else 'Denied'})"
    

from django.db import models

class AcademicYear(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Example: "2025-26"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = "Academic Year"
        verbose_name_plural = "Academic Years"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Ensure only one academic year is marked as current
        if self.is_current:
            AcademicYear.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_current_academic_year(cls):
        try:
            return cls.objects.get(is_current=True)
        except cls.DoesNotExist:
            return None