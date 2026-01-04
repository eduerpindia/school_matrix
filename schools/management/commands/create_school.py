# schools/management/commands/create_school.py
import secrets
import string
from datetime import datetime, date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connection
from django.contrib.auth import get_user_model

from schools.models import School, Domain

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a new school tenant with module-level RBAC'

    def add_arguments(self, parser):
        # School (required)
        parser.add_argument('--name', type=str, required=True, help='School name')
        parser.add_argument('--code', type=str, required=True, help='Unique school code (e.g., GVS01)')
        parser.add_argument('--domain', type=str, required=True, help='Domain (e.g., gvs.localhost:8000)')
        parser.add_argument('--email', type=str, required=True, help='School contact email')
        parser.add_argument('--phone', type=str, required=True, help='School phone')
        parser.add_argument('--city', type=str, required=True, help='School city')

        # School (optional)
        parser.add_argument('--state', type=str, default='Maharashtra')
        parser.add_argument('--country', type=str, default='India')
        parser.add_argument('--address', type=str)
        parser.add_argument('--board', type=str, choices=['CBSE', 'ICSE', 'STATE', 'IB'], default='CBSE')

        # Subscription
        parser.add_argument('--plan', type=str, choices=['basic', 'premium', 'enterprise'], default='basic')
        parser.add_argument('--validity-days', type=int, default=365)

        # Admin (required)
        parser.add_argument('--admin-name', type=str, required=True, help='Admin full name')
        parser.add_argument('--admin-email', type=str, required=True, help='Admin login email')

        # Admin (optional)
        parser.add_argument('--admin-password', type=str)
        parser.add_argument('--admin-phone', type=str)
        parser.add_argument('--admin-gender', type=str, choices=['M', 'F', 'O'], default='M')
        parser.add_argument('--admin-dob', type=str)  # YYYY-MM-DD
        parser.add_argument('--admin-address', type=str)

        # Advanced
        parser.add_argument('--skip-validation', action='store_true')
        parser.add_argument('--auto-verify', action='store_true', default=True)

    def handle(self, *args, **options):
        try:
            # Reset to public schema first
            connection.set_schema_to_public()

            if not options['skip_validation']:
                self._validate_inputs(options)

            self._print_plan(options)

            # Create tenant
            school = self._create_school(options)
            domain = self._create_domain(school, options['domain'])

            # Migrate tenant schema
            self.stdout.write('🔄 Creating tenant schema and running migrations...')
            call_command('migrate_schemas', '--schema', school.schema_name)

            # Switch to tenant
            connection.set_tenant(school)

            # ✅ CREATE ADMIN USER WITH SCHOOL FIELDS
            admin_user, admin_password = self._create_admin_user(school, options)

            # Seed module-level RBAC
            modules_count, roles_count = self._seed_modules_and_roles()

            # Assign Super Admin role to admin
            self._assign_super_admin(admin_user)

            # Reset to public schema
            connection.set_schema_to_public()

            # Print summary
            self._print_success(
                school, domain, admin_user, admin_password, modules_count, roles_count
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ School creation failed: {e}'))
            # Reset connection to public schema on error
            connection.set_schema_to_public()
            raise CommandError(str(e))

    # ============ Validation ============

    def _validate_inputs(self, opts):
        self.stdout.write('🔍 Validating inputs...')

        # Check if school code already exists
        if School.objects.filter(school_code=opts['code']).exists():
            raise CommandError(f'School code "{opts["code"]}" already exists')

        # Check if domain already exists
        if Domain.objects.filter(domain=opts['domain']).exists():
            raise CommandError(f'Domain "{opts["domain"]}" already exists')

        # Email validation
        import re
        email_re = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_re, opts['email']):
            raise CommandError('Invalid school email format')
        if not re.match(email_re, opts['admin_email']):
            raise CommandError('Invalid admin email format')

        self.stdout.write(self.style.SUCCESS('✅ Validation OK'))

    # ============ Creation ============

    def _create_school(self, opts):
        clean_code = opts['code'].lower().replace(' ', '_').replace('-', '_')
        schema_name = f'school_{clean_code}'

        today = date.today()  # IST (since USE_TZ = False and server is IST)

        school = School.objects.create(
            name=opts['name'],
            school_code=opts['code'],
            email=opts['email'],
            phone=opts['phone'],
            address=opts.get('address') or f"{opts['name']} Campus, {opts['city']}",
            city=opts['city'],
            state=opts['state'],
            country=opts['country'],
            postal_code='400001',
            establishment_date=today,
            board=opts['board'],
            subscription_type=opts['plan'],
            subscription_start=today,
            subscription_end=today + timedelta(days=opts['validity_days']),
            student_capacity=1000,
            academic_year_start_month=4,
            is_active=True,
            is_verified=opts['auto_verify'],
            schema_name=schema_name,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ School '{school.name}' created (schema: {schema_name})"
            )
        )
        return school

    def _create_domain(self, school, domain_url):
        domain = Domain.objects.create(domain=domain_url, tenant=school, is_primary=True)
        self.stdout.write(self.style.SUCCESS(f"✅ Domain '{domain_url}' mapped"))
        return domain

    def _create_admin_user(self, school, opts):
        """Create admin user with school reference"""
        pwd = opts.get('admin_password') or self._gen_pwd()
        first, last = self._split_name(opts['admin_name'])

        dob = None
        if opts.get('admin_dob'):
            try:
                dob = datetime.strptime(opts['admin_dob'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(self.style.WARNING('⚠️ Invalid DOB format, skipping'))

        admin = User(
            username=opts['admin_email'],
            email=opts['admin_email'],
            first_name=first,
            last_name=last,
            user_type='school_admin',
            phone=opts.get('admin_phone', '9876543211'),
            gender=opts.get('admin_gender', 'M'),
            date_of_birth=dob,
            address=opts.get('admin_address', f"{opts['city']}, {opts['state']}"),
            city=opts.get('city', 'Mumbai'),
            state=opts.get('state', 'Maharashtra'),
            is_staff=True,
            is_active=True,
            is_verified=opts['auto_verify'],
            school_id=school.id,
            school_code=school.school_code,
        )
        admin.set_password(pwd)
        admin.save()
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Admin user '{admin.get_full_name()}' created"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"   School ID: {school.id}, School Code: {school.school_code}"
            )
        )
        return admin, pwd

    # ============ Seeding (Module-level RBAC only) ============

    def _seed_modules_and_roles(self):
        from core.models import Module, Permission, Role

        core = [
            ('dashboard', 'Dashboard', 'fas fa-tachometer-alt', True),
            ('students', 'Students', 'fas fa-user-graduate', True),
            ('teachers', 'Teachers', 'fas fa-chalkboard-teacher', True),
            ('classes', 'Classes', 'fas fa-school', True),
            ('attendance', 'Attendance', 'fas fa-check-square', True),
            ('settings', 'Settings', 'fas fa-cog', True),
        ]
        optional = [
            ('fees', 'Fees', 'fas fa-money-bill-wave', False),
            ('examinations', 'Examinations', 'fas fa-file-alt', False),
            ('timetable', 'Timetable', 'fas fa-calendar-alt', False),
            ('reports', 'Reports', 'fas fa-chart-bar', False),
            ('library', 'Library', 'fas fa-book-open', False),
            ('communications', 'Communications', 'fas fa-bullhorn', False),
            ('transport', 'Transport', 'fas fa-bus', False),
            ('events', 'Events', 'fas fa-calendar-check', False),
        ]
        all_modules = core + optional

        modules_created = 0
        for name, label, icon, is_core in all_modules:
            m, created = Module.objects.get_or_create(
                name=name,
                defaults=dict(
                    display_name=label,
                    icon=icon,
                    is_core=is_core,
                    is_active=True,
                    created_by_system=True,
                ),
            )
            if created:
                modules_created += 1

        # Create module-level permissions and ALL_MODULES
        perm_codes = ['ALL_MODULES'] + [m[0] for m in all_modules]

        def get_module_or_none(code):
            if code == 'ALL_MODULES':
                return None
            try:
                return Module.objects.get(name=code)
            except Module.DoesNotExist:
                return None

        for code in perm_codes:
            Permission.objects.get_or_create(
                module=get_module_or_none(code),
                action='module',
                defaults=dict(
                    codename=code,
                    description=(
                        'Access to all modules'
                        if code == 'ALL_MODULES'
                        else f'Full access to {code} module'
                    ),
                ),
            )

        # Create roles and attach module-level permissions
        roles_created = 0

        def perms(codes):
            return Permission.objects.filter(codename__in=codes)

        # Super Admin
        super_admin, created = Role.objects.get_or_create(
            name='Super Admin',
            defaults=dict(
                is_system_role=True,
                description='Full access to all modules',
                is_active=True,
            ),
        )
        if created:
            roles_created += 1
            super_admin.permissions.set(perms(['ALL_MODULES']))

        # Principal
        principal_modules = [
            'dashboard',
            'students',
            'teachers',
            'classes',
            'attendance',
            'fees',
            'examinations',
            'timetable',
            'reports',
            'library',
            'communications',
        ]
        principal, created = Role.objects.get_or_create(
            name='Principal',
            defaults=dict(
                is_system_role=True,
                description='Comprehensive module access',
                is_active=True,
            ),
        )
        if created:
            roles_created += 1
            principal.permissions.set(perms(principal_modules))

        return modules_created, roles_created

    def _assign_super_admin(self, user):
        from core.models import Role, UserRole

        role = Role.objects.get(name='Super Admin')
        UserRole.objects.get_or_create(
            user=user,
            role=role,
            defaults={'assigned_by': user, 'is_active': True},
        )
        self.stdout.write(self.style.SUCCESS('✅ Super Admin role assigned'))

    # ============ Helpers ============

    def _gen_pwd(self):
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        pwd = ''.join(secrets.choice(chars) for _ in range(12))
        # Ensure complexity
        if not any(c.islower() for c in pwd):
            pwd = pwd[:-1] + secrets.choice(string.ascii_lowercase)
        if not any(c.isupper() for c in pwd):
            pwd = pwd[:-1] + secrets.choice(string.ascii_uppercase)
        if not any(c.isdigit() for c in pwd):
            pwd = pwd[:-1] + secrets.choice(string.digits)
        if not any(c in "!@#$%^&*" for c in pwd):
            pwd = pwd[:-1] + secrets.choice("!@#$%^&*")
        return pwd

    def _split_name(self, full_name: str):
        parts = full_name.strip().split(' ', 1)
        return parts[0], (parts[1] if len(parts) > 1 else '')

    def _print_plan(self, opts):
        self.stdout.write(
            self.style.WARNING(
                f'\n{"="*60}\n'
                f'Creating School with Module-level RBAC\n'
                f'School: {opts["name"]} ({opts["code"]}) | {opts["domain"]}\n'
                f'Plan: {opts["plan"].title()} | Validity: {opts["validity_days"]} days\n'
                f'Admin: {opts["admin_name"]} <{opts["admin_email"]}>\n'
                f'{"="*60}\n'
            )
        )

    def _print_success(self, school, domain, admin, pwd, modules_count, roles_count):
        self.stdout.write(
            self.style.SUCCESS(
                f'\n{"="*70}\n'
                f'✅ School Created Successfully!\n'
                f'School: {school.name} | Code: {school.school_code}\n'
                f'Domain: {domain.domain} | Schema: {school.schema_name}\n'
                f'Admin: {admin.get_full_name()} <{admin.email}>\n'
                f'Password: {pwd}\n'
                f'Admin School ID: {admin.school_id}\n'
                f'Admin School Code: {admin.school_code}\n'
                f'Modules: {modules_count} | Roles: {roles_count}\n\n'
                f'🌐 Access URLs:\n'
                f'   • Django Admin: http://{domain.domain}/admin\n'
                f'   • API Login: http://{domain.domain}/api/v1/auth/login/\n'
                f'{"="*70}\n'
            )
        )
