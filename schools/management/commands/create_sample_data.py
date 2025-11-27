from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
from django.db import connection
from schools.models import School, Domain
from users.models import User

class Command(BaseCommand):
    help = 'Create sample school and data for localhost testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data for localhost...')
        
        # Create sample school
        school, created = School.objects.get_or_create(
            school_code="DEMO01",
            defaults={
                'name': 'Demo School',
                'email': 'info@demoschool.edu',
                'phone': '9876543210',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'schema_name': 'school_demo01',
                'is_active': True,
                'is_verified': True,
            }
        )
        
        # Create domain for localhost
        domain, created = Domain.objects.get_or_create(
            domain='127.0.0.1',
            defaults={'tenant': school, 'is_primary': True}
        )
        
        # Migrate tenant schema
        call_command('migrate_schemas', '--tenant', school.schema_name)
        
        # Switch to tenant and create admin user
        connection.set_tenant(school)
        
        admin, created = User.objects.get_or_create(
            email='admin@demoschool.edu',
            defaults={
                'username': 'admin@demoschool.edu',
                'first_name': 'School',
                'last_name': 'Admin',
                'user_type': 'school_admin',
                'is_staff': True,
                'is_active': True,
                'is_verified': True,
            }
        )
        
        if created:
            admin.set_password('admin123')
            admin.save()
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Sample data created successfully!\n'
            f'School: {school.name} ({school.school_code})\n'
            f'Admin Login: admin@demoschool.edu / admin123\n'
            f'Access URL: http://127.0.0.1:8000/admin\n'
            f'API Login: http://127.0.0.1:8000/api/auth/login/\n'
        ))