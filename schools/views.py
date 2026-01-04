from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import School
from .serializers import SchoolSerializer

class SchoolListAPIView(APIView):
    def get(self, request):
        schools = School.objects.filter(is_active=True)
        serializer = SchoolSerializer(schools, many=True)
        return Response(serializer.data)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import connection
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
import secrets
import string
from schools.models import School, Domain
from django.contrib.auth import get_user_model
import re
from django_tenants.utils import schema_context
User = get_user_model()

class CreateSchoolAPIView(APIView):
    """
    API to create new school with admin user
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Check authorization
            if not (request.user.is_superuser or getattr(request.user, 'user_type', None) == 'super_admin'):
                return Response(
                    {'error': 'Only super admin can create schools'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get data
            data = request.data
            
            # Validate required fields
            required_fields = ['name', 'code', 'email', 'phone', 'city', 
                             'admin_name', 'admin_email', 'admin_password']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return Response(
                    {'error': f'Missing required fields: {", ".join(missing_fields)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate school code
            connection.set_schema_to_public()
            if School.objects.filter(school_code=data['code']).exists():
                return Response(
                    {'error': f"School code '{data['code']}' already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate domain
            clean_code = data['code'].lower().replace(' ', '_').replace('-', '_')
            domain_url = f"{clean_code}.localhost:8000"
            if Domain.objects.filter(domain=domain_url).exists():
                return Response(
                    {'error': f"Domain '{domain_url}' already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate admin email
            email_re = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_re, data['admin_email']):
                return Response(
                    {'error': 'Invalid admin email format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate admin email not in any tenant
            # First check in public schema
            if User.objects.filter(email=data['admin_email']).exists():
                # Check in all tenant schemas
                schools = School.objects.all()
                for school in schools:
                    connection.set_tenant(school)
                    if User.objects.filter(email=data['admin_email']).exists():
                        connection.set_schema_to_public()
                        return Response(
                            {'error': f"Admin email '{data['admin_email']}' already exists in another school"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                connection.set_schema_to_public()
            
            # ✅ STEP 1: CREATE SCHOOL IN PUBLIC SCHEMA
            schema_name = f"school_{clean_code}"
            
            school = School.objects.create(
                name=data['name'],
                school_code=data['code'],
                schema_name=schema_name,
                email=data['email'],
                phone=data['phone'],
                address=data.get('address', f"{data['name']} Campus, {data['city']}"),
                city=data['city'],
                state=data.get('state', 'Maharashtra'),
                country=data.get('country', 'India'),
                postal_code=data.get('postal_code', '400001'),
                establishment_date=timezone.now().date(),
                board=data.get('board', 'CBSE'),
                subscription_type=data.get('plan', 'basic'),
                subscription_start=timezone.now().date(),
                subscription_end=timezone.now().date() + timedelta(days=int(data.get('validity_days', 365))),
                student_capacity=1000,
                academic_year_start_month=4,
                is_active=True,
                is_verified=True,
            )
            
            # ✅ STEP 2: CREATE DOMAIN
            domain = Domain.objects.create(
                domain=domain_url,
                tenant=school,
                is_primary=True
            )
            
            # ✅ STEP 3: MIGRATE TENANT SCHEMA
            call_command('migrate_schemas', '--schema', schema_name)
            
            # ✅ STEP 4: SWITCH TO TENANT AND CREATE ADMIN USER
            connection.set_tenant(school)
            
            # Split admin name
            admin_name_parts = data['admin_name'].strip().split(' ', 1)
            first_name = admin_name_parts[0]
            last_name = admin_name_parts[1] if len(admin_name_parts) > 1 else ''
            
            # Create admin user
            admin = User.objects.create(
                username=data['admin_email'],
                email=data['admin_email'],
                first_name=first_name,
                last_name=last_name,
                user_type='school_admin',
                phone=data.get('admin_phone', data['phone']),
                gender=data.get('admin_gender', 'M'),
                is_staff=True,
                is_active=True,
                is_verified=True,
                school_id=school.id,
                school_code=school.school_code
            )
            admin.set_password(data['admin_password'])
            admin.save()
            
            # ✅ STEP 5: SEED RBAC MODULES
            self._seed_rbac_modules()
            
            # ✅ STEP 6: ASSIGN SUPER ADMIN ROLE
            self._assign_super_admin_role(admin)
            
            # ✅ STEP 7: RETURN TO PUBLIC SCHEMA
            connection.set_schema_to_public()
            
            # ✅ STEP 8: PREPARE RESPONSE
            response_data = {
                'success': True,
                'message': 'School and admin created successfully',
                'data': {
                    'school': {
                        'id': school.id,
                        'name': school.name,
                        'code': school.school_code,
                        'schema': school.schema_name,
                        'email': school.email,
                        'phone': school.phone,
                        'city': school.city,
                        'state': school.state,
                        'address': school.address
                    },
                    'domain': {
                        'url': domain.domain,
                        'is_primary': domain.is_primary
                    },
                    'admin': {
                        'id': admin.id,
                        'name': admin.get_full_name(),
                        'email': admin.email,
                        'phone': admin.phone,
                        'school_id': admin.school_id,
                        'school_code': admin.school_code
                    },
                    'access_urls': {
                        'admin_panel': f"http://{domain.domain}/admin/",
                        'api_login': f"http://{domain.domain}/api/v1/auth/login/",
                        'frontend': f"http://{domain.domain}/"
                    },
                    'credentials': {
                        'email': admin.email,
                        'password': data['admin_password'],
                        'note': 'Please change password after first login'
                    }
                }
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # Cleanup on error
            try:
                if 'school' in locals():
                    school.delete()
                connection.set_schema_to_public()
            except:
                pass
            
            return Response(
                {
                    'success': False,
                    'error': 'School creation failed',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _seed_rbac_modules(self):
        """Seed RBAC modules"""
        from core.models import Module, Permission, Role
        
        # Create modules
        modules_data = [
            ('dashboard', 'Dashboard', 'fas fa-tachometer-alt', True),
            ('students', 'Students', 'fas fa-user-graduate', True),
            ('teachers', 'Teachers', 'fas fa-chalkboard-teacher', True),
            ('classes', 'Classes', 'fas fa-school', True),
            ('attendance', 'Attendance', 'fas fa-check-square', True),
            ('settings', 'Settings', 'fas fa-cog', True),
            ('fees', 'Fees', 'fas fa-money-bill-wave', False),
            ('examinations', 'Examinations', 'fas fa-file-alt', False),
            ('timetable', 'Timetable', 'fas fa-calendar-alt', False),
            ('reports', 'Reports', 'fas fa-chart-bar', False),
        ]
        
        for name, display_name, icon, is_core in modules_data:
            Module.objects.get_or_create(
                name=name,
                defaults={
                    'display_name': display_name,
                    'icon': icon,
                    'is_core': is_core,
                    'is_active': True,
                    'created_by_system': True
                }
            )
        
        # Create permissions
        for name, _, _, _ in modules_data:
            Permission.objects.get_or_create(
                codename=name,
                defaults={
                    'action': 'module',
                    'description': f'Access to {name} module'
                }
            )
        
        # Create ALL_MODULES permission
        Permission.objects.get_or_create(
            codename='ALL_MODULES',
            defaults={
                'action': 'module',
                'description': 'Access to all modules'
            }
        )
        
        # Create Super Admin role
        super_admin_role, _ = Role.objects.get_or_create(
            name='Super Admin',
            defaults={
                'is_system_role': True,
                'description': 'Full access to all modules',
                'is_active': True
            }
        )
        
        # Assign ALL_MODULES to Super Admin
        all_modules_perm = Permission.objects.get(codename='ALL_MODULES')
        super_admin_role.permissions.add(all_modules_perm)
    
    def _assign_super_admin_role(self, user):
        """Assign Super Admin role to user"""
        from core.models import Role, UserRole
        super_admin_role = Role.objects.get(name='Super Admin')
        UserRole.objects.get_or_create(
            user=user,
            role=super_admin_role,
            defaults={
                'assigned_by': user,
                'is_active': True
            }
        )
        
        

User = get_user_model()

class SchoolAndUserDetailsAPI(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            school_id = user.school_id
            school_code = user.school_code
            
            if not school_id or not school_code:
                return Response({
                    'success': False,
                    'message': 'User is not associated with any school'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Public schema में school की details fetch करें
            with schema_context('public'):
                try:
                    school = School.objects.get(
                        id=school_id,
                        school_code=school_code,
                        is_active=True
                    )
                    
                    school_details = {
                        'school_id': school.id,
                        'school_code': school.school_code,
                        'name': school.name,
                        'email': school.email,
                        'phone': school.phone,
                        'address': school.address,
                        'city': school.city,
                        'state': school.state,
                        'country': school.country,
                        'postal_code': school.postal_code,
                        'establishment_date': school.establishment_date,
                        'board': school.board,
                        'subscription_type': school.subscription_type,
                        'subscription_start': school.subscription_start,
                        'subscription_end': school.subscription_end,
                        'student_capacity': school.student_capacity,
                        'academic_year_start_month': school.academic_year_start_month,
                        'is_active': school.is_active,
                        'is_verified': school.is_verified
                    }
                except School.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'School not found or is inactive'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # User details
            user_details = {
                'user_id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user.user_type,
                'phone': user.phone,
                'date_of_birth': user.date_of_birth,
                'gender': user.gender,
                'address': user.address,
                'city': user.city,
                'state': user.state,
                'is_verified': user.is_verified,
                'profile_picture': request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None
            }
            
            return Response({
                'success': True,
                'message': 'School and user details fetched successfully',
                'school': school_details,
                'user': user_details
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error fetching details: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)